"""
Lambda Authorizer to facilitate usage of API keys and usage plans.

Taken from example:
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""

import json
import logging

from hydrocron.utils import connection


logging.getLogger().setLevel(logging.INFO)


def authorization_handler(event, context):
    """Lambda authorizer function to allow or deny a request."""

    logging.info("Event: %s", event)
    logging.info("Context: %s", context)

    api_key = "" if "x-api-key" not in event["headers"].keys() else event["headers"]["x-api-key"]
    stored_api_key_trusted = get_api_key("trusted")

    if api_key and api_key == stored_api_key_trusted:
        response_policy = create_policy("trusted_partner", "Allow", event["methodArn"], stored_api_key_trusted)
        logging.info("Created policy for truster partner.")

    else:
        stored_api_key_default = get_api_key("default")
        response_policy = create_policy("default_user", "Allow", event["methodArn"], stored_api_key_default)
        logging.info("Created policy for default user.")

    logging.info("Response: %s", response_policy)
    return json.loads(response_policy)


def get_api_key(key_type):
    """Return API key value from SSM parameter store."""

    ssm_client = connection.ssm_client
    api_key = ssm_client.get_parameter(Name=f"/service/hydrocron/api-key-{key_type}", WithDecryption=True)["Parameter"]["Value"]
    logging.info("Retrieved API key from SSM parameter: /service/hydrocron/api-key-%s", key_type)
    return api_key


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
