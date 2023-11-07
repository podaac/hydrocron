import logging
import os

from flask_testing import TestCase
from hydrocron.api.data_access.db import DynamoDataRepository


class BaseTestCase(TestCase):

    def create_app(self):
        os.environ['HYDROCRON_ENV'] = 'test'
        import hydrocron.api.hydrocron  # noqa: E501 # pylint: disable=import-outside-toplevel
        hydrocron.api.hydrocron.flask_app.config.update({
            "TESTING": True,
        })
        logging.getLogger('connexion.operation').setLevel('DEBUG')

        hydrocron.api.hydrocron.construct_repository = lambda: DynamoDataRepository(self.dynamo_db)
        return hydrocron.api.hydrocron.flask_app
