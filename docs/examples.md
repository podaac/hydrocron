# Examples

## Get time series GeoJSON for river reach

Search for a single river reach by reach ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return GeoJSON:

```json
{
    "status":"200 OK",
    "time":844.614,
    "hits":10,
    "results":{
        "csv":"",
        "geojson":{
            "type":"FeatureCollection",
            "features":[
                {
                    "id":"0",
                    "type":"Feature",
                    "properties":{
                        "reach_id":"78340600051",
                        "time_str":"2024-01-30T09:38:22Z",
                        "wse":"3089.5784",
                        "slope":"-0.0177291808"
                    },
                    "geometry":{
                        "type":"LineString",
                        "coordinates":[
                            [-127.285739,54.942484],
                            [-127.286202,54.942598],
                            [-127.286664,54.942767],
                            [-127.287029,54.942988],
                            [-127.330039,54.99239]
                        ]
                    }
                },
                {
                    "id":"1",
                    "type":"Feature",
                    "properties":{
                        "reach_id":"78340600051",
                        "time_str":"2024-02-03T18:33:48Z",
                        "wse":"1545.616","slope":"-0.0084122704"},
                        "geometry":{
                            "type":"LineString",
                            "coordinates":[
                                [-127.285739,54.942484],
                                [-127.286202,54.942598],
                                [-127.286664,54.942767],
                                [-127.287029,54.942988],
                                [-127.330039,54.99239]
                            ]
                        }
                    },
                    {
                        "id":"5",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"78340600051",
                            "time_str":"2024-02-24T15:18:54Z",
                            "wse":"2315.8056",
                            "slope":"-0.010764612"
                        },
                        "geometry":{
                            "type":"LineString",
                            "coordinates":[
                                [-127.285739,54.942484],
                                [-127.286202,54.942598],
                                [-127.286664,54.942767],
                                [-127.287029,54.942988],
                                [-127.330039,54.99239]
                            ]
                        }
                    }
                ]
            }
        }
}
```

** geometry simplified for example

## Get time series GeoJSON for river node

Search for a single river node by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=12228200110861&start_time=2024-01-25T00:00:00Z&end_time=2024-03-30T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=12228200110861&start_time=2024-01-25T00:00:00Z&end_time=2024-03-30T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse)

Will return GeoJSON:

```json
{
"status": "200 OK",
"time": 604.705,
"hits": 9,
"results": {
    "csv": "",
    "geojson": {
        "type": "FeatureCollection",
        "features": [
            {
            "id": "0",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-01-30T21:19:19Z",
                "wse": "677.9232",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "1",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-02-06T08:37:09Z",
                "wse": "673.46918",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "2",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "no_data",
                "wse": "-999999999999.0",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "3",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-02-20T18:04:24Z",
                "wse": "673.69799",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "4",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-02-27T05:22:15Z",
                "wse": "674.66235",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "5",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "no_data",
                "wse": "-999999999999.0",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "6",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-03-12T14:49:26Z",
                "wse": "673.47788",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "7",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "2024-03-19T02:07:17Z",
                "wse": "675.23219",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
                ]
            }
            },
            {
            "id": "8",
            "type": "Feature",
            "properties": {
                "reach_id": "12228200111",
                "node_id": "12228200110861",
                "time_str": "no_data",
                "wse": "-999999999999.0",
                "wse_units": "m"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                35.149314,
                -10.256285
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
    "time": 391.613,
    "hits": 1,
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
                        "time_str": "2024-07-25T22:48:23Z",
                        "wse": "260.802",
                        "area_total": "0.553409",
                        "quality_f": "1",
                        "collection_shortname": "SWOT_L2_HR_LakeSP_2.0",
                        "crid": "PIC0",
                        "PLD_version": "105",
                        "range_start_time": "2024-07-25T22:47:27Z",
                        "wse_units": "m",
                        "area_total_units": "km^2"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -42.590727027987064,
                            -19.822613018107482
                        ]
                    }
                }
            ]
        }
    }
}
```

