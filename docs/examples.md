# Examples

## Get time series GeoJSON for river reach

Search for a single river reach by reach ID:

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return GeoJSON:

```json
{
    "status": "200 OK",
    "time": 843.578,
    "hits": 10,
    "results": {
        "csv": "",
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "78340600051",
                        "time_str": "2024-02-03T18:34:05Z",
                        "wse": "386.9557",
                        "slope": "-0.0019823218",
                        "wse_units": "m",
                        "slope_units": "m/m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-127.330039, 54.99239],
                            [-127.32957, 54.992383],
                            "...",
                            [-127.285739, 54.942484]
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "78340600051",
                        "time_str": "2024-02-09T08:00:46Z",
                        "wse": "-999999999999.0",
                        "slope": "-999999999999.0",
                        "wse_units": "m",
                        "slope_units": "m/m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-127.330039, 54.99239],
                            [-127.32957, 54.992383],
                            "...",
                            [-127.285739, 54.942484]
                        ]
                    }
                },
                {
                    "id": "2",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "78340600051",
                        "time_str": "2024-02-20T06:23:40Z",
                        "wse": "386.5979",
                        "slope": "-0.0021285298",
                        "wse_units": "m",
                        "slope_units": "m/m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-127.330039, 54.99239],
                            [-127.32957, 54.992383],
                            "...",
                            [-127.285739, 54.942484]
                        ]
                    }
                }
            ]
        }
    }
}
```

**Note:** Geometry coordinates simplified for this example (329 total coordinates per feature).

## Get time series GeoJSON for river node

Search for a single river node by ID:

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=44404000150591&start_time=2024-01-02T00:00:00Z&end_time=2024-02-10T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=44404000150591&start_time=2024-01-02T00:00:00Z&end_time=2024-02-10T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse)

Will return GeoJSON:

```json
{
    "status": "200 OK",
    "time": 482.824,
    "hits": 4,
    "results": {
        "csv": "",
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "44404000151",
                        "node_id": "44404000150591",
                        "time_str": "2024-01-09T08:18:57Z",
                        "wse": "24.89255",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            102.543408,
                            3.40867
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "44404000151",
                        "node_id": "44404000150591",
                        "time_str": "2024-01-14T19:32:23Z",
                        "wse": "22.06794",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            102.543408,
                            3.40867
                        ]
                    }
                },
                {
                    "id": "2",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "44404000151",
                        "node_id": "44404000150591",
                        "time_str": "2024-01-30T05:04:03Z",
                        "wse": "23.0522",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            102.543408,
                            3.40867
                        ]
                    }
                },
                {
                    "id": "3",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "44404000151",
                        "node_id": "44404000150591",
                        "time_str": "2024-02-04T16:17:29Z",
                        "wse": "21.68793",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            102.543408,
                            3.40867
                        ]
                    }
                }
            ]
        }
    }
}
```

## Get time series GeoJSON for a lake

Search for a single lake by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=PriorLake&feature_id=6350036102&start_time=2024-07-20T00:00:00Z&end_time=2024-07-26T00:00:00Z&fields=lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time&output=geojson](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=PriorLake&feature_id=6350036102&start_time=2024-07-20T00:00:00Z&end_time=2024-07-26T00:00:00Z&fields=lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time&output=geojson)

Will return GeoJSON:

```json
{
    "status": "200 OK",
    "time": 410.161,
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
                        "lake_id": "6350036102",
                        "time_str": "2024-07-23T11:50:03Z",
                        "wse": "260.893",
                        "area_total": "0.483733",
                        "quality_f": "1",
                        "collection_shortname": "SWOT_L2_HR_LakeSP_D",
                        "crid": "PGD0",
                        "PLD_version": "202",
                        "range_start_time": "2024-07-23T11:44:34Z",
                        "wse_units": "m",
                        "area_total_units": "km^2"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -42.592754,
                            -19.822244
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "lake_id": "6350036102",
                        "time_str": "2024-07-25T22:48:23Z",
                        "wse": "260.803",
                        "area_total": "0.470057",
                        "quality_f": "1",
                        "collection_shortname": "SWOT_L2_HR_LakeSP_D",
                        "crid": "PGD0",
                        "PLD_version": "202",
                        "range_start_time": "2024-07-25T22:47:27Z",
                        "wse_units": "m",
                        "area_total_units": "km^2"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -42.591732,
                            -19.822285
                        ]
                    }
                }
            ]
        }
    }
}
```

