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

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### end_time : string, required: yes

End time of the time series in the form of YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-01-25T00:00:00Z)

The time can include a UTC offset which is specified in the form of &pm;HH:MM or &pm;HHMM so the entire time format can be: YYYY-MM-DDTHH:MM:SSZ&pm;HH:MM.

Please note you will need to encode offsets that use the `+` sign with `%2b` so that the parameters in the URL used to query the API passes the correct character to the API.

Example:

`/timeseries?feature=Reach&feature_id=78340600051&output=geojson&start_time=2024-01-25T00:00:00%2b00:00&end_time=2024-03-29T00:00:00%2b00:00&fields=reach_id,time_str,wse,slope`

### output : string, required: yes

Format of the data returned. Either: "csv" or "geojson"

### fields : string, required: yes

The SWOT data fields to return in the request.

This is specified in the form of a comma separated list (without any spaces): `fields=reach_id,time_str,wse,slope`

Hydrocron includes additional fields beyond the source data shapefile attributes, including units fields on measurements, cycle and pass information, and SWORD and collection versions. The complete list of fields that are available through Hydrocron are below:

**Reach data fields**

```bash
'reach_id', 'time', 'time_units', 'time_tai', 'time_tai_units', 'time_str', 'p_lat', 'p_lat_units', 'p_lon', 'p_lon_units', 'river_name',
'wse', 'wse_units', 'wse_u', 'wse_u_units', 'wse_r_u', 'wse_r_u_units', 'wse_c', 'wse_c_units', 'wse_c_u', 'wse_c_u_units',
'slope', 'slope_units', 'slope_u_units', 'slope_u', 'slope_r_u', 'slope_r_u_units', 
'slope2', 'slope2_units', 'slope2_u', 'slope2_u_units', 'slope2_r_u', 'slope2_r_u_units', 
'width', 'width_units', 'width_u', 'width_u_units', 'width_c', 'width_c_units', 'width_c_u', 'width_c_u_units', 
'area_total', 'area_tot_u', 'area_det_u_units', 'area_detct', 'area_det_u_units', 'area_det_u', area_det_u_units, 'area_wse', 'area_det_u_units',
'd_x_area', 'd_x_area_u', 'area_det_u_units'
'layovr_val', 'layovr_val_units', 'node_dist', 'node_dist_units', 'loc_offset', 'loc_offset_units', 'xtrk_dist', 'xtrk_dist_units'
'dschg_c', 'dschg_c_units', 'dschg_c_u', 'dschg_c_u_units', 'dschg_csf', 'dschg_csf_units', 'dschg_c_q',
'dschg_gc', 'dschg_gc_units', 'dschg_gc_u', 'dschg_gc_u_units', 'dschg_gcsf', 'dschg_gcsf_units', 'dschg_gc_q',
'dschg_m', 'dschg_m_units', 'dschg_m_u', 'dschg_m_u_units', 'dschg_msf', 'dschg_msf_units', 'dschg_m_q',
'dschg_gm', 'dschg_gm_units', 'dschg_gm_u', 'dschg_gm_u_units', 'dschg_gmsf', 'dschg_gmsf_units', 'dschg_gm_q',
'dschg_b', 'dschg_b_units', 'dschg_b_u', 'dschg_b_u_units', 'dschg_bsf', 'dschg_bsf_units', 'dschg_b_q',
'dschg_gb', 'dschg_gb_units', 'dschg_gb_u', 'dschg_gb_u_units', 'dschg_gbsf', 'dschg_gbsf_units', 'dschg_gb_q',
'dschg_h', 'dschg_h_units', 'dschg_h_u', 'dschg_h_u_units', 'dschg_hsf', 'dschg_hsf_units', 'dschg_h_q',
'dschg_gh', 'dschg_gh_units', 'dschg_gh_u', 'dschg_gh_u_units', 'dschg_ghsf', 'dschg_ghsf_units', 'dschg_gh_q',
'dschg_o', 'dschg_o_units', 'dschg_o_u', 'dschg_o_u_units', 'dschg_osf', 'dschg_osf_units', 'dschg_o_q',
'dschg_go', 'dschg_go_units', 'dschg_go_u', 'dschg_go_u_units', 'dschg_gosf', 'dschg_gosf_units', 'dschg_go_q',
'dschg_s', 'dschg_s_units', 'dschg_s_u', 'dschg_s_u_units', 'dschg_ssf', 'dschg_ssf_units', 'dschg_s_q',
'dschg_gs', 'dschg_gs_units', 'dschg_gs_u', 'dschg_gs_u_units', 'dschg_gssf', 'dschg_gssf_units', 'dschg_gs_q',
'dschg_i', 'dschg_i_units', 'dschg_i_u', 'dschg_i_u_units', 'dschg_isf', 'dschg_isf_units', 'dschg_i_q',
'dschg_gi', 'dschg_gi_units', 'dschg_gi_u', 'dschg_gi_u_units', 'dschg_gisf', 'dschg_gisf_units', 'dschg_gi_q',
'dschg_q_b', 'dschg_gq_b',
'reach_q', 'reach_q_b',
'dark_frac', 'dark_frac_units', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_nod', 'n_good_nod_units', 
'obs_frac_n', 'obs_frac_n_units', 'xovr_cal_q', 'geoid_hght', 'geoid_hght_units', 'geoid_slop', 'geoid_slop_units', 
'solid_tide', 'solid_tide_units', 'load_tidef', 'load_tidef_units', 'load_tideg', 'load_tideg_units', 'pole_tide', 'pole_tide_units',
'dry_trop_c', 'dry_trop_c_units', 'wet_trop_c', 'wet_trop_c_units', 'iono_c', 'iono_c_units', 'xovr_cal_c', 'xovr_cal_c_units', 
'n_reach_up', 'n_reach_up_units', 'n_reach_dn', 'n_reach_dn_units', 'rch_id_up', 'rch_id_up_units', 'rch_id_dn', 'rch_id_dn_units', 
'p_wse', 'p_wse_units', 'p_wse_var', 'p_wse_var_units', 'p_width', 'p_width_units', 'p_wid_var', 'p_wid_var_units', 
'p_n_nodes', 'p_n_nodes_units', 'p_dist_out', 'p_dist_out_units', 
'p_length', 'p_length_units', 'p_maf', 'p_maf_units', 'p_dam_id', 'p_dam_id_units', 
'p_n_ch_max', 'p_n_ch_max_units', 'p_n_ch_mod', 'p_n_ch_mod_units', 'p_low_slp',
'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
'crid', 'geometry', 'sword_version', 'collection_shortname', 'crid'
```

