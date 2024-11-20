import os
os.environ['HYDROCRON_ENV'] = 'LOCAL'
os.environ['HYDROCRON_dynamodb_endpoint_url'] = 'http://localhost:8000'
os.environ['AWS_ACCESS_KEY_ID'] = 'fakeMyKeyId'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fakeSecretAccessKey'
os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

import hydrocron.db.load_data
import hydrocron.api.hydrocron

from hydrocron.db import HydrocronTable
from hydrocron.utils import constants



hydrocron.db.load_data.load_data(
    HydrocronTable(hydrocron.api.hydrocron.data_repository._dynamo_instance, constants.SWOT_REACH_TABLE_NAME),
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'data',
        'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa
    ), True)

hydrocron.db.load_data.load_data(HydrocronTable(
    hydrocron.api.hydrocron.data_repository._dynamo_instance, constants.SWOT_NODE_TABLE_NAME), os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
    'SWOT_L2_HR_RiverSP_Node_540_010_AS_20230602T193520_20230602T193521_PIA1_01.zip'  # noqa
), True)
