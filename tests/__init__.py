import logging
import os

from flask_testing import TestCase
from hydrocron_api.data_access.db import DynamoDataRepository


class BaseTestCase(TestCase):

    def create_app(self):
        os.environ['HYDROCRON_ENV'] = 'test'
        import hydrocron_api.hydrocron  # noqa: E501 # pylint: disable=import-outside-toplevel
        hydrocron_api.hydrocron.flask_app.config.update({
            "TESTING": True,
        })
        logging.getLogger('connexion.operation').setLevel('DEBUG')

        hydrocron_api.hydrocron.construct_repository = lambda: DynamoDataRepository(self.dynamo_db)
        return hydrocron_api.hydrocron.flask_app
