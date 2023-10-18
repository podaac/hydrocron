# coding: utf-8
import pytest

from tests import BaseTestCase

    
@pytest.mark.usefixtures("hydrocron_dynamo_instance")
class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_getsubset_get(self):
        """Test case for getsubset_get

        Subset by time series for a given spatial region
        """
        subsetpolygon_example = '{"features":[{"type":"Feature","geometry":{"coordinates":[[-95.6499095054704,50.323685647314554],[-95.3499095054704,50.323685647314554],[-95.3499095054704,50.19088502467528],[-95.6499095054704,50.19088502467528],[-95.6499095054704,50.323685647314554]],"type":"LineString"},"properties":{}}],"type":"FeatureCollection"}'

        query_string = [('feature', 'Reach'),
                        ('subsetpolygon', subsetpolygon_example),
                        ('start_time', '2013-10-20T19:20:30+01:00'),
                        ('end_time', '2013-10-20T19:20:30+01:00'),
                        ('format', 'csv')]
        response = self.client.open(
            '/hydrocron/HydroAPI/1.0.0/timeseriesSubset',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_gettimeseries_get(self):
        """Test case for gettimeseries_get

        Get Timeseries for a particular Reach, Node, or LakeID
        """
        query_string = [('feature', 'Reach'),
                        ('feature_id', '73254700251'),
                        ('format', 'csv'),
                        ('start_time', '2022-08-04T00:00:00+00:00'),
                        ('end_time', '2022-08-23T00:00:00+00:00')]
        response = self.client.open(
            '/hydrocron/HydroAPI/1.0.0/timeseries',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest

    unittest.main()
