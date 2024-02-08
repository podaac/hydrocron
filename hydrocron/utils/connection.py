"""
Hydrocron Connection class.
"""

# Standard imports
import base64
import json
import os
from types import ModuleType
import sys

# Third-party imports
import boto3
from boto3.resources.base import ServiceResource
import botocore
import requests

# Local imports
from hydrocron.utils import constants


class Connection(ModuleType):
    """
    Hydrocron connection class for handling AWS service resources.
    """

    APP_NAME = 'hydrocron'
    SSM_PATH = f'/service/{APP_NAME}/'

    def __init__(self, name):
        super().__init__(name)
        self.env = os.getenv('HYDROCRON_ENV', 'prod')
        self._dynamodb_resource = None
        self._dynamodb_endpoint = self._get_dynamodb_endpoint()
        self._s3_resource = None

    def _get_dynamodb_endpoint(self):
        """Return dynamodb endpoint URL."""

        if self.env == "prod":
            ssm = boto3.client('ssm')
            try:
                endpoint = ssm.get_parameter(Name=f"{Connection.SSM_PATH}dynamodb_endpoint_url")
            except botocore.exceptions.ClientError as error:
                if error.response["Error"]["Code"] == "ParameterNotFound":
                    endpoint = None
                else:
                    raise error
        else:
            endpoint = os.getenv(f"{self.APP_NAME.upper()}_dynamodb_endpoint_url", None)

        return endpoint

    @property
    def dynamodb_resource(self) -> ServiceResource:
        """Return DynamoDB session resource."""

        session = boto3.session.Session()
        if not self._dynamodb_resource:
            if self._dynamodb_endpoint:
                self._dynamodb_resource = session.resource('dynamodb', endpoint_url=self._dynamodb_endpoint)
            else:
                self._dynamodb_resource = session.resource('dynamodb')
        return self._dynamodb_resource

    @property
    def s3_resource(self) -> ServiceResource:
        """Return S3 session resource."""

        if not self._s3_resource:
            creds = self.retrieve_credentials()
            s3_session = boto3.session.Session(
                aws_access_key_id=creds['accessKeyId'],
                aws_secret_access_key=creds['secretAccessKey'],
                aws_session_token=creds['sessionToken'],
                region_name='us-west-2')

            self._s3_resource = s3_session.resource('s3')

        return self._s3_resource

    @staticmethod
    def retrieve_credentials():
        """Makes the Oauth calls to authenticate with EDS and return a set of s3
        same-region, read-only credntials.
        """

        login_resp = requests.get(
            constants.S3_CREDS_ENDPOINT,
            allow_redirects=False,
            timeout=5
        )
        login_resp.raise_for_status()

        auth = f"{os.environ['EARTHDATA_USERNAME']}:{os.environ['EARTHDATA_PASSWORD']}"
        encoded_auth = base64.b64encode(auth.encode('ascii'))

        auth_redirect = requests.post(
            login_resp.headers['location'],
            data={"credentials": encoded_auth},
            headers={"Origin": constants.S3_CREDS_ENDPOINT},
            allow_redirects=False,
            timeout=5
        )
        auth_redirect.raise_for_status()

        final = requests.get(
            auth_redirect.headers['location'],
            allow_redirects=False,
            timeout=5
        )

        results = requests.get(
            constants.S3_CREDS_ENDPOINT,
            cookies={'accessToken': final.cookies['accessToken']},
            timeout=5
        )
        results.raise_for_status()

        return json.loads(results.content)


dynamodb_resource: ServiceResource
s3_resource: ServiceResource

sys.modules[__name__] = Connection(__name__)