**Node data fields**

```bash
'reach_id', 'node_id', 'time', 'time_units', 'time_tai', 'time_tai_units', 'time_str',
'lat', 'lat_units', 'lon', 'lon_units', 'lat_u', 'lat_u_units', 'lon_u', 'lon_u_units', 'river_name',
'wse', 'wse_units', 'wse_u', 'wse_u_units', 'wse_r_u', 'wse_r_u_units', 
'width', 'width_units', 'width_u', 'width_u_units', 
'area_total', 'area_total_units', 'area_tot_u', 'area_tot_u_units', 
'area_detct', 'area_detct_units', 'area_det_u', 'area_det_u_units', 'area_wse', 'area_wse_units', 
'layovr_val', 'layovr_val_units', 'node_dist', 'node_dist_units', 'xtrk_dist', 'xtrk_dist_units',
'flow_angle', 'flow_angle_units', 'node_q', 'node_q_b',
'dark_frac', 'dark_frac_units', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_pix', 'n_good_pix_units', 
'xovr_cal_q', 'rdr_sig0', 'rdr_sig0_units', 'rdr_sig0_u', 'rdr_sig0_u_units', 'rdr_pol', 'geoid_hght', 'geoid_hght_units', 
'solid_tide', 'solid_tide_units', 'load_tidef', 'load_tidef_units', 'load_tideg', 'load_tideg_units', 'pole_tide', 'pole_tide_units', 
'dry_trop_c', 'dry_trop_c_units', 'wet_trop_c', 'iono_c', 'iono_c_units', 'xovr_cal_c', 'xovr_cal_c_units', 
'p_wse', 'p_wse_units', 'p_wse_var', 'p_wse_var_units', 'p_width', 'p_width_units', 'p_wid_var', 'p_wid_var_units', 
'p_dist_out', 'p_dist_out_units', 'p_length', 'p_length_units', 
'p_dam_id', 'p_dam_id_units', 'p_n_ch_max', 'p_n_ch_max_units', 'p_n_ch_mod', 'p_n_ch_mod_units', 
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
