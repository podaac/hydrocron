# timeseries

This page serves to document the timeseries request endpoint for the Hydrocron API. The timeseries endpoint retrieves time series data from SWOT observations for reaches and nodes based on a user request which can include the headers and query parameters documented below under "Request Headers" and "Request Parameters".

The timeseries endpoint returns a CSV or GeoJSON response depending on the user request, see "Response Format" below. If something goes wrong the timeseries endpoint returns different response codes to indicate to the user what might have caused an error, see "Response Codes" below.

For more information on using request headers when working with an API like Hydrocron programatically, see: https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation

## Request Headers

### Accept

Accept headers provide more control over the output that is returned by Hydrocron. You can pass the `Accept` header in your request to return a specific response format.

Accept headers: `application/json`, `text/csv`, `application/geo+json`

Possible header and request parameter combinations:

- If the Accept header is `text/csv` or `application/geo+json`, the raw CSV or GeoJSON response is returned.
- If the Accept header is `application/json` with an output field of `geojson`, the entire JSON object with metadata including GeoJSON response is returned.
- If the Accept header is `application/json` with an output field of `csv`, the entire JSON object with metadata including CSV response is returned.
- If the Accept header is `application/json` without an output field, the entire JSON object with metadata including GeoJSON response is returned.
- If the Accept header is none of the accepted types then a 415 Unsupported is returned.
- If no Accept header is passed in the request then the default is to return `application/json` with metadata. The `output` field is used to determine whether a GeoJSON or CSV response is returned in the `results` field of the response.

Example GeoJSON request and response:

```bash
curl -v --header "Accept: application/geo+json" --location 'https://soto.podaac.sit.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

Content-Type: 'application/geo+json'

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": "0",
            "type": "Feature",
            "properties": {
                "reach_id": "63470800171",
                "time_str": "2024-02-01T02:26:50Z",
                "wse": "3386.9332",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": []
            }
        },
        {
            "id": "1",
            "type": "Feature",
            "properties": {
                "reach_id": "63470800171",
                "time_str": "2024-02-08T13:48:41Z",
                "wse": "1453.4136",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": []
            }
        }
    ]
}
```

*Coordinates removed

Example CSV request and response:

