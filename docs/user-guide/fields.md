(fields-detail)=
# Fields

Hydrocron will return every field that is available in the archived source data. For SWOT River and Lake data products, these fields are the attributes that are available in the shapefiles.

In addition to the shapefile attributes, some additional fields are available through Hydrocron that are pulled from other locations such as the shapefile metadata (xml) and the filename. These include things like the cycle and pass numbers, CRID, granule name, continent ID, units, collection name, etc.

The [](fields) parameter is required, and you must list every field that you want to return in a comma-separated list, with no spaces. Units are a special case in that they will be automatically returned for any fields you request that have units attached. You do not need to explicitly list the units fields separately.

We strongly recommend returning and using the quality flags on the fields that have them to avoid degraded observations.

For each feature type, the full list of currently supported fields is below. Full descriptions of what these fields are and how to use them are available in the SWOT Product Description Documents available on the PO.DAAC collection landing pages for [Rivers](https://podaac.jpl.nasa.gov/dataset/SWOT_L2_HR_RiverSP_2.0) and [Lakes](https://podaac.jpl.nasa.gov/dataset/SWOT_L2_HR_LakeSP_2.0)

Occasionally new fields may be added to the SWOT data products. If there are fields you find in the SWOT shapefiles that are not returned from Hydrocron, please open an issue on the [Hydrocron GitHub repository](https://github.com/podaac/hydrocron).

**Reach fields**

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
'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
'granuleUR', 'ingest_time'
```

**Node fields**

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
'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
'granuleUR', 'ingest_time'
```

**Lake fields**
```bash
'lake_id', 'reach_id', 'obs_id', 'overlap', 'n_overlap',
'time', 'time_tai', 'time_str', 'wse', 'wse_u', 'wse_r_u', 'wse_std',
'area_total', 'area_tot_u', 'area_detct', 'area_det_u',
'layovr_val', 'xtrk_dist', 'ds1_l', 'ds1_l_u', 'ds1_q', 'ds1_q_u',
'ds2_l', 'ds2_l_u', 'ds2_q', 'ds2_q_u',
'quality_f', 'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f',
'xovr_cal_q', 'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c', 'lake_name', 'p_res_id',
'p_lon', 'p_lat', 'p_ref_wse', 'p_ref_area', 'p_date_t0', 'p_ds_t0', 'p_storage',
'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
'crid', 'geometry', 'PLD_version', 'collection_shortname', 'collection_version',
'granuleUR', 'ingest_time'
```
