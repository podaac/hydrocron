"""
Hydrocron API context module
"""
# flake8: noqa: E501
import os
import sys
from types import ModuleType
from typing import Callable

import boto3

from hydrocron.api.data_access.db import DynamoDataRepository


class Context(ModuleType):
    """
    Hydrocron API context class
    """
    APP_NAME = 'hydrocron'
    SSM_PATH = f'/service/{APP_NAME}/'

    def __init__(self, name: str):
        super().__init__(name)
        self.env = os.getenv('HYDROCRON_ENV', 'prod')
        self._db = None

        if self.env == 'prod':
            self._load_params_from_ssm()
        else:
            from dotenv import load_dotenv  # noqa: E501 # pylint: disable=import-outside-toplevel
            load_dotenv()

    def _load_params_from_ssm(self):
        ssm = boto3.client('ssm')
        parameters = ssm.get_parameters_by_path(
            Path=Context.SSM_PATH,
            WithDecryption=True
        )['Parameters']

        self._ssm_parameters = {}

        for param in parameters:
            name = param['Name'].removeprefix(self.SSM_PATH)
            self._ssm_parameters[name] = param['Value']

    def get_param(self, name):
        """
        Retrieves a parameter from SSM or the environment depending on the
        environment
        """
        if self.env == 'prod':
            return self._ssm_parameters.get(name)

        return os.getenv(f'{self.APP_NAME.upper()}_{name}')

    @property
    def data_repository(self) -> DynamoDataRepository:
        """

        @return:
        """
        if not self._db:
            self._db = self.construct_repository()

        return self._db

    def construct_repository(self):
        """

        @return:
        """
        session = boto3.session.Session()

        if endpoint_url := self.get_param('dynamodb_endpoint_url'):
            dyndb_resource = session.resource('dynamodb', endpoint_url=endpoint_url)
        else:
            dyndb_resource = session.resource('dynamodb')

        return DynamoDataRepository(dyndb_resource)


# Silence the linters
get_param: Callable[[str], str]
data_repository: DynamoDataRepository

sys.modules[__name__] = Context(__name__)
