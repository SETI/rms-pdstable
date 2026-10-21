################################################################################
# UNIT TESTS
################################################################################


import numpy as np

from pdstable import PdsTable

INDEX_PATH = 'test_files/uranus_occultations_index.xml'


def test_pds4_table_uranus_occultations() -> None:


    test_table_basic = PdsTable(INDEX_PATH)

    # Test strings
    test_file_names = test_table_basic.column_values['File Name']
    file_name_test_set = np.array([
        'u0201_palomar_508cm_2200nm_radius_equator_egress_1000m.xml',
        'u0201_palomar_508cm_2200nm_radius_equator_egress_100m.xml',
        'u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml',
        'u0201_palomar_508cm_2200nm_radius_equator_ingress_1000m.xml'
    ])
    assert np.all(file_name_test_set == test_file_names[0:4])

    # Test ints
    test_data_quality_idx = test_table_basic.column_values['Data Quality Index']
    data_quality_idx_test_set = np.array([6, 6, 6, 6])
    assert np.all(data_quality_idx_test_set == test_data_quality_idx[:4])

    # Test floats
    test_proj_star_diameter = test_table_basic.column_values['Projected Star Diameter']
    proj_star_diameter_test_set = np.array([0.3, 0.3, 0.3, 0.3])
    assert np.all(proj_star_diameter_test_set == test_proj_star_diameter[:4])

    # Test times as strings
    test_start_time_strs = test_table_basic.column_values['Start Time UTC']
    start_time_str_test_set = ['2002-07-29T10:03:17.0654Z',
                               '2002-07-29T10:03:13.4075Z',
                               '2002-07-29T10:03:15.4524Z',
                               '2002-07-29T09:48:38.6088Z']
    assert start_time_str_test_set[0] == test_start_time_strs[0]
    assert start_time_str_test_set[1] == test_start_time_strs[1]
    assert start_time_str_test_set[2] == test_start_time_strs[2]
    assert start_time_str_test_set[3] == test_start_time_strs[3]

    assert isinstance(test_start_time_strs, np.ndarray)
    assert isinstance(test_start_time_strs[0], np.str_)

    # Test dicts_by_row()
    rowdict = test_table_basic.dicts_by_row()
    for i in range(4):
        assert rowdict[i]['Start Time UTC'] == test_start_time_strs[i]

    rowvals = test_table_basic.get_column('Start Time UTC')
    rowmasks = test_table_basic.get_column_mask('Start Time UTC')
    for i in range(10):
        assert rowdict[i]['Start Time UTC'] == rowvals[i]
        assert not rowmasks[i]

    # Test strings with whitespace preserved
    assert rowdict[22]['Star ID'] == 'u0   '

    ####################################
    # Test times as seconds (floats)
    ####################################

    test_table_secs = PdsTable(INDEX_PATH, times=['Start Time UTC'])

    test_start_times = test_table_secs.column_values['Start Time UTC']
    start_time_test_set = np.array([81209029.0654, 81209025.4075,
                                    81209027.4524, 81208150.6088])
    assert np.all(start_time_test_set == test_start_times[:4])
    assert isinstance(start_time_test_set, np.ndarray)

    # Test dicts_by_row()
    rowdict = test_table_secs.dicts_by_row()
    for i in range(4):
        assert rowdict[i]['Start Time UTC'] == start_time_test_set[i]

    rowvals = test_table_secs.get_column('Start Time UTC')
    rowmask = test_table_secs.get_column_mask('Start Time UTC')
    for i in range(10):
        assert rowdict[i]['Start Time UTC'] == rowvals[i]
        assert not rowmask[i]

    ####################################
    # Row lookups
    ####################################
    # File Specification
    assert test_table_basic.filespec_column_index() == 2
    # Bundle Name
    assert test_table_basic.volume_column_index() == 4
    # File Specification
    assert test_table_basic.find_row_index_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == 2
    assert test_table_basic.find_row_indices_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == [2]
    assert test_table_basic.find_row_index_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_ingress_1000m.xml') == 3
    assert test_table_basic.find_row_indices_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_ingress_1000m.xml') == [3]
    # Bundle Name & File Specification
    assert test_table_basic.find_row_index_by_volume_filespec('uranus_occ_u0_kao_91cm', r'2021-04-uranus-redelivery\uranus_occ_u0_kao_91cm\data\global' + r'\u0_kao_91cm_734nm_radius_equator_egress_1000m.xml') == 21
    assert test_table_basic.find_row_indices_by_volume_filespec('uranus_occ_u0_kao_91cm', r'2021-04-uranus-redelivery\uranus_occ_u0_kao_91cm\data\global' + r'\u0_kao_91cm_734nm_radius_equator_egress_1000m.xml') == [21]

    ####################################
    # Row ranges
    ####################################

    partial_table = PdsTable(INDEX_PATH, row_range=(2, 4))
    assert partial_table.rows == 2

    assert partial_table.filespec_column_index() == 2
    assert partial_table.volume_column_index() == 4

    assert partial_table.find_row_index_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == 0
    assert partial_table.find_row_indices_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == [0]

    assert partial_table.find_row_index_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_ingress_1000m.xml') == 1
    assert partial_table.find_row_indices_by_volume_filespec('', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_ingress_1000m.xml') == [1]

    assert partial_table.find_row_index_by_volume_filespec('uranus_occ_u0201_palomar_508cm', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == 0
    assert partial_table.find_row_indices_by_volume_filespec('uranus_occ_u0201_palomar_508cm', r'2021-04-uranus-redelivery\uranus_occ_u0201_palomar_508cm\data\global' + r'\u0201_palomar_508cm_2200nm_radius_equator_egress_500m.xml') == [0]

    ####################################
    # PdsLabel input option
    ####################################
    # For PDS4, we store the label dictionary in .label instead of pdsparser.PdsLabel
    # instance, therefore we use "==" here instead of "is"
    test = PdsTable(INDEX_PATH, label_contents=partial_table.pdslabel)
    assert test.pdslabel == partial_table.pdslabel

    # PDS4 TODO: Add tests for invalids & replacements
