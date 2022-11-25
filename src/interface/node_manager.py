import datetime
from typing import Optional, List, Iterator

import boto3
from boto3.resources.base import ServiceResource
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.service_resource import Instance

import os
import json
import time
import logging
from logging import INFO, DEBUG, WARNING

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_public_ip(ec2_client: EC2Client, instance_id):
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get(
        "Reservations"
    )

    for reservation in reservations:
        for instance in reservation["Instances"]:
            return instance.get("PublicIpAddress")


def stop_instance(ec2_client, instance_id):
    response = ec2_client.stop_instances(InstanceIds=[instance_id])
    logger.info(f"stop {instance_id=}: {response}")


def terminate_instance(ec2_client, instance_id):
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])
    logger.info(f"terminate {instance_id=}: {response}")


def running_instances_ids(ec2_client) -> Iterator[str]:
    reservations = ec2_client.describe_instances(
        Filters=[
            {
                "Name": "instance-state-name",
                "Values": ["running"],
            }
        ]
    ).get("Reservations")

    for reservation in reservations:
        for instance in reservation["Instances"]:
            yield instance["InstanceId"]


def terminate_all_instances(ec2_client):
    for instance_id in running_instances_ids(ec2_client):
        terminate_instance(ec2_client, instance_id)


def get_running_instances(ec2_client, ec2_resource) -> List:
    reservations = ec2_client.describe_instances(
        Filters=[
            {
                "Name": "instance-state-name",
                "Values": ["running"],
            }
        ]
    ).get("Reservations")

    instances = []

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            public_ip = instance["PublicIpAddress"]
            private_ip = instance["PrivateIpAddress"]
            print(f"{instance_id}, {instance_type}, {public_ip=}, {private_ip=}")
            instances.append({
                'instance_id': instance_id,
                'instance_type': instance_type,
                'public_ip': public_ip,
                'private_ip': private_ip
            })

    return instances

    # for status in ec2_resource.meta.app.describe_instance_status()["InstanceStatuses"]:
    #     print(status)


def print_running_instances(ec2_client, ec2_resource):
    reservations = ec2_client.describe_instances(
        Filters=[
            {
                "Name": "instance-state-name",
                "Values": ["running"],
            }
        ]
    ).get("Reservations")

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            public_ip = instance["PublicIpAddress"]
            private_ip = instance["PrivateIpAddress"]
            print(f"{instance_id}, {instance_type}, {public_ip=}, {private_ip=}")

    for status in ec2_resource.meta.app.describe_instance_status()["InstanceStatuses"]:
        print(status)


