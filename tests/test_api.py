from hydrocron.utils.constants import TEST_REACH_ID_VALUE


def test_timeseries_lambda_handler(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries
    # TODO: Implement test
    event = {
        "body": {
            "feature": "Reach",
            "reach_id": "71224100223",
            "start_time": "2022-08-04T00:00:00+00:00",
            "end_time": "2022-08-23T00:00:00+00:00",
            "output": "csv",
            "fields": "feature_id,time_str,wse"
        }
    }

    result = hydrocron.api.controllers.timeseries.lambda_handler(event, {})
    print(result)
    assert result['status'] == '200 OK'
