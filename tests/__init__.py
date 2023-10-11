import logging
import os
from collections import namedtuple

import hydrocron_db.load_data
from flask_testing import TestCase
from hydrocron_db.hydrocron_database import HydrocronDB
from mypy_boto3_dynamodb import ServiceResource

from hydrocronapi.data_access.db import DynamoDataRepository


class BaseTestCase(TestCase):

    def load_test_data(self, dynamo_resource: ServiceResource):
        Args = namedtuple('Args', ['table_name', 'start', 'end'])

        hydrocron_db.load_data.setup_connection = lambda: HydrocronDB(dyn_resource=dynamo_resource)
        hydrocron_db.load_data.find_new_granules = lambda *_: [
            (os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'),)
        ]
        hydrocron_db.load_data.run(Args('hydrocron-swot-reach-table', None, None))

        hydrocron_db.load_data.find_new_granules = lambda *_: [
            (os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'SWOT_L2_HR_RiverSP_Node_540_010_AS_20230602T193520_20230602T193521_PIA1_01.zip'),),
        ]
        hydrocron_db.load_data.run(Args('hydrocron-swot-node-table', None, None))

    def create_app(self):
        os.environ['HYDROCRON_ENV'] = 'test'
        import hydrocronapi.hydrocron  # noqa: E501 # pylint: disable=import-outside-toplevel
        hydrocronapi.hydrocron.flask_app.config.update({
            "TESTING": True,
        })
        logging.getLogger('connexion.operation').setLevel('DEBUG')

        hydrocronapi.hydrocron.construct_repository = lambda: DynamoDataRepository(self.dynamo_db)
        self.load_test_data(self.dynamo_db)

        return hydrocronapi.hydrocron.flask_app
