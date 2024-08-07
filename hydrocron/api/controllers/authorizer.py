"""
Lambda Authorizer to facilitate usage of API keys and usage plans.

Taken from example:
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""

import base64
import json
import logging
import os

from hydrocron.utils import connection


logging.getLogger().setLevel(logging.INFO)


KMS_CLIENT = connection.kms_client


def authorization_handler(event, context):
    """Lambda authorizer function to allow or deny a request."""

    logging.info("Event: %s", event)
    logging.info("Context: %s", context)

    api_key_trusted = "" if "x-hydrocron-key" not in event["headers"].keys() else event["headers"]["x-hydrocron-key"]
    trusted_ciphertext = base64.b64decode(os.getenv("API_KEY_TRUSTED"))
    trusted_key_list = json.loads(decrypt_key(trusted_ciphertext))

    if api_key_trusted and api_key_trusted in trusted_key_list:
        response_policy = create_policy("trusted_partner", "Allow", event["methodArn"], api_key_trusted)
        logging.info("Created policy for truster partner.")

    else:
        default_ciphertext = base64.b64decode(os.getenv("API_KEY_DEFAULT"))
        default_key = decrypt_key(default_ciphertext)
        response_policy = create_policy("default_user", "Allow", event["methodArn"], default_key)
        logging.info("Created policy for default user.")

    logging.info("Response: %s", response_policy)
    return json.loads(response_policy)


def decrypt_key(ciphertext_blob):
    """Decrypt API key environment variables."""

    key = KMS_CLIENT.decrypt(
        CiphertextBlob=ciphertext_blob,
        KeyId=f"alias/{os.getenv('VENUE_PREFIX')}-lambda-key"
    )
    return key["Plaintext"].decode("utf-8")


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
