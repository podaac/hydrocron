"""
Class to test Connection class which handles access to AWS service resources.
"""

# Local imports
import os
from hydrocron.utils.constants import DB_TEST_TABLE_NAME


def test_dynamodb_resource():
    """Test retrieval of DynamoDB resource."""

    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
    from hydrocron.utils import connection
    assert connection.dynamodb_resource.Table(DB_TEST_TABLE_NAME).name == "hydrocron-swot-test-table"


def test_s3_resource(s3_connection):
    """Test retrieval of S3 resource."""

    # Import module
    from hydrocron.utils import connection
    assert type(connection.s3_resource).__name__ == "s3.ServiceResource"
    
def test_ssm_client():
    """Test retrieval of SSM client."""

    # Import module
    from hydrocron.utils import connection
    assert type(connection.ssm_client).__name__ == "SSM"

def test_ssm_client():
    """Test retrieval of SNS client."""

    # Import module
    from hydrocron.utils import connection
    assert type(connection.sns_client).__name__ == "SNS"   