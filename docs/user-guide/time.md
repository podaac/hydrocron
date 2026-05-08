# Observed Time vs Range Time

SWOT source data is organized to include all of the features from the prior river and lake databases that the satellite crosses over during each pass of a continent.
If for any reason SWOT does not record an observation of a prior database feature during a pass, the source data will contain fill values for all observed fields, including the time of observation.

To retain times where there was a satellite pass but no observation was made, Hydrocron queries on the *start time of the range of observations included in the pass over the continent during the cycle of interest*. For example, if it takes 10 seconds for the satellite to pass over North America, 3 different river reaches observed during that pass may have an observation time recorded at 2 seconds, 5 seconds, and 9 seconds. However, Hydrocron uses the range start time of 0 seconds (the beginning of the 10 second window for the pass over the continent) as the start time, and the range end time of 9 seconds as the end time when querying for data.

## Example

| reach_id    |  time               | range_start_time    | range_end_time      | wse              |
|-------------|---------------------|---------------------|---------------------|------------------|
| 72558200021 | 2024-01-18T18:28:58Z|2024-01-18T18:25:07Z |2024-01-18T18:36:12Z | 177.4408         |
| 72558200021 | no_data             |2024-01-21T07:38:51Z |2024-01-21T07:53:21Z | -999999999999.0  |
| 72558200021 | 2024-01-31T06:10:05Z|2024-01-31T06:01:05Z |2024-01-31T06:15:32Z | 177.3027         |

In this example, querying Hydrocron using a start_time of 2024-01-18T00:00:00Z and an end_time of 2024-02-01T00:00:00Z will return all three features, because it is the pass start time that is used in the query. The returned data will include the actual observation time, including the no_data value for the feature that was not observed.

:::{tip}
Try this query yourself:

[`GET /timeseries?feature=Reach&feature_id=72558200021&start_time=2024-01-18T00:00:00Z&end_time=2024-02-01T00:00:00Z&output=csv&fields=reach_id,time_str,range_start_time,range_end_time,wse`](https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=Reach&feature_id=72558200021&start_time=2024-01-18T00%3A00%3A00Z&end_time=2024-02-01T00%3A00%3A00Z&output=csv&fields=reach_id,time_str,range_start_time,range_end_time,wse)
:::