**NOTE:** Due to the size of the original polygon in the lake (L2_HR_LakeSP) shapefiles, we are only returning the calculated center point of the lake. This is to facilitate conformance with the GeoJSON specification and center points should not be considered accurate.

## Get time series GeoJSON for river reach with discharge

Search for a single river reach by reach ID, requesting the SoS discharge fields. Discharge fields are only available for the version 2.0 river collection, so `collection_name=SWOT_L2_HR_RiverSP_2.0` is specified.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Reach&feature_id=18180900091&start_time=2025-04-01T00:00:00%2b00:00&end_time=2025-10-30T00:00:00%2b00:00&output=geojson&fields=reach_id,time_str,wse,sos_consensus_q,sos_hivdi_q,sos_metroman_q,sos_momma_q,sos_sad_q,sos_sic4dvar_q,sos_lakeflow_q,swot_discharge_reanalysis](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Reach&feature_id=18180900091&start_time=2025-04-01T00:00:00%2b00:00&end_time=2025-10-30T00:00:00%2b00:00&output=geojson&fields=reach_id,time_str,wse,sos_consensus_q,sos_hivdi_q,sos_metroman_q,sos_momma_q,sos_sad_q,sos_sic4dvar_q,sos_lakeflow_q,swot_discharge_reanalysis)

Will return GeoJSON:

```json
{
    "status": "200 OK",
    "time": 599.437,
    "hits": 3,
    "results": {
        "csv": "",
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "18180900091",
                        "time_str": "2025-04-08T01:01:01Z",
                        "wse": "1014.2303",
                        "sos_consensus_q": "72.91022466338953",
                        "sos_hivdi_q": "-999999999999.0",
                        "sos_metroman_q": "-999999999999.0",
                        "sos_momma_q": "-999999999999.0",
                        "sos_sad_q": "-999999999999.0",
                        "sos_sic4dvar_q": "72.91022466338953",
                        "sos_lakeflow_q": "-999999999999.0",
                        "swot_discharge_reanalysis": "72.91022466338953",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [46.935083, -18.315388],
                            [46.935312, -18.315548],
                            "...",
                            [46.927729, -18.384032]
                        ]
                    }
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "18180900091",
                        "time_str": "2025-04-15T12:24:12Z",
                        "wse": "1029.1983",
                        "sos_consensus_q": "1060.3418312796152",
                        "sos_hivdi_q": "-999999999999.0",
                        "sos_metroman_q": "-999999999999.0",
                        "sos_momma_q": "-999999999999.0",
                        "sos_sad_q": "-999999999999.0",
                        "sos_sic4dvar_q": "1060.3418312796152",
                        "sos_lakeflow_q": "-999999999999.0",
                        "swot_discharge_reanalysis": "1060.3418312796152",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [46.935083, -18.315388],
                            [46.935312, -18.315548],
                            "...",
                            [46.927729, -18.384032]
                        ]
                    }
                },
                {
                    "id": "2",
                    "type": "Feature",
                    "properties": {
                        "reach_id": "18180900091",
                        "time_str": "2025-04-28T21:46:06Z",
                        "wse": "1014.1341",
                        "sos_consensus_q": "179.12798112357618",
                        "sos_hivdi_q": "-999999999999.0",
                        "sos_metroman_q": "295.7076800569933",
                        "sos_momma_q": "139.43628483322104",
                        "sos_sad_q": "-999999999999.0",
                        "sos_sic4dvar_q": "62.548282190159064",
                        "sos_lakeflow_q": "-999999999999.0",
                        "swot_discharge_reanalysis": "179.12798112357618",
                        "wse_units": "m"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [46.935083, -18.315388],
                            [46.935312, -18.315548],
                            "...",
                            [46.927729, -18.384032]
                        ]
                    }
                }
            ]
        }
    }
}
```

**Note:** Geometry coordinates simplified for this example (284 total coordinates per feature).

