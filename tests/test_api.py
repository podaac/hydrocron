"""
Tests for API queries
"""
import csv
import os.path
import pathlib

import pytest
import geojson
import geopandas as gpd
import json
import numpy as np
from numpy.testing import assert_almost_equal


def test_timeseries_lambda_handler_json(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result['status'] == '200 OK' and \
           result['results']['geojson'] == expected


def test_timeseries_lambda_handler_validate_geojson_reach(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint response for valid GeoJSON
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,slope,time"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    assert geojson.loads(json.dumps((result['results']['geojson']))).is_valid


def test_timeseries_lambda_handler_csv(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """

    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "csv",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    assert result['status'] == '200 OK'
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__))).joinpath('test_data').joinpath('api_query_results_csv.csv'))
    with open(test_data) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar=None)
        row_str = ""
        for row in csv_reader:
            row_str += f"{','.join(row)}\n"
        
    assert result['results']['csv'] == row_str


def test_timeseries_convert_to_df_lake():
    """
    Test conver_to_df function to make sure it creates a correctly formatted
    GeoDataFrame.
    """
    import hydrocron.api.controllers.timeseries

    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_items_lake.json'))
    with open(test_data) as jf:
        items = json.load(jf)
    gdf = hydrocron.api.controllers.timeseries.convert_to_df(items)
    assert_almost_equal(np.array([-999999999999.0, -999999999999.0], dtype=np.float64),
                        gdf['wse'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([68.693765, 68.693765], dtype=np.float64),
                        gdf['p_lat'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([-999999999999.0, -999999999999.0], dtype=np.float64),
                        gdf['time'].to_numpy().astype(np.float64))
    geo_array = gpd.points_from_xy(x=[-121.362755, -121.362755],
                                   y=[50.415171, 50.415171]).to_numpy()
    assert str(geo_array) == str(gdf['geometry'].to_numpy())


def test_timeseries_convert_to_df_node():
    """
    Test conver_to_df function to make sure it creates a correctly formatted
    GeoDataFrame.
    """
    import hydrocron.api.controllers.timeseries

    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_items_node.json'))
    with open(test_data) as jf:
        items = json.load(jf)
    gdf = hydrocron.api.controllers.timeseries.convert_to_df(items)
    assert_almost_equal(np.array([319.3727, 321.95384, 320.88183], dtype=np.float64),
                        gdf['wse'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([-999999999999.0, -999999999999.0, -999999999999.0], dtype=np.float64),
                        gdf['width'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([735105930.351, 735449281.545, 735792633.34], dtype=np.float64),
                        gdf['time'].to_numpy().astype(np.float64))
    geo_array = gpd.points_from_xy(x=[-95.060448, -95.060448, -95.060448],
                                   y=[49.359134, 49.359134, 49.359134]).to_numpy()
    assert str(geo_array) == str(gdf['geometry'].to_numpy())


def test_timeseries_convert_to_df_reach():
    """
    Test conver_to_df function to make sure it creates a correctly formatted
    GeoDataFrame.
    """
    import hydrocron.api.controllers.timeseries

    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_items_reach.json'))
    with open(test_data) as jf:
        items = json.load(jf)
    gdf = hydrocron.api.controllers.timeseries.convert_to_df(items)
    assert_almost_equal(np.array([320.2114, 322.3147, 323.3131], dtype=np.float64),
                        gdf['wse'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([-999999999999.0, -999999999999.0, -999999999999.0], dtype=np.float64),
                        gdf['width'].to_numpy().astype(np.float64))
    assert_almost_equal(np.array([-999999999999.0, -999999999999.0, -999999999999.0], dtype=np.float64),
                        gdf['slope'].to_numpy().astype(np.float64))


def test_add_units():
    """
    Test add_units function.
    """

    import hydrocron.api.controllers.timeseries

    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_items_reach.json'))
    with open(test_data) as jf:
        items = json.load(jf)
    gdf = hydrocron.api.controllers.timeseries.convert_to_df(items)

    columns = ["reach_id", "wse", "width", "slope", "slope2", "geometry"]
    columns = hydrocron.api.controllers.timeseries.add_units(gdf, columns)

    expected_columns = ["reach_id", "wse", "width", "slope", "slope2", "geometry", "wse_units", "width_units",
                        "slope_units", "slope2_units"]
    assert expected_columns == columns


def test_timeseries_lambda_handler_missing():
    """
    Test the lambda handler for the timeseries endpoint for missing parameters
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {},
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }
    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: This required parameter is missing: 'feature'" in str(e.value)

    event = {
        "body": {
            "feature": "Reach",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }
    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: This required parameter is missing: 'feature_id'" in str(e.value)


def test_timeseries_lambda_handler_feature():
    """
    Test the lambda handler for the timeseries endpoint for feature parameter
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "River",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: feature parameter should be Reach, Node, or PriorLake, not: River" in str(e.value)


def test_timeseries_lambda_handler_feature_id():
    """
    Test the lambda handler for the timeseries endpoint for feature_id parameter
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "7122ff4100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: feature_id cannot contain letters: 7122ff4100223" in str(e.value)


def test_timeseries_lambda_handler_dates():
    """
    Test the lambda handler for the timeseries endpoint for start_time and 
    end_time parameters
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023/06/04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    assert "400: start_time and end_time parameters must conform to format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS-00:00" in str(
        e.value)


def test_timeseries_lambda_handler_output():
    """
    Test the lambda handler for the timeseries output parameters
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "txt",
            "fields": "reach_id,time_str,wse,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: output parameter should be csv or geojson, not: txt" in str(e.value)


def test_timeseries_lambda_handler_fields():
    """
    Test the lambda handler for the timeseries output parameters
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry,height"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: fields parameter should contain valid SWOT fields" in str(e.value)


def test_timeseries_lambda_handler_not_found():
    """
    Test the lambda handler for cases where the identifier is not found in the
    database.
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100227",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,geometry,height"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: Results with the specified Feature ID 71224100227 were not found" in str(e.value)


def test_timeseries_lambda_handler_elastic_agent():
    """
    Test the lambda handler for cases where invoked by Elastic Agent.
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {},
        "headers": {
            "User-Agent": "Elastic-Heartbeat/7.16.2 (linux; amd64; 3c518f4d17a15dc85bdd68a5a03d5af51d9edd8e; 2021-12-18 21:10:52 +0000 UTC)",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    assert result == {}


def test_timeseries_lambda_handler_missing_header():
    """
    Test the lambda handler for cases where invoked by Elastic Agent.
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {},
        "headers": {}
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: Issue encountered with request headers" in str(e.value)


def test_timeseries_lambda_handler_geojson_accept(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid",
            "compact": "false"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "application/geo+json"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result == expected


def test_timeseries_lambda_handler_csv_accept(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """

    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid,geometry"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "text/csv"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)

    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__))).joinpath('test_data').joinpath('api_query_results_csv.csv'))
    with open(test_data) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar=None)
        row_str = ""
        for row in csv_reader:
            row_str += f"{','.join(row)}\n"
        
    assert result == row_str


def test_timeseries_lambda_handler_geojson_accept_output():
    """
    Test the lambda handler for the timeseries endpoint
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "application/geo+json"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: Invalid combination of Accept header and output request parameter" in str(e.value)


def test_timeseries_lambda_handler_json_no_output(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result['status'] == '200 OK' and \
           result['results']['geojson'] == expected


def test_timeseries_lambda_handler_json_multi_accept(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "image/webp,image/*,*/*;q=0.8"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result['status'] == '200 OK' and \
           result['results']['geojson'] == expected


def test_timeseries_lambda_handler_unsupported():
    """
    Test the lambda handler for the timeseries endpoint
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "image/jpg"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "415: Unsupported media type in Accept request header: image/jpg." in str(e.value)


def test_timeseries_lambda_handler_reachid_not_found():
    """
    Test the lambda handler for the timeseries endpoint
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100228",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "image/jpg"
        }
    }

    context = "_"
    with pytest.raises(hydrocron.api.controllers.timeseries.RequestError) as e:
        hydrocron.api.controllers.timeseries.lambda_handler(event, context)
        assert "400: Results with the specified Feature ID 71224100228 were not found" in str(e.value)


def test_timeseries_lambda_handler_json_compact(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "output": "geojson",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid",
            "compact": "true"
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson_compact.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result['status'] == '200 OK' and \
           result['results']['geojson'] == expected


def test_timeseries_lambda_handler_geojson_accept_compact(hydrocron_api):
    """
    Test the lambda handler for the timeseries endpoint
    Parameters
    ----------
    hydrocron_api: Fixture ensuring the database is configured for the api
    """
    import hydrocron.api.controllers.timeseries

    event = {
        "body": {
            "feature": "Reach",
            "feature_id": "71224100223",
            "start_time": "2023-06-04T00:00:00Z",
            "end_time": "2023-06-23T00:00:00Z",
            "fields": "reach_id,time_str,wse,sword_version,collection_shortname,crid",
        },
        "headers": {
            "User-Agent": "curl/8.4.0",
            "X-Forwarded-For": "123.456.789.000",
            "Accept": "application/geo+json"
        }
    }

    context = "_"
    result = hydrocron.api.controllers.timeseries.lambda_handler(event, context)
    test_data = (pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
                 .joinpath('test_data').joinpath('api_query_results_geojson_compact.json'))
    with open(test_data) as jf:
        expected = json.load(jf)
    assert result == expected