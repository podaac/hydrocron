"""
Constants used throughout API and DB modules

"""
import os.path

# ----------------- #
# TESTING CONSTANTS #
# ----------------- #

# -------- River Reach
TEST_REACH_SHAPEFILE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../..', 'tests', 'data',
    'SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip'  # noqa E501
))
TEST_REACH_PATHNAME = (
    "SWOT_L2_HR_RiverSP_2.0/SWOT_L2_HR_RiverSP_Reach_548_011_NA_20230610T193337_20230610T193344_PIA1_01.zip")

TEST_REACH_FILENAME = (
    "SWOT_L2_HR_RiverSP_Reach_548_011_NA_"
    "20230610T193337_20230610T193344_PIA1_01.zip")

TEST_REACH_ITEM_DICT = {
    "reach_id": "71224100223",
    "time": "739741183.129",
    "time_str": "2023-06-10T19:39:43Z",
    "wse": "286.2983",
    "cycle_id": "548",
    "sword_version": "15",
    "p_lat_units": "degrees_north"
}

DB_TEST_TABLE_NAME = "hydrocron-swot-test-table"
API_TEST_REACH_TABLE_NAME = "hydrocron-swot-reach-table"
API_TEST_NODE_TABLE_NAME = "hydrocron-swot-node-table"
TEST_REACH_COLLECTION_NAME = "SWOT_L2_HR_RiverSP_2.0"
TEST_REACH_TRACK_INGEST_TABLE_NAME = "hydrocron-swot-reach-track-ingest-table"
TEST_REACH_PARTITION_KEY_NAME = 'reach_id'
TEST_REACH_SORT_KEY_NAME = 'range_start_time'
TEST_REACH_ID_VALUE = '71224100223'
TEST_REACH_TIME_VALUE = '2023-06-10T19:33:37Z'
TEST_REACH_WSE_VALUE = '286.2983'
TEST_REACH_SWORD_VERSION_VALUE = '15'
TEST_REACH_UNITS_FIELD = 'p_lat_units'
TEST_REACH_UNITS = 'degrees_north'

# -------- Prior Lakes
TEST_PLAKE_SHAPEFILE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../..', 'tests', 'data',
    'SWOT_L2_HR_LakeSP_Prior_018_100_GR_20240713T111741_20240713T112027_PIC0_01.zip'  # noqa E501
))

TEST_PLAKE_PATHNAME = (
    "SWOT_L2_HR_LakeSP_2.0/SWOT_L2_HR_LakeSP_Prior_018_100_GR_20240713T111741_20240713T112027_PIC0_01.zip")

TEST_PLAKE_FILENAME = (
    "SWOT_L2_HR_LakeSP_Prior_018_100_GR_20240713T111741_20240713T112027_PIC0_01.zip")

TEST_PLAKE_ITEM_DICT = {
    "lake_id": "9130047472",
    "time": "774184696.644",
    "time_str": "2024-07-13T11:18:16Z",
    "wse": "307.482",
    "cycle_id": "018",
    "PLD_version": "105",
    "area_total_units": "km^2"
}

