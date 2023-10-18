import logging
import os

from flask_testing import TestCase
from hydrocronapi.data_access.db import DynamoDataRepository


class BaseTestCase(TestCase):

    def create_app(self):
        os.environ['HYDROCRON_ENV'] = 'test'
        import hydrocronapi.hydrocron  # noqa: E501 # pylint: disable=import-outside-toplevel
        hydrocronapi.hydrocron.flask_app.config.update({
            "TESTING": True,
        })
        logging.getLogger('connexion.operation').setLevel('DEBUG')

        hydrocronapi.hydrocron.construct_repository = lambda: DynamoDataRepository(self.dynamo_db)
        return hydrocronapi.hydrocron.flask_app
