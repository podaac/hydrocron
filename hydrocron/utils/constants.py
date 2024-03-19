"""
Constants used throughout API and DB modules

"""
import os.path

# ----------------- #
# TESTING CONSTANTS #
# ----------------- #
TEST_SHAPEFILE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../..', 'tests', 'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa E501
))

TEST_FILENAME = (
    "SWOT_L2_HR_RiverSP_Reach_548_011_NA_"
    "20230610T193337_20230610T193344_PIA1_01.zip")

TEST_ITEM_DICT = {
    "reach_id": "71224100223",
    "time": "739741183.129",
    "time_str": "2023-06-10T19:39:43Z",
    "wse": "286.2983",
    "cycle_id": "548",
    "sword_version": "15",
    "p_lat_units": "degrees_north"
}

DB_TEST_TABLE_NAME = "hydrocron-swot-test-table"
API_TEST_TABLE_NAME = "hydrocron-swot-reach-table"
TEST_PARTITION_KEY_NAME = 'reach_id'
TEST_SORT_KEY_NAME = 'range_start_time'
TEST_REACH_ID_VALUE = '71224100223'
TEST_TIME_VALUE = '2023-06-10T19:33:37Z'
TEST_WSE_VALUE = '286.2983'
TEST_SWORD_VERSION_VALUE = '15'
TEST_UNITS_FIELD = 'p_lat_units'
TEST_UNITS = 'degrees_north'

# ------------ #
# PROD CONSTANTS #
# ------------ #
SWOT_REACH_TABLE_NAME = "hydrocron-swot-reach-table"
SWOT_NODE_TABLE_NAME = "hydrocron-swot-node-table"

SWOT_REACH_COLLECTION_NAME = "SWOT_L2_HR_RIVERSP_1.0"
SWOT_NODE_COLLECTION_NAME = "SWOT_L2_HR_RIVERSP_1.0"

SWOT_REACH_PARTITION_KEY = "reach_id"
SWOT_NODE_PARTITION_KEY = "node_id"
SWOT_REACH_SORT_KEY = "range_start_time"
SWOT_NODE_SORT_KEY = "range_start_time"

FIELDNAME_REACH_ID = 'reach_id'
FIELDNAME_TIME = 'time'
FIELDNAME_TIME_STR = 'time_str'
FIELDNAME_WSE = 'wse'
FIELDNAME_SLOPE = 'slope'
FIELDNAME_P_LON = 'p_lon'
FIELDNAME_P_LAT = 'p_lat'
FIELDNAME_SWORD_VERSION = 'sword_version'

S3_CREDS_ENDPOINT = "https://archive.swot.podaac.earthdata.nasa.gov/s3credentials"

REACH_DATA_COLUMNS = [
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
    'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'n_good_nod',
    'obs_frac_n', 'xovr_cal_q', 'geoid_hght', 'geoid_slop',
    'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
    'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c'
]

NODE_DATA_COLUMNS = [
    'wse', 'wse_u', 'wse_r_u',
    'width', 'width_u',
    'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
    'layovr_val', 'node_dist', 'xtrk_dist',
    'flow_angle', 'node_q', 'node_q_b',
    'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'n_good_pix',
    'xovr_cal_q', 'rdr_sig0', 'rdr_sig0_u', 'rdr_pol',
    'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
    'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c'
]

REACH_ALL_COLUMNS = [
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
    'crid', 'geometry', 'sword_version', 'collection_shortname', 'crid'
]

NODE_ALL_COLUMNS = [
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
    'crid', 'geometry', 'sword_version', 'collection_shortname', 'crid'
]
