# Examples

## Get time series GeoJSON for river reach

Search for a single river reach by reach ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return GeoJSON:

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

** geometry simplified for example

## Get time series CSV for river reach

Search for a single river reach by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope)

Will return CSV:

    {
        "status": "200 OK",
        "time": 850.25,
        "hits": 12,
        "results": {
            "csv": "reach_id,time_str,wse,slope,wse_units,slope_units\n78340600051,2024-01-30T09:38:22Z,386.1973,-0.0022161476,m,m/m\n78340600051,2024-02-03T18:33:48Z,386.404,-0.0021030676,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-02-13T16:56:05Z,386.4593,-0.0024754944,m,m/m\n78340600051,2024-02-20T06:23:27Z,407.3638,-0.0021535548,m,m/m\n78340600051,2024-02-24T15:18:54Z,385.9676,-0.001794102,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-05T13:41:09Z,385.6664,-0.0024497335,m,m/m\n78340600051,2024-03-12T03:08:30Z,408.4634,-0.0021388862,m,m/m\n78340600051,2024-03-16T12:03:56Z,386.5635,-0.0021972558,m,m/m\n78340600051,no_data,-999999999999.0,-999999999999.0,m,m/m\n78340600051,2024-03-26T10:26:13Z,386.2493,-0.0021548483,m,m/m\n",
            "geojson": {}
        }
    }

## Get time series GeoJSON for river node

Search for a single river node by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=12228200110861&start_time=2024-01-25T00:00:00Z&end_time=2024-03-30T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=12228200110861&start_time=2024-01-25T00:00:00Z&end_time=2024-03-30T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse)

Will return GeoJSON:

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

## Get time series CSV for river node

Search for a single river node by ID.

[https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=28311800020621&start_time=2024-01-25T00:00:00Z&end_time=2024-03-27T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Node&feature_id=28311800020621&start_time=2024-01-25T00:00:00Z&end_time=2024-03-27T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry)

Will return CSV:

    {
        "status": "200 OK",
        "time": 500.644,
        "hits": 11,
        "results": {
            "csv": "node_id,reach_id,time_str,wse,geometry,wse_units\n28311800020621,28311800021,2024-01-28T08:15:21Z,-15.54433,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-01-31T21:37:09Z,-15.63838,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-07T06:37:36Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-10T19:59:24Z,-14.46997,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-18T05:00:26Z,-15.99808,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-21T18:22:14Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-02-28T03:22:42Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-02T16:44:30Z,-16.80069,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-10T01:45:29Z,-15.65594,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-13T15:07:16Z,-999999999999.0,POINT (45.949474 48.354881),m\n28311800020621,28311800021,2024-03-23T13:29:33Z,-16.73133,POINT (45.949474 48.354881),m\n",
            "geojson": {}
        }
    }
