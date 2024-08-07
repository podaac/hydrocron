"""
Test Lambda authorizer.
"""

import base64
import json
import os
import pathlib
import unittest

import boto3
import moto

class TestAuthorizer(unittest.TestCase):

    def setUp(self):

        # Set up mock
        self.mock_aws = moto.mock_aws()
        self.mock_aws.start()

        # Set region
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"

        # Create KMS key and encrypt API keys
        kms = boto3.client("kms")
        key_id = kms.create_key(Description="test kms key")["KeyMetadata"]["KeyId"]        
        
        kms.create_alias(
            AliasName="alias/hydrocron-test-lambda-key",
            TargetKeyId=key_id
        )
        os.environ["VENUE_PREFIX"] = "hydrocron-test"
        
        default = kms.encrypt(
            KeyId=key_id,
            Plaintext=b'abc123'
        )
        os.environ["API_KEY_DEFAULT"] = base64.b64encode(default["CiphertextBlob"]).decode("utf-8")
        
        json_string = json.dumps(["def456", "xyz321"]).encode("utf-8")
        trusted = kms.encrypt(
            KeyId=key_id,
            Plaintext=json_string
        )
        os.environ["API_KEY_TRUSTED"] = base64.b64encode(trusted["CiphertextBlob"]).decode("utf-8")


    def tearDown(self):

        self.mock_aws.stop()


    def test_authorizer_lambda_handler_default(self):
        """
        Test the lambda handler for the Lambda authorizer for default users.
        """
        import hydrocron.api.controllers.authorizer

        test_event = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                    .joinpath('test_data').joinpath('api_authorizer_default.json'))
        with open(test_event) as jf:
            event = json.load(jf)
        context = "_"
        
        result = hydrocron.api.controllers.authorizer.authorization_handler(event, context)
        
        expected_policy = {
            "principalId": "default_user",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": "arn:aws:execute-api:us-west-2:xxxx:xxxx/v1/GET/timeseries"
                }
                ]
            },
            "usageIdentifierKey": "abc123"
        }
        
        self.assertEqual(result, expected_policy)
        
    def test_authorizer_lambda_handler_trusted(self):
        """
        Test the lambda handler for the Lambda authorizer for trusted users.
        """
        import hydrocron.api.controllers.authorizer

        
        test_event = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                    .joinpath('test_data').joinpath('api_authorizer_trusted.json'))
        with open(test_event) as jf:
            event = json.load(jf)
        context = "_"
        
        result = hydrocron.api.controllers.authorizer.authorization_handler(event, context)
        
        expected_policy = {
            "principalId": "trusted_partner",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": "arn:aws:execute-api:us-west-2:xxxx:xxxx/v1/GET/timeseries"
                }
                ]
            },
            "usageIdentifierKey": "def456"
        }
        
        self.assertEqual(result, expected_policy)