```bash
curl -v --header "Accept: text/csv" --location 'https://soto.podaac.sit.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

Content-Type: text/csv

```json
"reach_id,time_str,wse,wse_units\n63470800171,2024-02-01T02:26:50Z,3386.9332,m\n63470800171,2024-02-08T13:48:41Z,1453.4136,m\n"
```

## Request Parameters

(feature)=
### feature : string, required: yes

Type of feature being requested. Either: "Reach", "Node" or "PriorLake"

(feature_id)=
### feature_id : string, required: yes

ID of the feature to retrieve

- Reaches have the format CBBBBBRRRRT (e.g., 78340600051)
- Nodes have the format CBBBBBRRRRNNNT (e.g., 12228200110861)
- PriorLakes have the format CBBNNNNNNT (e.g., 2710046612)

Please see the [SWOT Product Description Document for the L2_HR_RiverSP Dataset](https://podaac.jpl.nasa.gov/SWOT?tab=datasets-information&sections=about) for more information on reach and node identifiers.
Please see the [SWOT Product Description Document for the L2_HR_LakeSP Dataset](https://podaac.jpl.nasa.gov/SWOT?tab=datasets-information&sections=about) for more information on lake identifiers.

### start_time : string, required: yes

Start time of the time series in the form of YYYY-MM-DDTHH:MM:SSZ (e.g., 2023-08-04T00:00:00Z)

The time can include a UTC offset which is specified in the form of &pm;HH:MM or &pm;HHMM so the entire time format can be: YYYY-MM-DDTHH:MM:SSZ&pm;HH:MM.

Please note you will need to encode offsets that use the `+` sign with `%2b` so that the parameters in the URL used to query the API passes the correct character to the API.

Example:

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### end_time : string, required: yes

End time of the time series in the form of YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-01-25T00:00:00Z)

The time can include a UTC offset which is specified in the form of &pm;HH:MM or &pm;HHMM so the entire time format can be: YYYY-MM-DDTHH:MM:SSZ&pm;HH:MM.

Please note you will need to encode offsets that use the `+` sign with `%2b` so that the parameters in the URL used to query the API passes the correct character to the API.

Example:

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### output : string, required: no

Format of the data returned. Either: "csv" or "geojson"

### compact: string, required: no

Whether to return a 'compact' GeoJSON response. Either: "true" or "false"

The default for header `Accept: application/geo+json` is to set compact to `true` if it is not provided. The default header for `application/json` is to set compact to `false` if it is not provided. See "Response" section for details on the returned compact response.

(collection_name)=
### collection_name: string, required: no

The name of the collection to return. Allows users to explicitly request data from a particular version of the data.
Supported collection names include:

Version C/2.0 (default):

- SWOT_L2_HR_RiverSP_2.0,
- SWOT_L2_HR_RiverSP_reach_2.0,
- SWOT_L2_HR_RiverSP_node_2.0,
- SWOT_L2_HR_LakeSP_2.0,
- SWOT_L2_HR_LakeSP_prior_2.0,

Version D:

- SWOT_L2_HR_RiverSP_D,
- SWOT_L2_HR_RiverSP_reach_D,
- SWOT_L2_HR_RiverSP_node_D,
- SWOT_L2_HR_LakeSP_D,
- SWOT_L2_HR_LakeSP_prior_D

(fields)=
### fields : string, required: yes

The SWOT data fields to return in the request.

This is specified in the form of a comma separated list (without any spaces): `fields=reach_id,time_str,wse,slope`

Hydrocron includes additional fields beyond the source data shapefile attributes, including units fields on measurements, cycle and pass information, SWORD and PLD (prior river and lake database names), and collection versions. **NOTE: Units are always returned for fields that have corresponding units stored in Hydrocron, they do not need to be requested.** The complete list of input fields that are available through Hydrocron are described in the [](fields-detail) section.

## Response Format

### Default

This includes cases where Accept header is not included or equals `*/*` or `application/json`.

Returns a JSON response that contains CSV or GeoJSON in `results` object with a Content-Type set to  'application/json'.

If the user sends a request parameter of `output=csv` then the `results` object will contain CSV data of the requested fields.

Example CSV response:

```json
{
    "status": "200 OK",
    "time": 806.886,
    "hits": 4,
    "results": {
        "csv": "reach_id,time_str,wse,geometry,wse_units\n72390300011,2024-01-29T15:06:46Z,41.2087,\"LINESTRING (-62.159497 50.285927)\",m\n",
        "geojson": {}
    }
}
```

If the user sends a request parameter of `output=geojson` then the `results` object will contain GeoJSON data of the requested fields.

Example JSON response:

```json
{
    "status": "200 OK",
    "time": 723.004,
    "hits": 2,
    "results": {
        "csv": "",
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "63470800171",
                        "time_str": "2024-02-01T02:26:50Z",
                        "wse": "3386.9332",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [
                                -45.845445,
                                -16.166559
                            ]
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "63470800171",
                        "time_str": "2024-02-08T13:48:41Z",
                        "wse": "1453.4136",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [
                                -45.845445,
                                -16.166559
                            ]
                        ]
                    }
                }
            ]
        }
    }
}
```

If the user sends a request parameter of `compact=true` and the request parameter `output=geojson`, the response will be compacted. The compacted response appends time series data into a single list for each requested field and is stored under the `properties` object in the `results` object.

Only one Feature is ever returned as the data is aggregated under a single "Feature". The geometry for the data is included in the response's `geometry` object which is listed once as there is only one Feature represented in the response.

Example compacted JSON response:

```json
{
    "status": "200 OK",
    "time": 2175.824,
    "hits": 2,
    "results": {
        "csv": "",
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "reach_id": [
                            "63470800171",
                            "63470800171"
                        ],
                        "time_str": [
                            "2024-02-01T02:26:50Z",
                            "2024-02-08T13:48:41Z"
                        ],
                        "wse": [
                            "3386.9332",
                            "1453.4136"
                        ],
                        "wse_units": [
                            "m",
                            "m"
                        ]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            -45.845445,
                            -16.166559
                        ]
                    }
                }
            ]
        }
    }
}
```

*Coordinates removed

### application/geo+json

When the `Accept` header is set to `application/geo+json` and there is no `output` request parameter, a GeoJSON response is returned with a Content-Type set to 'application/geo+json'.

The default behavior is to compact the response into a single "Feature". The compacted response appends time series data into a single list for each requested field and includes a single geometry object for the data.

Example compacted GeoJSON response:

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": "0",
            "type": "Feature",
            "properties": {
                "reach_id": [
                    "63470800171",
                    "63470800171"
                ],
                "time_str": [
                    "2024-02-01T02:26:50Z",
                    "2024-02-08T13:48:41Z"
                ],
                "wse": [
                    "3386.9332",
                    "1453.4136"
                ],
                "wse_units": [
                    "m",
                    "m"
                ]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [
                        -45.845445,
                        -16.166559
                    ]
                ]
            }
        }
    ]
}
```

*Coordinates removed

If the user sends a request parameter of `compact=false` then the GeoJSON response will not be compacted and there will be one "Feature" per time step.

Example GeoJSON response that is not compacted:

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": "0",
            "type": "Feature",
            "properties": {
                "reach_id": "63470800171",
                "time_str": "2024-02-01T02:26:50Z",
                "wse": "3386.9332",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": []
            }
        },
        {
            "id": "1",
            "type": "Feature",
            "properties": {
                "reach_id": "63470800171",
                "time_str": "2024-02-08T13:48:41Z",
                "wse": "1453.4136",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": []
            }
        }
    ]
}
```

*Coordinates removed

### text/csv

When the `Accept` header is set to `text/csv` and there is no `output` request parameter, a CSV response is returned with Content-Type set to 'text/csv'.

Example CSV response:

```bash
"reach_id,time_str,wse,wse_units\n63470800171,2024-02-01T02:26:50Z,3386.9332,m\n63470800171,2024-02-08T13:48:41Z,1453.4136,m\n"
```

## Response Codes

| Code    | Reason                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200     | Request has succeeded and response has been returned to the user.                                                                                                           |
| 400*    | 'Bad Request': This indicates that the end user entered the parameters incorrectly in their query or time series data could not be located for the feature ID. The API attempts to send a response as to which parameter was incorrect. |
| 413     | 'Payload Too Large': The user attempted to retrieve a response that was too large. This is triggered for queries that exceed 6mb.                                           |
| 500     | 'Internal Server Error': Internal API error.                                                                                                                                |
| 415     | 'Unsupported Media Type': The user send an invalid `Accept` header.                                                                                                         |

*The 400 code is also currently returned for queries where no time series data could be located for the request specified feature ID. The message returned with the response indicates this and it can be helpful to adjust the date ranges you are searching.

## API Keys

Users may request a special API key for cases where their intended usage of the API may be considered heavy or more complex. Heavy usage can be defined as continued use with many requests per hour or day or continued use which may require many requests per second or concurrent requests. To request an API key or to discuss your use case, please submit a [GitHub issue](https://github.com/podaac/hydrocron/issues).

**Note: Users do *not* have to send an API key in their request to use the Hydrocron API. The API key is optional.**

### How to use an API key in requests

Hydrocron API key header: `x-hydrocron-key`

After receiving the API key, users may send the API key in their request under the `x-hydrocron-key` header.

Example

```bash
curl --header 'x-hydrocron-key: <podaac-provided-api-key>' --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

Replace `<podaac-provided-api-key>` with the API key provided to you.

Python Example

```python
import requests

url = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"

headers = {
    "x-hydrocon-key": "<podaac-provided-api-key>"
}

params = {
    "feature": "Reach",
    "feature_id": "63470800171",
    "output": "csv",
    "start_time": "2024-02-01T00:00:00%2b00:00",
    "end_time": "2024-10-30T00:00:00%2b00:00",
    "fields": "reach_id,time_str,wse,slope,width"
}

response = requests.get(url=url, headers=headers, params=params)
```

Replace `<podaac-provided-api-key>` with the API key provided to you.
