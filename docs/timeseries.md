# timeseries

Retrieve time series data from SWOT observations for reaches and nodes.

## Request Parameters

### feature : string, required: yes

Type of feature being requested. Either: "Reach" or "Node"

### feature_id : string, required: yes

ID of the feature to retrieve

- Reaches have the format CBBBBBRRRRT (e.g., 78340600051)
- Nodes have the format CBBBBBRRRRNNNT (e.g., 12228200110861)

Please see the [SWOT Product Description Document for the L2_HR_RiverSP Dataset](https://podaac.jpl.nasa.gov/SWOT?tab=datasets-information&sections=about) for more information on identifiers.

### start_time : string, required: yes

Start time of the time series in the form of YYYY-MM-DDTHH:MM:SSZ (e.g., 2023-08-04T00:00:00Z)

The time can include a UTC offset which is specified in the form of &pm;HH:MM or &pm;HHMM so the entire time format can be: YYYY-MM-DDTHH:MM:SSZ&pm;HH:MM.

Please note you will need to encode offsets that use the `+` sign with `%2b` so that the parameters in the URL used to query the API passes the correct character to the API.

Example:

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2023-07-01T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### end_time : string, required: yes

End time of the time series in the form of YYYY-MM-DDTHH:MM:SSZ (e.g., 2023-08-04T00:00:00Z)

The time can include a UTC offset which is specified in the form of &pm;HH:MM or &pm;HHMM so the entire time format can be: YYYY-MM-DDTHH:MM:SSZ&pm;HH:MM.

Please note you will need to encode offsets that use the `+` sign with `%2b` so that the parameters in the URL used to query the API passes the correct character to the API.

Example:

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2023-07-01T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### output : string, required: yes

Format of the data returned. Either: "csv" or "geojson"

### fields : string, required: yes

The SWOT data fields to return in the request. 

This is specified in the form of a comma separated list (without any spaces): `fields=reach_id,time_str,wse,slope`

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
'crid', 'sword_version', 'collection_shortname',
'geometry'
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
'crid', 'sword_version', 'collection_shortname',
'geometry'
```

## Returns

CSV or GEOJSON file containing the data for the selected feature and time period.

## Response Codes

| Code    | Reason                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200     | Request has succeeded and response has been returned to the user.                                                                                                           |
| 400*    | 'Bad Request': This indicates that the end user entered the parameters incorrectly in their query or time series data could not be located for the feature ID. The API attempts to send a response as to which parameter was incorrect. |
| 413     | 'Payload Too Large': The user attempted to retrieve a response that was too large. This is triggered for queries that exceed 6mb.                                           |
| 500     | 'Internal Server Error': Internal API error.                                                                                                                                |

*The 400 code is also currently returned for queries where no time series data could be located for the request specified feature ID. The message returned with the response indicates this and it can be helpful to adjust the date ranges you are searching.
