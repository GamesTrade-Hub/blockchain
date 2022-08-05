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
logger.setLevel(logging.INFO)


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


def get_running_instances(ec2_client, ec2_resource):
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

    for status in ec2_resource.meta.app.describe_instance_status()[
        "InstanceStatuses"
    ]:
        print(status)


class AutoRunner:
    region_name = "eu-west-3"
    key_name = "aws_gth_keys"

    def __init__(self):
        self.node_session = boto3.Session(profile_name="ec2_node")
        self.creator_session = boto3.Session(profile_name="ec2_creator")

        self.ec2_resource_node: ServiceResource = self.node_session.resource(
            "ec2", region_name=self.region_name
        )
        self.ec2_client_node: EC2Client = self.node_session.app(
            "ec2", region_name=self.region_name
        )
        self.ec2_resource_creator: ServiceResource = self.creator_session.resource(
            "ec2", region_name=self.region_name
        )
        self.ec2_client_creator: EC2Client = self.creator_session.app(
            "ec2", region_name=self.region_name
        )

        self.ssm_client = self.node_session.app("ssm", region_name=self.region_name)

    def create_node_instance(self, name=None) -> Optional[Instance]:
        """
        Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
        :param name: name of the EC2 instance
        :return: the instance if created, None otherwise
        """
        logger.info("Creating node instance")
        instances: List[Instance] = self.ec2_resource_creator.create_instances(
            ImageId="ami-0f7559f51d3a22167",
            KeyName=self.key_name,
            MaxCount=1,
            MinCount=1,
            Monitoring={"Enabled": True},
            Placement={"AvailabilityZone": "eu-west-3c"},
            InstanceType="t2.micro",
            SecurityGroupIds=["sg-0ea7ad2589dc158bf"],
            IamInstanceProfile={
                "Arn": "arn:aws:iam::747137879128:instance-profile/BlockchainNode",
            },
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": name
                            or f"node-{datetime.datetime.now().__str__()[5:-5]}",
                        }
                    ],
                }
            ],
        )

        self.__run_dummy_command_checkup(instances[0])
        logger.info(
            f"Created node instance: {instances[0].id}. ip: {get_public_ip(self.ec2_client_creator, instances[0].id)}"
        )
        self.__run_blockchain_node_setup(instances[0])

        return instances[0]

    def __run_dummy_command_checkup(self, instance: Instance) -> None:
        instance.wait_until_running()
        instance.reload()

        timeout = 10
        count = 0
        while True:
            try:
                response = self.ssm_client.send_command(
                    InstanceIds=[instance.id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": ["ls -la /"],
                    },
                )

                break
            except Exception as e:
                logger.debug(f"ssm_client.send_command failed {e}")
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

    def get_running_instances(self):
        get_running_instances(self.ec2_client_creator, self.ec2_resource_creator)

    def __run_blockchain_node_setup(self, instance):
        # https://github.com/GamesTrade-Hub/blockchain.git

        timeout = 10
        count = 0
        while True:
            try:
                response = self.ssm_client.send_command(
                    InstanceIds=[instance.id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": [
                            "git clone https://github.com/GamesTrade-Hub/blockchain.git",
                            "cd blockchain",
                            "./deploy.sh prod.config.json",
                        ],
                        "workingDirectory": ["/home/ubuntu"],
                    },
                )
                break
            except Exception as e:
                logger.debug(f"ssm_client.send_command failed {e}")
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
        logger.debug(f"run BC command output {output['StandardOutputContent']}")
        logger.debug(f"run BC command error {output['StandardErrorContent']}")
        logger.info(f"run blockchain node setup status: {output['Status']}")
        logger.debug(f"StatusDetails {output['StatusDetails']}")


if __name__ == "__main__":
    auto_runner = AutoRunner()
    auto_runner.terminate_all_instances()
    auto_runner.create_node_instance()
