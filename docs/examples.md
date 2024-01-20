# Examples

## Get time series GeoJSON for river reach

Search for a single river reach by reach ID.

    /timeseries?feature=Reach&feature_id=73111000545&output=geojson&start_time=2023-06-04T00:00:00&end_time=2023-06-10T00:00:00&fields=feature_id,time_str,wse,geometry

Will return geojson, eg:

    {
    "status": "200 OK",
    "time": "65.691 ms.",
    "type": "FeatureCollection",
    "features": [
        {
        "properties": {
            "time": "2023-06-05 06:58:52",
            "reach_id": 73111000545,
            "wse": -23.9435,
            "slope": 0.000005225450000000001
        },
        "geometry": {
            "coordinates": [
            [
                -67.138008,
                45.134336
            ],
            [
                -67.140648,
                45.137619
            ],
            [
                -67.142347,
                45.141698
            ],
            [
                -67.144123,
                45.145777
            ],
            [
                -67.144469,
                45.146863
            ],
            [
                -67.146042,
                45.150129
            ],
            [
                -67.148479,
                45.15503
            ],
            [
                -67.149418,
                45.156665
            ],
            [
                -67.151297,
                45.159936
            ],
            [
                -67.153499,
                45.162672
            ],
            [
                -67.158077,
                45.162746
            ],
            [
                -67.16379,
                45.163162
            ],
            [
                -67.17678,
                45.162777
            ],
            [
                -67.18513,
                45.164314
            ],
            [
                -67.188161,
                45.16501
            ],
            [
                -67.191202,
                45.165436
            ],
            [
                -67.194232,
                45.166186
            ],
            [
                -67.197255,
                45.167152
            ]
            ],
            "type": "LineString"
        },
        "type": "Feature"
        }
    ],
    "hits": 1
    }

** geometry simplified for example
