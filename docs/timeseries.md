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
curl -v --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
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
        "reach_id": ["63470800171", "63470800171", "63470800171", ...],
        "time_str": ["2024-02-08T13:48:48Z", "2024-02-12T00:49:59Z", "2024-02-29T10:33:53Z", ...],
        "wse": ["493.9646", "495.8134", "489.3664", ...],
        "wse_units": ["m", "m", "m", ...]
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [[-46.100781, -15.940864], [-46.101059, -15.940592], ...295 total...]
      }
    }
  ]
}
```

Example CSV request and response:

```bash
curl -v --header "Accept: text/csv" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

Content-Type: text/csv

```
"reach_id,time_str,wse,wse_units\n63470800171,2024-02-08T13:48:48Z,493.9646,m\n63470800171,2024-02-12T00:49:59Z,495.8134,m\n...\n"
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

Please see the [SWOT Product Description Document for the L2_HR_RiverSP Dataset](https://www.earthdata.nasa.gov/data/catalog/pocloud-swot-l2-hr-riversp-d-d) for more information on reach and node identifiers.
Please see the [SWOT Product Description Document for the L2_HR_LakeSP Dataset](https://www.earthdata.nasa.gov/data/catalog/pocloud-swot-l2-hr-lakesp-d-d) for more information on lake identifiers.

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

Format of the data returned. Either: "csv", "geojson", or "csv_file"

- `csv` — returns CSV data in the JSON response body
- `geojson` — returns GeoJSON data in the JSON response body
- `csv_file` — triggers a CSV file download in the browser with a `Content-Disposition: attachment` header

### filename : string, required: no

Custom filename for the downloaded CSV file. Only used when `output=csv_file`. If not provided, a default filename is generated in the format: `hydrocron_{feature}_{feature_id}_{start_date}_{end_date}.csv`

For reach and node requests ([](#node_fields)), the default is `hydrocron_Reach_nodes_{feature_id}_{start_date}_{end_date}.csv`.

The filename is sanitized to only allow safe characters (`a-z`, `A-Z`, `0-9`, `_`, `-`, `.`). If the filename does not end with `.csv`, the extension is appended automatically. Maximum length is 200 characters.

### compact: string, required: no

Whether to return a 'compact' GeoJSON response. Either: "true" or "false"

The default for header `Accept: application/geo+json` is to set compact to `true` if it is not provided. The default header for `application/json` is to set compact to `false` if it is not provided. See "Response" section for details on the returned compact response.

(collection_name)=
### collection_name: string, required: no

The name of the collection to query. Allows users to request data from a specific version or feature type. If omitted, defaults to a Version D collection.

| Collection Name | Version | Scope |
|-----------------|---------|-------|
| `SWOT_L2_HR_RiverSP_D` | D (default) | All river data (reaches and nodes) |
| `SWOT_L2_HR_RiverSP_reach_D` | D | Reaches only |
| `SWOT_L2_HR_RiverSP_node_D` | D | Nodes only |
| `SWOT_L2_HR_LakeSP_D` | D (default) | Lake data |
| `SWOT_L2_HR_LakeSP_prior_D` | D | Prior lakes only |
| `SWOT_L2_HR_RiverSP_2.0` | 2.0 | All river data (reaches and nodes) |
| `SWOT_L2_HR_RiverSP_reach_2.0` | 2.0 | Reaches only |
| `SWOT_L2_HR_RiverSP_node_2.0` | 2.0 | Nodes only |
| `SWOT_L2_HR_LakeSP_2.0` | 2.0 | Lake data |
| `SWOT_L2_HR_LakeSP_prior_2.0` | 2.0 | Prior lakes only |

SoS discharge fields (`sos_consensus_q`, `sos_hivdi_q`, etc.) are only available on river reaches in the Version 2.0 collection. To request them, set `collection_name=SWOT_L2_HR_RiverSP_2.0`. See the [discharge guide](user-guide/discharge.md) for details.

(fields)=
### fields : string, required: yes

The SWOT data fields to return in the request.

This is specified in the form of a comma separated list: `fields=reach_id,time_str,wse,slope`

Hydrocron includes additional fields beyond the source data shapefile attributes, including units fields on measurements, cycle and pass information, SWORD and PLD (prior river and lake database names), and collection versions. **NOTE: Units are always returned for fields that have corresponding units stored in Hydrocron, they do not need to be requested.** The complete list of input fields that are available through Hydrocron are described in the [](#fields-detail) section.

River reaches in the Version 2.0 collection also expose SoS discharge fields (`sos_consensus_q`, `sos_hivdi_q`, `sos_metroman_q`, `sos_momma_q`, `sos_sad_q`, `sos_sic4dvar_q`, `sos_lakeflow_q`, and `swot_discharge_reanalysis`). These require `collection_name=SWOT_L2_HR_RiverSP_2.0`. See the [discharge guide](user-guide/discharge.md) for details.

(node_fields)=
### node_fields : string, required: no

Return a reach **and all of its nodes** in one request. Only valid with `feature=Reach`.

When `node_fields` is present, the response contains the reach's time series and the time series of every node on that reach. [](#fields) sets the reach columns and `node_fields` sets the node columns, in the same comma separated form: `node_fields=node_id,time_str,wse,node_q`

- Valid node fields are listed in the [](#fields-detail) section. Units are returned automatically, as with [](#fields).
- Nodes come from the same collection version as the reach ([](#collection_name)).
- Version D only node fields (`wse_sm`, `wse_sm_u`, `wse_sm_q`, `wse_sm_q_b`) return a 400 with a Version 2.0 collection.
- A 400 is returned if `node_fields` is used with `feature=Node` or `feature=PriorLake`, is empty, or contains a field that is not a node field.
- A 413 is returned if the reach has more than 25,000 node rows in the requested time range. Reduce the time range.

See [](#reach-and-node-responses) for the response layout.

## Response Format

### Default

This includes cases where Accept header is not included or equals `*/*` or `application/json`.

Returns a JSON response that contains CSV or GeoJSON in `results` object with a Content-Type set to  'application/json'.

If the user sends a request parameter of `output=csv` then the `results` object will contain CSV data of the requested fields.

Example CSV response:

```json
{
    "status": "200 OK",
    "time": 697.498,
    "hits": 10,
    "results": {
        "csv": "reach_id,time_str,wse,wse_units\n78340600051,2024-02-03T18:34:05Z,386.9557,m\n78340600051,2024-02-09T08:00:46Z,-999999999999.0,m\n...\n",
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
    "hits": 25,
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
                        "time_str": "2024-02-08T13:48:48Z",
                        "wse": "493.9646",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-46.100781, -15.940864],
                            "...",
                            [-46.122559, -15.875454]
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "63470800171",
                        "time_str": "2024-02-12T00:49:59Z",
                        "wse": "495.8134",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-46.100781, -15.940864],
                            "...",
                            [-46.122559, -15.875454]
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
    "hits": 25,
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
                            "63470800171",
                            "..."
                        ],
                        "time_str": [
                            "2024-02-08T13:48:48Z",
                            "2024-02-12T00:49:59Z",
                            "..."
                        ],
                        "wse": [
                            "493.9646",
                            "495.8134",
                            "..."
                        ],
                        "wse_units": [
                            "m",
                            "m",
                            "..."
                        ]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-46.100781, -15.940864],
                            "...",
                            [-46.122559, -15.875454]
                        ]
                    }
                }
            ]
        }
    }
}
```

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
                    "63470800171",
                    "..."
                ],
                "time_str": [
                    "2024-02-08T13:48:48Z",
                    "2024-02-12T00:49:59Z",
                    "..."
                ],
                "wse": [
                    "493.9646",
                    "495.8134",
                    "..."
                ],
                "wse_units": [
                    "m",
                    "m",
                    "..."
                ]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.100781, -15.940864],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        }
    ]
}
```

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
                "time_str": "2024-02-08T13:48:48Z",
                "wse": "493.9646",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.100781, -15.940864],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        },
        {
            "id": "1",
            "type": "Feature",
            "properties": {
                "reach_id": "63470800171",
                "time_str": "2024-02-12T00:49:59Z",
                "wse": "495.8134",
                "wse_units": "m"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.100781, -15.940864],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        }
    ]
}
```

### text/csv

When the `Accept` header is set to `text/csv` and there is no `output` request parameter, a CSV response is returned with Content-Type set to 'text/csv'.

Example CSV response:

```
"reach_id,time_str,wse,wse_units\n63470800171,2024-02-08T13:48:48Z,493.9646,m\n63470800171,2024-02-12T00:49:59Z,495.8134,m\n...\n"
```

### CSV File Download

When the `output` parameter is set to `csv_file`, the response triggers a file download in the browser. The response has `Content-Type: text/csv` and a `Content-Disposition: attachment; filename=...` header that causes the browser to prompt a Save As dialog.

Example request with default filename:

```bash
curl -OJ --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&output=csv_file&fields=reach_id,time_str,wse'
```

Downloads as: `hydrocron_Reach_63470800171_2024-02-01_2024-10-30.csv`

Example request with custom filename:

```bash
curl -OJ --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&output=csv_file&filename=my_analysis&fields=reach_id,time_str,wse'
```

Downloads as: `my_analysis.csv`

:::{tip} Opening CSV files in Excel
Excel reformats long numbers when it opens a CSV. For example, 14-digit `node_id` values show as `5.7203E+13` and the fill value `-999999999999.0` shows as `-1E+12`. The CSV file has the full values.

- To keep every value exactly as returned, import the file with Data → From Text/CSV and set the columns to **Text** — at least the ID columns (`node_id`, `reach_id`, `lake_id`) and any column with fill values.
- If you filter out missing data, check for the fill value `-999999999999.0` in the original CSV, not Excel's displayed `-1E+12`.
- Don't save the file back to CSV from Excel after values are reformatted, as the full values can be lost.
:::

(reach-and-node-responses)=
### Reach and node responses

When [](#node_fields) is present, every response format (JSON, GeoJSON, CSV, CSV file download) holds both the reach and its nodes:

- **Rows:** reach rows first, then node rows in `node_id` order. Each node's rows are in time order.
- **Added columns:** every row starts with `feature_type`, `reach_id` and `node_id` (node rows), even if not requested. `feature_type` is `Reach` or `Node` (the same values as the [](#feature) parameter).
- **Column order:** `feature_type`, `reach_id`, `node_id`, then the requested [](#fields), then any new fields from [](#node_fields), then units. A field in both lists appears once.
- **Fields that don't apply:**
  - **CSV** has one header for all rows, so a column that doesn't apply to a row's feature type is **empty** (e.g. `node_id` and `node_q` on the reach row, `slope` on node rows).
  - **GeoJSON:** each Feature has only its own feature type's properties. Reach Features have no `node_id` and no node-only fields; node Features have no reach-only fields.
  - A value that applies but is missing keeps the fill value `-999999999999.0`, as in other responses.
- **Units:** unit columns come from the rows returned. In CSV, if only the reach or only nodes have data, the other feature type's requested fields still appear (empty), but their unit columns may not.
- **Unobserved nodes** are included with `time_str` of `no_data` and fill values, the same as `feature=Node` requests.
- **Geometry:** GeoJSON always includes it — a LineString for the reach and a Point for each node. CSV includes it only if `geometry` is requested (in [](#fields) for reach rows, in [](#node_fields) for node rows).
- **Compact:** `compact=true` returns one Feature for the reach and one for each node, each with its values as lists.
- **`hits`:** the total number of reach and node rows, before compaction.
- If only the reach or only nodes have data in the time range, that data is returned. A 400 is returned only if neither has data.

Example CSV request (Version D reach `57203000041`, one pass):

```bash
curl --header "Accept: text/csv" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=57203000041&start_time=2026-04-01T00:00:00Z&end_time=2026-04-30T00:00:00Z&fields=reach_id,time_str,wse,slope&node_fields=node_id,time_str,wse,node_q'
```

```
feature_type,reach_id,node_id,time_str,wse,slope,node_q,wse_units,slope_units
Reach,57203000041,,2026-04-19T19:08:16Z,7.6096,0.00135545806,,m,m/m
Node,57203000041,57203000040011,no_data,-999999999999.0,,3,m,
...
Node,57203000041,57203000040201,2026-04-19T19:08:16Z,6.06841,,0,m,
...
```

The reach row has an empty `node_id` and `node_q`; node rows have an empty `slope` and `slope_units`. Node `57203000040011` was not observed on this pass, so it has `no_data` and fill values.

Example compact GeoJSON response for the same request with `Accept: application/geo+json` (2 of the 52 node Features shown):

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": "0",
            "type": "Feature",
            "properties": {
                "feature_type": ["Reach"],
                "reach_id": ["57203000041"],
                "time_str": ["2026-04-19T19:08:16Z"],
                "wse": ["7.6096"],
                "slope": ["0.00135545806"],
                "wse_units": ["m"],
                "slope_units": ["m/m"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[171.24103, -42.454014], [171.241175, -42.453743], "...", [171.341708, -42.437007]]
            }
        },
        {
            "id": "1",
            "type": "Feature",
            "properties": {
                "feature_type": ["Node"],
                "reach_id": ["57203000041"],
                "node_id": ["57203000040011"],
                "time_str": ["no_data"],
                "wse": ["-999999999999.0"],
                "node_q": ["3"],
                "wse_units": ["m"]
            },
            "geometry": {"type": "Point", "coordinates": [171.241318, -42.452933]}
        },
        "...",
        {
            "id": "20",
            "type": "Feature",
            "properties": {
                "feature_type": ["Node"],
                "reach_id": ["57203000041"],
                "node_id": ["57203000040201"],
                "time_str": ["2026-04-19T19:08:16Z"],
                "wse": ["6.06841"],
                "node_q": ["0"],
                "wse_units": ["m"]
            },
            "geometry": {"type": "Point", "coordinates": [171.280862, -42.452075]}
        },
        "..."
    ]
}
```

% TODO: example output is from local test data (one pass, April 2026); replace with production output once node_fields is released.

## Response Codes

| Code    | Reason                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200     | Request has succeeded and response has been returned to the user.                                                                                                           |
| 400*    | 'Bad Request': This indicates that the end user entered the parameters incorrectly in their query or time series data could not be located for the feature ID. The API attempts to send a response as to which parameter was incorrect. |
| 413     | 'Payload Too Large': The user attempted to retrieve a response that was too large. This is triggered for queries that exceed 6mb, and for [](#node_fields) requests where the reach has more than 25,000 node rows in the time range. |
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
    "x-hydrocron-key": "<podaac-provided-api-key>"
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
