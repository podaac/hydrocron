"""
Constants used for SWOT data loading

"""

reach_columns = [
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
    'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c'
]

node_columns = [
    'wse', 'wse_u', 'wse_r_u',
    'width', 'width_u',
    'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
    'layovr_val', 'node_dist', 'xtrk_dist',
    'flow_angle', 'node_q', 'node_q_b',
    'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_pix',
    'xovr_cal_q', 'rdr_sig0', 'rdr_sig0_u', 'rdr_pol',
    'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
    'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c'
]