TEST_PLAKE_GEOM_DICT = {
    "lake_id": "9130047472",
    "geometry": (
        (-50.14521191, 69.30222612), (-50.14550301, 69.30215475),
        (-50.14612341, 69.30224091), (-50.14641609, 69.30216916),
        (-50.14674362, 69.30232713), (-50.14677875, 69.30255678),
        (-50.1471051, 69.30271506,), (-50.14713811, 69.30294524),
        (-50.1474643, 69.30310355), (-50.14808323, 69.30319009),
        (-50.14837586, 69.30311835), (-50.1489949, 69.30320486),
        (-50.14932109, 69.30336317), (-50.14993974, 69.30344978),
        (-50.14990648, 69.30321964), (-50.14987337, 69.30298947),
        (-50.15016696, 69.30291749), (-50.15046021, 69.30284559),
        (-50.15075352, 69.30277367), (-50.15137324, 69.30286),
        (-50.15166675, 69.30278803), (-50.15228657, 69.30287434),
        (-50.15261279, 69.30303264), (-50.15293903, 69.30319094),
        (-50.15326526, 69.30334923), (-50.15359148, 69.30350753),
        (-50.15362358, 69.30373794), (-50.15365621, 69.30396824),
        (-50.15398295, 69.30412641), (-50.15460271, 69.30421273),
        (-50.15492895, 69.30437102), (-50.15496171, 69.30460129),
        (-50.15558151, 69.3046876), (-50.15590777, 69.3048459),
        (-50.15623406, 69.30500419), (-50.156559, 69.30516281),
        (-50.15626538, 69.30523481), (-50.15597192, 69.30530677),
        (-50.15567856, 69.30537871), (-50.15538527, 69.30545062),
        (-50.15541698, 69.30568115), (-50.15512387, 69.30575302),
        (-50.15483084, 69.30582487), (-50.15421294, 69.30573808),
        (-50.15392004, 69.3058099), (-50.15359524, 69.30565124),
        (-50.15297631, 69.3055647), (-50.15268369, 69.30563645),
        (-50.15235735, 69.30547818), (-50.15203056, 69.30532002),
        (-50.15141283, 69.30523318), (-50.15112013, 69.30530495),
        (-50.1505015, 69.30521834), (-50.15017531, 69.30506003),
        (-50.15046779, 69.30498832), (-50.15043315, 69.30475852),
        (-50.1501077, 69.30460003), (-50.15040003, 69.30452836),
        (-50.15036646, 69.3042983), (-50.15065919, 69.30422653),
        (-50.15095197, 69.30415475), (-50.15091834, 69.3039247),
        (-50.15059214, 69.3037664), (-50.14997352, 69.30367978),
        (-50.14968083, 69.30375154), (-50.14906209, 69.30366496),
        (-50.14844328, 69.30357838), (-50.14815009, 69.30365026),
        (-50.14785768, 69.30372195), (-50.14753153, 69.30356363),
        (-50.14691338, 69.30347689), (-50.14629497, 69.30339021),
        (-50.14567671, 69.3033035), (-50.14535057, 69.30314519),
        (-50.14564277, 69.30307356), (-50.14626111, 69.30316024),
        (-50.14655355, 69.30308855), (-50.14651952, 69.30285862),
        (-50.14648605, 69.30262853), (-50.14615845, 69.30247059),
        (-50.14553817, 69.30238438), (-50.14521191, 69.30222612))
}


TEST_PLAKE_ITEM_NO_GEO_DICT = {
    "lake_id": "9120145452"
}

DB_TEST_PLAKE_TABLE_NAME = "hydrocron-swot-testlake-table"
API_TEST_PLAKE_TABLE_NAME = "hydrocron-swot-prior-lake-table"
TEST_PLAKE_COLLECTION_NAME = "SWOT_L2_HR_LakeSP_2.0"
TEST_PLAKE_PARTITION_KEY_NAME = 'lake_id'
TEST_PLAKE_SORT_KEY_NAME = 'range_start_time'
TEST_PLAKE_ID_VALUE = '9130047472'
TEST_PLAKE_TIME_VALUE = '2024-07-13T11:18:16Z'
TEST_PLAKE_WSE_VALUE = '307.482'
TEST_PLAKE_PLD_VERSION_VALUE = '105'
TEST_PLAKE_UNITS_FIELD = 'area_total'
TEST_PLAKE_UNITS = 'km^2'

# ------------ #
# PROD CONSTANTS #
# ------------ #
SWOT_REACH_TABLE_NAME = "hydrocron-swot-reach-table"
SWOT_NODE_TABLE_NAME = "hydrocron-swot-node-table"
SWOT_PRIOR_LAKE_TABLE_NAME = "hydrocron-swot-prior-lake-table"
SWOT_REACH_TRACK_INGEST_TABLE_NAME = "hydrocron-swot-reach-track-ingest-table"
SWOT_NODE_TRACK_INGEST_TABLE_NAME = "hydrocron-swot-node-track-ingest-table"
SWOT_PRIOR_LAKE_TRACK_INGEST_TABLE_NAME = "hydrocron-swot-prior-lake-track-ingest-table"