## Get time series CSV for river reach with discharge

Search for a single river reach by reach ID, requesting the SoS discharge fields in CSV format. As with the GeoJSON example, `collection_name=SWOT_L2_HR_RiverSP_2.0` is specified since discharge fields are only available for the version 2.0 river collection.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Reach&feature_id=18180900091&start_time=2025-04-01T00:00:00%2b00:00&end_time=2025-10-30T00:00:00%2b00:00&output=csv&fields=reach_id,time_str,wse,sos_consensus_q,sos_hivdi_q,sos_metroman_q,sos_momma_q,sos_sad_q,sos_sic4dvar_q,sos_lakeflow_q,swot_discharge_reanalysis](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?collection_name=SWOT_L2_HR_RiverSP_2.0&feature=Reach&feature_id=18180900091&start_time=2025-04-01T00:00:00%2b00:00&end_time=2025-10-30T00:00:00%2b00:00&output=csv&fields=reach_id,time_str,wse,sos_consensus_q,sos_hivdi_q,sos_metroman_q,sos_momma_q,sos_sad_q,sos_sic4dvar_q,sos_lakeflow_q,swot_discharge_reanalysis)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 564.74,
    "hits": 3,
    "results": {
        "csv": "reach_id,time_str,wse,sos_consensus_q,sos_hivdi_q,sos_metroman_q,sos_momma_q,sos_sad_q,sos_sic4dvar_q,sos_lakeflow_q,swot_discharge_reanalysis,wse_units\n18180900091,2025-04-08T01:01:01Z,1014.2303,72.91022466338953,-999999999999.0,-999999999999.0,-999999999999.0,-999999999999.0,72.91022466338953,-999999999999.0,72.91022466338953,m\n18180900091,2025-04-15T12:24:12Z,1029.1983,1060.3418312796152,-999999999999.0,-999999999999.0,-999999999999.0,-999999999999.0,1060.3418312796152,-999999999999.0,1060.3418312796152,m\n18180900091,2025-04-28T21:46:06Z,1014.1341,179.12798112357618,-999999999999.0,295.7076800569933,139.43628483322104,-999999999999.0,62.548282190159064,-999999999999.0,179.12798112357618,m\n",
        "geojson": {}
    }
}
```

## Get time series CSV for river reach

Search for a single river reach by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 697.498,
    "hits": 10,
    "results": {
        "csv": "reach_id,time_str,wse,slope,wse_units,slope_units\n78340600051,2024-02-03T18:34:05Z,386.9557,-0.0019823218,m,m/m\n78340600051,2024-02-09T08:00:46Z,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-02-20T06:23:40Z,386.5979,-0.0021285298,m,m/m\n78340600051,2024-02-24T15:19:10Z,386.6074,-0.00197282,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-05T13:41:22Z,387.0104,-0.0020154178,m,m/m\n78340600051,2024-03-12T03:08:43Z,386.5742,-0.0021428208,m,m/m\n78340600051,2024-03-16T12:04:12Z,386.5983,-0.0019235693,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-26T10:26:26Z,386.3501,-0.0021486242,m,m/m\n",
        "geojson": {}
    }
}
```

## Get time series CSV for river node

Search for a single river node by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=44404000150591&start_time=2024-01-02T00:00:00Z&end_time=2024-02-10T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=44404000150591&start_time=2024-01-02T00:00:00Z&end_time=2024-02-10T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 806.167,
    "hits": 4,
    "results": {
        "csv": "node_id,reach_id,time_str,wse,geometry,wse_units\n44404000150591,44404000151,2024-01-09T08:18:57Z,24.89255,POINT (102.543408 3.40867),m\n44404000150591,44404000151,2024-01-14T19:32:23Z,22.06794,POINT (102.543408 3.40867),m\n44404000150591,44404000151,2024-01-30T05:04:03Z,23.0522,POINT (102.543408 3.40867),m\n44404000150591,44404000151,2024-02-04T16:17:29Z,21.68793,POINT (102.543408 3.40867),m\n",
        "geojson": {}
    }
}
```

## Get time series CSV for lake

Search for a single lake by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=PriorLake&feature_id=6350036102&start_time=2024-07-20T00:00:00Z&end_time=2024-07-26T00:00:00Z&fields=lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time&output=csv](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=PriorLake&feature_id=6350036102&start_time=2024-07-20T00:00:00Z&end_time=2024-07-26T00:00:00Z&fields=lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time&output=csv)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 325.231,
    "hits": 2,
    "results": {
        "csv": "lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time,wse_units,area_total_units\n6350036102,2024-07-23T11:50:03Z,260.893,0.483733,1,SWOT_L2_HR_LakeSP_D,PGD0,202,2024-07-23T11:44:34Z,m,km^2\n6350036102,2024-07-25T22:48:23Z,260.803,0.470057,1,SWOT_L2_HR_LakeSP_D,PGD0,202,2024-07-25T22:47:27Z,m,km^2\n",
        "geojson": {}
    }
}
```

