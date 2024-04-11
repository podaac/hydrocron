# Examples

## Get time series GeoJSON for river reach

Search for a single river reach by reach ID.

    /timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope

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

    timeseries?feature=Reach&feature_id=78340600051&output=csv&start_time=2024-01-25T00:00:00Z&end_time=2024-03-29T00:00:00Z&fields=reach_id,time_str,wse,slope

Will return CSV:

    {
        "status":"200 OK",
        "time":1698.409,
        "hits":10,
        "results":{
            "csv":"reach_id,time_str,wse,slope\n78340600051,2024-01-30T09:38:22Z,3089.5784,-0.0177291808\n78340600051,2024-02-03T18:33:48Z,1545.616,-0.0084122704\n78340600051,no_data,-999999999999.0,-999999999999.0\n78340600051,2024-02-13T16:56:05Z,2705.2151,-0.0173284608\n78340600051,2024-02-20T06:23:27Z,2851.5466,-0.0150748836\n78340600051,2024-02-24T15:18:54Z,2315.8056,-0.010764612\n78340600051,no_data,-999999999999.0,-999999999999.0\n78340600051,2024-03-05T13:41:09Z,2699.6648,-0.017148134500000002\n78340600051,2024-03-12T03:08:30Z,1225.3901999999998,-0.0064166586\n78340600051,no_data,-999999999999.0,-999999999999.0\n",
            "geojson":{}
        }
    }

## Get time series GeoJSON for river node

Search for a single river node by ID.

    timeseries?feature=Node&feature_id=12228200110861&start_time=2024-01-25T00:00:00Z&end_time=2024-03-30T00:00:00Z&output=geojson&fields=reach_id,node_id,time_str,wse'

Will return GeoJSON:

    {
        "status":"200 OK",
        "time":559.201,
        "hits":5,
        "results":{
            "csv":"",
            "geojson":{
                "type":"FeatureCollection",
                "features":[
                    {
                        "id":"0",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"12228200111",
                            "node_id":"12228200110861",
                            "time_str":"2024-01-30T21:19:19Z",
                            "wse":"5423.3856"
                        },
                        "geometry":{
                            "type":"Point",
                            "coordinates":[35.149314,-10.256285]
                        }
                    },
                    {
                        "id":"1",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"12228200111",
                            "node_id":"12228200110861",
                            "time_str":"2024-02-06T08:37:09Z",
                            "wse":"2020.4075400000002"
                        },
                        "geometry":{
                            "type":"Point",
                            "coordinates":[35.149314,-10.256285]
                        }
                    },
                    {
                        "id":"2",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"12228200111",
                            "node_id":"12228200110861",
                            "time_str":"2024-02-20T18:04:24Z",
                            "wse":"2021.09397"
                        },
                        "geometry":{
                            "type":"Point",
                            "coordinates":[35.149314,-10.256285]
                        }
                    },
                    {
                        "id":"3",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"12228200111",
                            "node_id":"12228200110861",
                            "time_str":"2024-03-12T14:49:26Z",
                            "wse":"5387.82304"
                        },
                        "geometry":{
                            "type":"Point",
                            "coordinates":[35.149314,-10.256285]
                        }
                    },
                    {
                        "id":"4",
                        "type":"Feature",
                        "properties":{
                            "reach_id":"12228200111",
                            "node_id":"12228200110861",
                            "time_str":"2024-03-19T02:07:17Z",
                            "wse":"6077.089709999999"
                        },
                        "geometry":{
                            "type":"Point",
                            "coordinates":[35.149314,-10.256285]
                        }
                    }
                ]
            }
        }
    }

## Get time series CSV for river node

Search for a single river node by ID.

    timeseries?feature=Node&feature_id=28311800020621&start_time=2024-01-25T00:00:00Z&end_time=2024-03-27T00:00:00Z&output=csv&fields=node_id,reach_id,time_str,wse,geometry

Will return CSV:

    {
        "status":"200 OK",
        "time":521.995,
        "hits":2,
        "results":{
            "csv":"node_id,reach_id,time_str,wse,geometry\n28311800020621,28311800021,2024-01-28T08:15:21Z,-77.72165,POINT (45.949474 48.354881)\n28311800020621,28311800021,2024-01-31T21:37:09Z,-78.1919,POINT (45.949474 48.354881)\n",
            "geojson":{}
            }
    }
