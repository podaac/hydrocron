"""
Class to test Connection class which handles access to AWS service resources.
"""

# Standard imports
import unittest

# Local imports
from hydrocron.utils.constants import DB_TEST_TABLE_NAME


class TestConnection(unittest.TestCase):
    """Test Connection class."""

    # def setUp(self):
    #     """ Set environment variables."""

    #     # Set environment variables
    #     os.environ['HYDROCRON_ENV'] = 'LOCAL'
    #     os.environ['HYDROCRON_dynamodb_endpoint_url'] = 'http://localhost:8000'
    #     os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAW5KWYZA4HRSZUDXY'
    #     os.environ['AWS_SECRET_ACCESS_KEY'] = '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'
    #     os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

    def test_dynamodb_resource(self):
        """Test retrieval of DynamoDB resource."""

        # Import module
        from hydrocron.utils import connection

        assert connection.dynamodb_resource.Table(DB_TEST_TABLE_NAME).name == "hydrocron-swot-test-table"
