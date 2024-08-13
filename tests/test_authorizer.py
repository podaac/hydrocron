"""
Test Lambda authorizer.
"""

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
        
        # Create SSM client and put API keys
        ssm = boto3.client("ssm")
        ssm.put_parameter(Name="/service/hydrocron/api-key-default", Value="abc123", Type="SecureString")
        ssm.put_parameter(Name="/service/hydrocron/api-key-trusted", Value='["def456", "qrs789"]', Type="SecureString")
        
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