TABLE_COLLECTION_INFO = [
    {'collection_name': 'SWOT_L2_HR_RiverSP_2.0',
     'table_name': 'hydrocron-swot-reach-table',
     'track_table': 'hydrocron-swot-reach-track-ingest-table',
     'feature_type': 'Reach',
     'feature_id': 'reach_id'
     },
    {'collection_name': 'SWOT_L2_HR_RiverSP_2.0',
     'table_name': 'hydrocron-swot-node-table',
     'track_table': 'hydrocron-swot-node-track-ingest-table',
     'feature_type': 'Node',
     'feature_id': 'node_id'
     },
    {'collection_name': 'SWOT_L2_HR_LakeSP_2.0',
     'table_name': 'hydrocron-swot-prior-lake-table',
     'track_table': 'hydrocron-swot-prior-lake-track-ingest-table',
     'feature_type': 'LakeSP_Prior',
     'feature_id': 'lake_id'
     },
    {'collection_name': 'SWOT_L2_HR_RiverSP_D',
     'table_name': 'hydrocron-SWOT_L2_HR_RiverSP_D-reach-table',
     'track_table': 'hydrocron-SWOT_L2_HR_RiverSP_D-reach-track-ingest',
     'feature_type': 'Reach',
     'feature_id': 'reach_id'
     },
    {'collection_name': 'SWOT_L2_HR_RiverSP_D',
     'table_name': 'hydrocron-SWOT_L2_HR_RiverSP_D-node-table',
     'track_table': 'hydrocron-SWOT_L2_HR_RiverSP_D-node-track-ingest',
     'feature_type': 'Node',
     'feature_id': 'node_id'
     },
    {'collection_name': 'SWOT_L2_HR_LakeSP_D',
     'table_name': 'hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-table',
     'track_table': 'hydrocron-SWOT_L2_HR_LakeSP_D-prior-lake-track-ingest',
     'feature_type': 'LakeSP_Prior',
     'feature_id': 'lake_id'
     }
]

FEATURE_ID = {
    "SWOT_L2_HR_RiverSP_reach_2.0": "reach_id",
    "SWOT_L2_HR_RiverSP_node_2.0": "node_id",
    "SWOT_L2_HR_LakeSP_prior_2.0": "lake_id"
}

SHORTNAME = {
    "SWOT_L2_HR_RiverSP_reach_2.0": "SWOT_L2_HR_RiverSP_2.0",
    "SWOT_L2_HR_RiverSP_node_2.0": "SWOT_L2_HR_RiverSP_2.0",
    "SWOT_L2_HR_LakeSP_prior_2.0": "SWOT_L2_HR_LakeSP_2.0"
}

SWOT_PRIOR_LAKE_FILL_GEOMETRY_COORDS = (
        (-31.286028054129474, -27.207309600925463),
        (-22.19117572552625, -28.812946226841383),
        (-15.725605024311761, -29.21206933352415),
        (-9.73430598260046, -29.228374663756604),
        (-9.643271006951636, -27.233170541912884),
        (-13.841716582541977, -27.37318973052451),
        (-13.640561876091681, -21.64742387547294),
        (-15.517427505373604, -21.61501976602659),
        (-15.687806151090996, -28.090307824912784),
        (-20.53678800850099, -28.156869804349213),
        (-20.271711250148456, -24.421282696689033),
        (-16.826147231682597, -24.69813060607345),
        (-16.457685427420472, -21.588744491452957),
        (-21.46664265437724, -21.33573507315593),
        (-21.962226106320827, -27.948720914494196),
        (-23.98629064034978, -27.80816909915125),
        (-22.949633572250406, -20.8450893435173),
        (-25.16962667009571, -20.772294910422403),
        (-25.61120124377038, -25.40631583584434),
        (-31.032731158967948, -24.810351227750644),
        (-31.286028054129474, -27.207309600925463))

SWOT_REACH_PARTITION_KEY = "reach_id"
SWOT_NODE_PARTITION_KEY = "node_id"
SWOT_PRIOR_LAKE_PARTITION_KEY = "lake_id"
SWOT_REACH_SORT_KEY = "range_start_time"
SWOT_NODE_SORT_KEY = "range_start_time"
SWOT_PRIOR_LAKE_SORT_KEY = "range_start_time"

FIELDNAME_REACH_ID = 'reach_id'
FIELDNAME_LAKE_ID = 'lake_id'
FIELDNAME_TIME = 'time'
FIELDNAME_TIME_STR = 'time_str'
FIELDNAME_WSE = 'wse'
FIELDNAME_SLOPE = 'slope'
FIELDNAME_P_LON = 'p_lon'
FIELDNAME_P_LAT = 'p_lat'
FIELDNAME_SWORD_VERSION = 'sword_version'
FIELDNAME_PLD_VERSION = 'PLD_version'

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

PRIOR_LAKE_DATA_COLUMNS = [
    'wse', 'wse_u', 'wse_r_u', 'wse_std',
    'area_total', 'area_tot_u', 'area_detct', 'area_det_u',
    'layovr_val', 'xtrk_dist', 'ds1_l', 'ds1_l_u', 'ds1_q', 'ds1_q_u',
    'ds2_l', 'ds2_l_u', 'ds2_q', 'ds2_q_u',
    'quality_f', 'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f',
    'xovr_cal_q', 'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
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
    'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
    'granuleUR', 'ingest_time'
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

PRIOR_LAKE_ALL_COLUMNS = [
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
    'crid', 'geometry', 'PLD_version', 'collection_shortname', 'crid'
]
