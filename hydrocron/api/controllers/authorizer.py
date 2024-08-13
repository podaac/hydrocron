"""
Lambda Authorizer to facilitate usage of API keys and usage plans.

Taken from example:
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""

import json
import logging

from hydrocron.utils import connection


logging.getLogger().setLevel(logging.INFO)


ssm_client = connection.ssm_client
STORED_API_KEY_TRUSTED = ssm_client.get_parameter(Name="/service/hydrocron/api-key-trusted", WithDecryption=True)["Parameter"]["Value"]
STORED_API_KEY_DEFAULT = ssm_client.get_parameter(Name="/service/hydrocron/api-key-default", WithDecryption=True)["Parameter"]["Value"]


def authorization_handler(event, context):
    """Lambda authorizer function to allow or deny a request."""

    logging.info("Event: %s", event)
    logging.info("Context: %s", context)

    api_key_trusted = "" if "x-hydrocron-key" not in event["headers"].keys() else event["headers"]["x-hydrocron-key"]
    trusted_key_list = json.loads(STORED_API_KEY_TRUSTED)

    if api_key_trusted and api_key_trusted in trusted_key_list:
        response_policy = create_policy("trusted_partner", "Allow", event["methodArn"], api_key_trusted)
        logging.info("Created policy for truster partner.")

    else:
        response_policy = create_policy("default_user", "Allow", event["methodArn"], STORED_API_KEY_DEFAULT)
        logging.info("Created policy for default user.")

    logging.info("Response: %s", response_policy)
    return json.loads(response_policy)


def create_policy(principle_id, effect, method_arn, api_key=""):
    """Create IAM policy to return in authorizer response."""

    authorization_response = {
        "principalId": principle_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": method_arn,
                }
            ]
        },
        "usageIdentifierKey": api_key
    }

    return json.dumps(authorization_response)