class NodesManager:
    region_name = "eu-west-3"
    key_name = "aws_gth_keys"

    def __init__(self):
        self.node_session = boto3.Session(profile_name="ec2_node")
        self.creator_session = boto3.Session(profile_name="ec2_creator")
        # These 2 guys are currently the same role in AWS. TODO later

        self.ec2_resource_node: ServiceResource = self.node_session.resource(
            "ec2", region_name=self.region_name
        )
        self.ec2_client_node: EC2Client = self.node_session.client(
            "ec2", region_name=self.region_name
        )
        self.ec2_resource_creator: ServiceResource = self.creator_session.resource(
            "ec2", region_name=self.region_name
        )
        self.ec2_client_creator: EC2Client = self.creator_session.client(
            "ec2", region_name=self.region_name
        )

        self.ssm_client = self.node_session.client("ssm", region_name=self.region_name)

    def create_node_instance(
            self,
            private_key,
            public_key,
            availability_zone="eu-west-3c",
            instance_name=None,
            nodes=None
    ) -> Optional[Instance]:
        """
        Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
        :param nodes: ip of the node to connect to
        :param instance_name: name of the EC2 instance
        :return: the instance if created, None otherwise
        """
        logger.info("Creating node instance")
        instances: List[Instance] = self.ec2_resource_creator.create_instances(
            ImageId='ami-0f7559f51d3a22167',
            Placement={"AvailabilityZone": availability_zone},
            InstanceType='t2.micro',

            MinCount=1,
            MaxCount=1,

            SecurityGroupIds=["sg-0b4757204f93b037e"],
            KeyName=self.key_name,
            Monitoring={"Enabled": True},

            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": instance_name or f"node-{datetime.datetime.now().__str__()[5:-5]}",
                        }
                    ],
                }
            ],

            IamInstanceProfile={
                "Arn": "arn:aws:iam::958267223794:instance-profile/AmazonSSMRoleForInstancesQuickSetup",
            },
        )

        self.__run_dummy_command_checkup(instances[0])
        logger.info(
            f"Created node instance: {instances[0].id}. ip: {get_public_ip(self.ec2_client_creator, instances[0].id)}"
        )
        self.__run_blockchain_node_setup(instances[0], private_key, public_key, nodes or [])

        return instances[0]

    def __run_dummy_command_checkup(self, instance: Instance) -> None:
        instance.wait_until_running()
        instance.reload()

        timeout = 10
        count = 0
        while True:
            try:
                logger.debug(f"Send dummy command to {instance.id=}")
                response = self.ssm_client.send_command(
                    InstanceIds=[instance.id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": ["ls -la /"],
                    },
                )

                break
            except Exception as e:
                logger.debug(f"ssm_client.send_command failed {e} (Please wait for some if the instance has just been created)")
                if (count := count + 1) >= timeout:
                    logger.error(f"ssm_client.send_command failed {timeout} times")
                    return
                time.sleep(3)

        command_id = response["Command"]["CommandId"]
        time.sleep(2)
        output = self.ssm_client.get_command_invocation(
            CommandId=command_id, InstanceId=instance.id
        )
        while output["Status"] == "InProgress":
            output = self.ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance.id
            )
        logger.debug(f"dummy command output {output['StandardOutputContent']}")

    def stop_instance(self, instance_id):
        stop_instance(self.ec2_client_creator, instance_id)

    def terminate_instance(self, instance_id):
        terminate_instance(self.ec2_client_creator, instance_id)

    def running_instances_ids(self) -> Iterator[str]:
        yield running_instances_ids(self.ec2_client_creator)

    def terminate_all_instances(self):
        terminate_all_instances(self.ec2_client_creator)

    def print_running_instances(self):
        print_running_instances(self.ec2_client_creator, self.ec2_resource_creator)

    def get_running_instances(self) -> List:
        return get_running_instances(self.ec2_client_creator, self.ec2_resource_creator)

    def __run_blockchain_node_setup(self, instance, private_key, public_key, nodes):
        # https://github.com/GamesTrade-Hub/blockchain.git

        timeout = 10
        count = 0

        while True:
            try:
                response = self.ssm_client.describe_instance_information(Filters=[{'Key': 'InstanceIds', 'Values': [instance.id]}])
                logger.debug(f"{response['InstanceInformationList']=}")
                logger.info(f'Send node deployment command to {instance.id=}')

                response = self.ssm_client.send_command(
                    InstanceIds=[instance.id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": [
                            "git clone https://github.com/GamesTrade-Hub/blockchain.git",
                            "cd blockchain",
                            "git checkout new_encryption",
                            "git log -1",
                            f"python3 update_miner_keys.py -cfg ./configs/prod.config.json -pvk {private_key} -pbk {public_key} -nds {' '.join(nodes)}" if len(nodes) > 0 else
                            f"python3 update_miner_keys.py -cfg ./configs/prod.config.json -pvk {private_key} -pbk {public_key}",
                            "sudo ./deploy.sh ./configs/prod.config.json",
                        ],
                        "workingDirectory": ["/home/ubuntu"],
                    },
                )
                break
            except Exception as e:
                logger.warning(f"ssm_client.send_command failed {e}")
                if (count := count + 1) >= timeout:
                    return None
                time.sleep(3)

        command_id = response["Command"]["CommandId"]
        time.sleep(2)
        output = self.ssm_client.get_command_invocation(
            CommandId=command_id, InstanceId=instance.id
        )
        while output["Status"] == "InProgress":
            output = self.ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance.id
            )
        logger.debug(f"[run BC command std output]: {output['StandardOutputContent']}")
        logger.debug(f"[run BC command err output]: {output['StandardErrorContent']}")
        logger.info(f"[run blockchain node setup status]: {output['Status']}")
        logger.debug(f"[StatusDetails]: {output['StatusDetails']}")


if __name__ == "__main__":
    nodes_manager = NodesManager()
    nodes_manager.terminate_all_instances()
    # nodes_manager.create_node_instance()