**NOTE:** Due to the size of the original polygon in the lake (L2_HR_LakeSP) shapefiles, we are only returning the calculated center point of the lake. This is to facilitate conformance with the GeoJSON specification and center points should not be considered accurate.

## Get time series CSV for river reach

Search for a single river reach by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 850.25,
    "hits": 12,
    "results": {
        "csv": "reach_id,time_str,wse,slope,wse_units,slope_units\n78340600051,2024-01-30T09:38:22Z,386.1973,-0.0022161476,m,m/m\n78340600051,2024-02-03T18:33:48Z,386.404,-0.0021030676,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-02-13T16:56:05Z,386.4593,-0.0024754944,m,m/m\n78340600051,2024-02-20T06:23:27Z,407.3638,-0.0021535548,m,m/m\n78340600051,2024-02-24T15:18:54Z,385.9676,-0.001794102,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-05T13:41:09Z,385.6664,-0.0024497335,m,m/m\n78340600051,2024-03-12T03:08:30Z,408.4634,-0.0021388862,m,m/m\n78340600051,2024-03-16T12:03:56Z,386.5635,-0.0021972558,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-26T10:26:13Z,386.2493,-0.0021548483,m,m/m\n",
        "geojson": {}
    }
}
```

## Get time series CSV for river node

Search for a single river node by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=28311800020621&start_time=2024-01-25T00:00:00Z&end_time=2024-03-27T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=28311800020621&start_time=2024-01-25T00:00:00Z&end_time=2024-03-27T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry)

Will return CSV:

```json
{
    "status": "200 OK",
    "time": 500.644,
    "hits": 11,
    "results": {
        "csv": "node_id,reach_id,time_str,wse,geometry,wse_units\n28311800020621,28311800021,2024-01-28T08:15:21Z,-15.54433,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-01-31T21:37:09Z,-15.63838,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-07T06:37:36Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-10T19:59:24Z,-14.46997,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-18T05:00:26Z,-15.99808,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-21T18:22:14Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-28T03:22:42Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-02T16:44:30Z,-16.80069,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-10T01:45:29Z,-15.65594,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-13T15:07:16Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-23T13:29:33Z,-16.73133,POINT (45.949474 48.354881),m\n",
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
    "time": 321.592,
    "hits": 1,
    "results": {
        "csv": "lake_id,time_str,wse,area_total,quality_f,collection_shortname,crid,PLD_version,range_start_time,wse_units,area_total_units\n6350036102,2024-07-25T22:48:23Z,260.802,0.553409,1,SWOT_L2_HR_LakeSP_2.0,PIC0,105,2024-07-25T22:47:27Z,m,km^2\n",
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

** Note the output query parameter is not specified in the request.

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
                "width": [
                    "383.19271200000003",
                    "501.616464"
                ],
                "wse_units": [
                    "m",
                    "m"
                ],
                "width_units": [
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

** geometry simplified for example

### Get time series for text/csv Accept Header

```bash
curl --header "Accept: text/csv" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

** Note the output query parameter is not specified in the request.

Will return a CSV response:

```json
"reach_id,time_str,wse,width,wse_units,width_units\n63470800171,2024-02-01T02:26:50Z,3386.9332,383.19271200000003,m,m\n63470800171,2024-02-08T13:48:41Z,1453.4136,501.616464,m,m\n"
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

** geometry simplified for example

### Get time series for application/geo+json

```bash
curl -v --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse'
```

** Note compacted response returned by default as no compact query parameter is specified.

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

** geometry simplified for example

### Get time series for application/geo+json with compact=False

```bash
curl --header "Accept: application/geo+json" --location 'https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=63470800171&start_time=2024-02-01T00:00:00%2b00:00&end_time=2024-10-30T00:00:00%2b00:00&fields=reach_id,time_str,wse&compact=false'
```

** Note compact query parameter is specified.

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
```

** geometry simplified for example
