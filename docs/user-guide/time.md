# Observed Time vs Range Time

SWOT source data is organized to include all of the features from the prior river and lake databases that the satellite crosses over during each pass of a continent.
If for any reason SWOT does not record an observation of a prior database feature during a pass, the source data will contain fill values for all observed fields, including the time of observation.

To retain times where there was a satellite pass but no observation was made, Hydrocron queries on the *start time of the range of observations included in the pass over the continent during the cycle of interest*. For example, if it takes 10 seconds for the satellite to pass over North America, 3 different river reaches observed during that pass may have an observation time recorded at 2 seconds, 5 seconds, and 9 seconds. However, Hydrocron uses the range start time of 0 seconds (the beginning of the 10 second window for the pass over the continent) as the start time, and the range end time of 9 seconds as the end time when querying for data.

## Example

| reach_id    |  time               | range_start_time    | range_end_time      | wse           | ... |
|-------------|---------------------|---------------------|---------------------|---------------|-----|
| 71224100223 | 2023-08-01T12:30:45 |2023-08-01T12:30:30  |2023-08-01T12:40:30  | 316.8713      |     |
| 71224100223 | no_data             |2023-09-01T12:30:30  |2023-09-01T12:40:30  | -99999999.0000|     |
| 71224100223 | 2023-10-01T12:30:42 |2023-10-01T12:30:30  |2023-10-01T12:40:30  | 286.2983      |     |

In this simplified example, querying Hydrocron using a start_time of 2023-08-01T12:30:00 and an end_time of 2023-10-01T13:00:00 will return all three features, becasue it is the pass start time that is used in the query. The returned data will include the actual observation time, including the no_data value for the feature that was not observed.
