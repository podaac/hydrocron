"""
Hydrocron Connection class.
"""

# Standard imports
import os
from types import ModuleType
import sys

# Third-party imports
import boto3
from boto3.resources.base import ServiceResource
import botocore
from botocore.client import BaseClient


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
        self._kms_client = None

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

            s3_session = boto3.session.Session()

            self._s3_resource = s3_session.resource('s3')

        return self._s3_resource

    @property
    def kms_client(self) -> BaseClient:
        """Return SSM client."""

        if not self._kms_client:

            ssm_session = boto3.session.Session()
            self._kms_client = ssm_session.client('kms')

        return self._kms_client


dynamodb_resource: ServiceResource
s3_resource: ServiceResource
kms_client: BaseClient

sys.modules[__name__] = Connection(__name__)
