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
from hydrocron.utils import connection

class Context(ModuleType):
    """
    Hydrocron API context class
    """
    APP_NAME = 'hydrocron'
    SSM_PATH = f'/service/{APP_NAME}/'

    def __init__(self, name: str):
        super().__init__(name)
        self._db = None

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

        return DynamoDataRepository(connection.dynamodb_resource)


# Silence the linters
data_repository: DynamoDataRepository

sys.modules[__name__] = Context(__name__)
