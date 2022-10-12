from typing import List, Iterator
import datetime

import boto3
from boto3.resources.base import ServiceResource
from mypy_boto3_ec2 import EC2Client
from mypy_boto3_ec2.service_resource import Instance


def create_instance(
        ec2_resource_creator,
        instance_name,
        key_name
) -> List[Instance]:

    instances: List[Instance] = ec2_resource_creator.create_instances(
        ImageId='ami-0f7559f51d3a22167',
        Placement={"AvailabilityZone": "eu-west-3c"},
        InstanceType='t2.micro',

        MinCount=1,
        MaxCount=1,

        SecurityGroupIds=["sg-0b4757204f93b037e"],
        KeyName=key_name,
        Monitoring={"Enabled": True},

        InstanceInitiatedShutdownBehavior="terminate",
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": instance_name
                        or f"node-{datetime.datetime.now().__str__()[5:-5]}",
                    }
                ],
            }
        ],

        IamInstanceProfile={
            "Arn": "arn:aws:iam::958267223794:instance-profile/AmazonSSMRoleForInstancesQuickSetup",
        },
    )
    return instances


def get_public_ip(ec2_client: EC2Client, instance_id):
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            print(instance.get("PublicIpAddress"))


def stop_instance(ec2_client, instance_id):
    response = ec2_client.stop_instances(InstanceIds=[instance_id])
    print(f'stop {instance_id=}: {response}')


def terminate_instance(ec2_client, instance_id):
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])
    print(f'terminate {instance_id=}: {response}')


def running_instances_ids(ec2_client) -> Iterator[str]:
    reservations = ec2_client.describe_instances(Filters=[
        {
            "Name": "instance-state-name",
            "Values": ["running"],
        }
    ]).get("Reservations")

    for reservation in reservations:
        for instance in reservation["Instances"]:
            yield instance["InstanceId"]


def terminate_all_instances(ec2_client):
    for instance_id in running_instances_ids(ec2_client):
        terminate_instance(ec2_client, instance_id)


def get_running_instances(ec2_client, ec2_resource):
    reservations = ec2_client.describe_instances(Filters=[
        {
            "Name": "instance-state-name",
            "Values": ["running"],
        }
    ]).get("Reservations")

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            public_ip = instance["PublicIpAddress"]
            private_ip = instance["PrivateIpAddress"]
            print(f"{instance_id}, {instance_type}, {public_ip=}, {private_ip=}")

    for status in ec2_resource.meta.client.describe_instance_status()['InstanceStatuses']:
        print(status)


if __name__ == '__main__':
    region_name = 'eu-west-3'
    key_name = 'aws_gth_keys'
    instance_name = 'coucou12'

    node_session = boto3.Session(profile_name='ec2_node')
    creator_session = boto3.Session(profile_name='ec2_creator')

    ec2_resource_node: ServiceResource = node_session.resource('ec2', region_name=region_name)
    ec2_client_node: EC2Client = node_session.client('ec2', region_name=region_name)
    ec2_resource_creator: ServiceResource = creator_session.resource('ec2', region_name=region_name)
    ec2_client_creator: EC2Client = creator_session.client('ec2', region_name=region_name)

    print(f"{ec2_client_creator=}, {ec2_resource_creator=}, {ec2_client_node=}, {ec2_resource_node=}")

    instances = create_instance(ec2_resource_creator, instance_name, key_name)

    i: Instance = instances[0]
    print(f"{i.id=}, {len(instances)=}, {type(instances[0])=}, {i=}")

    i.wait_until_running()
    i.reload()

    print(f"{get_public_ip(ec2_client_creator, i.id)}, {i.state=}")

    import time

    # time.sleep(20)
    instance_id = i.id
    # instance_id = 'i-09521b9c2fd7ff5c4'

    ssm_client = node_session.client('ssm', region_name=region_name)
    # ssm_client = boto3.client('ssm', region_name="eu-west-3")

    while True:
        try:
            response = ssm_client.describe_instance_information(Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}])
            # if len(response["InstanceInformationList"]) > 0 and \
            #         response["InstanceInformationList"][0]["PingStatus"] == "Online" and \
            #         response["InstanceInformationList"][0]["InstanceId"] == instance_id:
            print(response["InstanceInformationList"])
            print(f'SEND COMMAND TO {instance_id=}')
            response = ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': ['ls -la /']}
            )
            # command_id = response['Command']['CommandId']
            # output = ssm_client.get_command_invocation(
            #       CommandId=command_id,
            #       InstanceId=instance_id,
            #     )
            # print(output)
            break
        except Exception as e:
            print(e)
            time.sleep(3)

    command_id = response['Command']['CommandId']
    time.sleep(2)
    output = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    while output['Status'] == "InProgress":
        output = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    print(output['StandardOutputContent'])

    print(f"{get_running_instances(ec2_client_creator, ec2_resource_creator)=}")

    print("Terminate all instance")
    terminate_all_instances(ec2_client_creator)

    response = ec2_client_creator.terminate_instances(
        InstanceIds=[
            instance.id for instance in instances
        ],
    )

    print(response)
