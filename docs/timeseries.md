# timeseries

Get time series data from SWOT observations for reaches and nodes

## Parameters

feature : string  
    Type of feature being requested. Either "Reach" or "Node"

feature_id : string  
    ID of the feature to retrieve in format CBBTTTSNNNNNN (i.e. 74297700000000)  

start_time : string  
    Start time of the timeseries  (i.e 2023-08-04T00:00:00Z)

end_time : string  
    End time of the timeseries

output : string  
    Format of the data returned. Must be one of ["csv", "geojson"]

fields : string  
    The fields to return. Defaults to "feature_id, time_str, wse, geometry"

## Returns

CSV or GEOJSON file containing the data for the selected feature and time period.

## Responses

200 : OK

400 : The specified URL is invalid (does not exist)

404 : An entry with the specified region was not found

413 : Your query returns too much data