## Accept headers

See the [documentation on the timeseries endpoint](timeseries.md) for an explanation of Accept headers.

### Get time series for application/geo+json Accept Header

```bash
curl --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

**Note:** The output query parameter is not specified in the request.

Will return GeoJSON response:

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
                    "63470800171",
                    "..."
                ],
                "time_str": [
                    "2024-02-08T13:48:48Z",
                    "2024-02-12T00:49:59Z",
                    "2024-02-29T10:33:53Z",
                    "..."
                ],
                "wse": [
                    "493.9646",
                    "495.8134",
                    "489.3664",
                    "..."
                ],
                "wse_units": [
                    "m",
                    "m",
                    "m",
                    "..."
                ]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.100781, -15.940864],
                    [-46.101059, -15.940592],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        }
    ]
}
```

**Note:** Response truncated — 25 observations and 295 coordinates in full response.

### Get time series for text/csv Accept Header

```bash
curl --header "Accept: text/csv" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

**Note:** The output query parameter is not specified in the request.

Will return a CSV response:

```
"reach_id,time_str,wse,wse_units\n63470800171,2024-02-08T13:48:48Z,493.9646,m\n63470800171,2024-02-12T00:49:59Z,495.8134,m\n63470800171,2024-02-29T10:33:53Z,489.3664,m\n...\n"
```

## Compact request

### Get time series for application/json with compact=True

```bash
curl --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse&compact=true'
```

Will return a compacted JSON response with metadata:

```json
{
    "status": "200 OK",
    "time": 737.056,
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
                            "63470800171",
                            "..."
                        ],
                        "time_str": [
                            "2024-02-08T13:48:48Z",
                            "2024-02-12T00:49:59Z",
                            "2024-02-29T10:33:53Z",
                            "..."
                        ],
                        "wse": [
                            "493.9646",
                            "495.8134",
                            "489.3664",
                            "..."
                        ],
                        "wse_units": [
                            "m",
                            "m",
                            "m",
                            "..."
                        ]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-46.100781, -15.940864],
                            [-46.101059, -15.940592],
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

**Note:** Response truncated — 25 observations and 295 coordinates in full response.

### Get time series for application/geo+json

```bash
curl -v --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

**Note:** Compacted response returned by default as no compact query parameter is specified.

Will return compacted GeoJSON response:

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
                    "63470800171",
                    "..."
                ],
                "time_str": [
                    "2024-02-08T13:48:48Z",
                    "2024-02-12T00:49:59Z",
                    "2024-02-29T10:33:53Z",
                    "..."
                ],
                "wse": [
                    "493.9646",
                    "495.8134",
                    "489.3664",
                    "..."
                ],
                "wse_units": [
                    "m",
                    "m",
                    "m",
                    "..."
                ]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.100781, -15.940864],
                    [-46.101059, -15.940592],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        }
    ]
}
```

**Note:** Response truncated — 25 observations and 295 coordinates in full response.

### Get time series for application/geo+json with compact=False

```bash
curl --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse&compact=false'
```

**Note:** The compact query parameter is specified.

Will return a GeoJSON response that is not compacted:

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
                    [-46.101059, -15.940592],
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
                    [-46.101059, -15.940592],
                    "...",
                    [-46.122559, -15.875454]
                ]
            }
        }
    ]
}
```

**Note:** Response truncated — 25 features and 295 coordinates per feature in full response.
