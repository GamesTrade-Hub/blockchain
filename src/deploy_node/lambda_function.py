import json
import logging
from uuid import uuid4
import json
import sys


def lambda_handler(event, context):
    print(f"(({event=}))")
    print(f"(({context=}))")

    if "nodes" in event:
        logger.debug(f"nodes type: {type(event['nodes'])}")
    else:
        logger.debug(f"nodes not in values")

    try:
        nodes_manager.create_node_instance(
            event["private_key"],
            event["public_key"],
            event["region"] if "region" in event else "eu-west-3c",
            event["nodes"] if "nodes" in event else [],
        )
    except BaseException as e:
        return json.dumps(e), 402


"""
aws lambda update-function-code --function-name example --zip-file bc_interface_deploy.zip
  {
  "FunctionName": "mylambdafunction",
  "FunctionArn": "arn:aws:lambda:us-west-2:123456789012:function:mylambdafunction",
  "Runtime": "python3.9",
  "Role": "arn:aws:iam::123456789012:role/lambda-role",
  "Handler": "lambda_function.lambda_handler",
  "CodeSize": 5912988,
  "CodeSha256": "A2P0NUWq1J+LtSbkuP8tm9uNYqs1TAa3M76ptmZCw5g=",
  "Version": "$LATEST",
  "RevisionId": "5afdc7dc-2fcb-4ca8-8f24-947939ca707f",
  ...
  }

"""