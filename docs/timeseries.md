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

### feature : string, required: yes

Type of feature being requested. Either: "Reach", "Node" or "PriorLake"

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

### fields : string, required: yes

The SWOT data fields to return in the request.

This is specified in the form of a comma separated list (without any spaces): `fields=reach_id,time_str,wse,slope`

Hydrocron includes additional fields beyond the source data shapefile attributes, including units fields on measurements, cycle and pass information, SWORD and PLD (prior river and lake database names), and collection versions. **NOTE: Units are always returned for fields that have corresponding units stored in Hydrocron, they do not need to be requested.** The complete list of input fields that are available through Hydrocron are below:

**Reach data fields**

```bash
'reach_id', 'time', 'time_tai', 'time_str', 'p_lat', 'p_lon', 'river_name',
'wse', 'wse_u', 'wse_r_u', 'wse_c', 'wse_c_u',
'slope', 'slope_u', 'slope_r_u', 'slope2', 'slope2_u', 'slope2_r_u',
'width', 'width_u', 'width_c', 'width_c_u',
'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
'd_x_area', 'd_x_area_u',
'layovr_val', 'node_dist', 'loc_offset', 'xtrk_dist',
'dschg_c', 'dschg_c_u', 'dschg_csf', 'dschg_c_q',
'dschg_gc', 'dschg_gc_u', 'dschg_gcsf', 'dschg_gc_q',
'dschg_m', 'dschg_m_u', 'dschg_msf', 'dschg_m_q',
'dschg_gm', 'dschg_gm_u', 'dschg_gmsf', 'dschg_gm_q',
'dschg_b', 'dschg_b_u', 'dschg_bsf', 'dschg_b_q',
'dschg_gb', 'dschg_gb_u', 'dschg_gbsf', 'dschg_gb_q',
'dschg_h', 'dschg_h_u', 'dschg_hsf', 'dschg_h_q',
'dschg_gh', 'dschg_gh_u', 'dschg_ghsf', 'dschg_gh_q',
'dschg_o', 'dschg_o_u', 'dschg_osf', 'dschg_o_q',
'dschg_go', 'dschg_go_u', 'dschg_gosf', 'dschg_go_q',
'dschg_s', 'dschg_s_u', 'dschg_ssf', 'dschg_s_q',
'dschg_gs', 'dschg_gs_u', 'dschg_gssf', 'dschg_gs_q',
'dschg_i', 'dschg_i_u', 'dschg_isf', 'dschg_i_q',
'dschg_gi', 'dschg_gi_u', 'dschg_gisf', 'dschg_gi_q',
'dschg_q_b', 'dschg_gq_b',
'reach_q', 'reach_q_b',
'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_nod',
'obs_frac_n', 'xovr_cal_q', 'geoid_hght', 'geoid_slop',
'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c',
'n_reach_up', 'n_reach_dn', 'rch_id_up', 'rch_id_dn',
'p_wse', 'p_wse_var', 'p_width', 'p_wid_var', 'p_n_nodes', 'p_dist_out',
'p_length', 'p_maf', 'p_dam_id', 'p_n_ch_max', 'p_n_ch_mod', 'p_low_slp',
'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
'granuleUR', 'ingest_time'
```

**Node data fields**

```bash
'reach_id', 'node_id', 'time', 'time_tai', 'time_str',
'lat', 'lon', 'lat_u', 'lon_u', 'river_name',
'wse', 'wse_u', 'wse_r_u',
'width', 'width_u',
'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
'layovr_val', 'node_dist', 'xtrk_dist',
'flow_angle', 'node_q', 'node_q_b',
'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_pix',
'xovr_cal_q', 'rdr_sig0', 'rdr_sig0_u', 'rdr_pol',
'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c',
'p_wse', 'p_wse_var', 'p_width', 'p_wid_var', 'p_dist_out', 'p_length',
'p_dam_id', 'p_n_ch_max', 'p_n_ch_mod',
'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
'crid', 'geometry', 'sword_version', 'collection_shortname'
```

**Lake data fields**
```bash
'lake_id', 'reach_id', 'obs_id', 'overlap', 'n_overlap',
'time', 'time_tai', 'time_str', 'wse', 'wse_u', 'wse_r_u', 'wse_std',
'area_total', 'area_tot_u', 'area_detct', 'area_det_u',
'layovr_val', 'xtrk_dist', 'ds1_l', 'ds1_l_u', 'ds1_q', 'ds1_q_u',
'ds2_l', 'ds2_l_u', 'ds2_q', 'ds2_q_u',
'quality_f', 'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f',
'xovr_cal_q', 'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c', 'lake_name', 'p_res_id',
'p_lon', 'p_lat', 'p_ref_wse', 'p_ref_area', 'p_date_t0', 'p_ds_t0', 'p_storage',
'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
'crid', 'geometry', 'PLD_version', 'collection_shortname', 'crid'
```

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

## API Keys [DRAFT]

> ⚠️
>API keys not yet implemented but coming soon! Content below is not finalized. More details to follow...

Users may request a special API key for cases where their intended usage of the API may be considered heavy or more complex. Heavy usage can be defined as continued used with over x requests per day or continue use which require many requests per second or concurrent requests. To request an API key or to discuss your use case, please contact us at x.

**Note: Users do *not* have to send an API key in their request to use the Hydrocron API. The API key is optional.**

### How to use an API key in requests [DRAFT]

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
