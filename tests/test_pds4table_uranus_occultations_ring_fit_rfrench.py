################################################################################
# UNIT TESTS
################################################################################

from pdstable import *

import unittest

class Test_Pds4Table(unittest.TestCase):

  def runTest(self):

    INDEX_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'
    TABLE_FILE_NAME = 'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv'

    test_table_basic = PdsTable(label_file=INDEX_PATH,
                                table_file=TABLE_FILE_NAME)

    # Test strings
    test_file_names = test_table_basic.column_values['Star Name']
    file_name_test_set = np.array(['Bper', 'SSgr', 'U0', 'U0201'])
    self.assertTrue(np.all(file_name_test_set == test_file_names[:4]))

    # Test ints
    test_data_quality_idx = test_table_basic.column_values['Star Number']
    data_quality_idx_test_set = np.array([3, 8, 12, 16])
    self.assertTrue(np.all(data_quality_idx_test_set == test_data_quality_idx[:4]))

    # Test floats
    test_proj_star_diameter = test_table_basic.column_values['RA(ICRS)']
    proj_star_diameter_test_set = np.array([47.04220716,
                                            283.8163196 ,
                                            219.5492129 ,
                                            330.1143053])
    self.assertTrue(np.all(proj_star_diameter_test_set == test_proj_star_diameter[:4]))

    # Test dicts_by_row()
    rowdict = test_table_basic.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]['RA(ICRS)'], proj_star_diameter_test_set[i])

    ######################################################################################
    # Test PdsTable instantiation without specifying a valid table name if multiple tables
    # are available
    ######################################################################################
    table_files = "['uranus_occultation_ring_fit_rfrench_20201201.tab', 'uranus_occultation_ring_fit_rfrench_20201201.txt', 'uranus_occultation_ring_fit_rfrench_input_data_20201201.tab', 'uranus_occultation_ring_fit_rfrench_input_events_20201201.tab', 'uranus_occultation_ring_fit_rfrench_input_observatories_20201201.tab', 'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv']"
    try:
        test_table_basic = PdsTable(label_file=INDEX_PATH)
    except ValueError as e:
        self.assertIn(table_files, str(e),
                      f'"{table_files}" NOT in error messages: "{str(e)}"')

    try:
        test_table_basic = PdsTable(label_file=INDEX_PATH, table_file='xxx')
    except ValueError as e:
        self.assertIn(table_files, str(e),
                      f'"{table_files}" NOT in error messages: "{str(e)}"')

    ########################################################################
    # Row lookups
    # No File Specification or Bundle Name in .csv table, so return -1
    ########################################################################
    # File Specification
    self.assertEqual(test_table_basic.filespec_column_index(), -1)
    # Bundle Name
    self.assertEqual(test_table_basic.volume_column_index(), -1)

    ########################################################################
    # Row ranges
    # Can't specify row range since rows are not fixed length
    ########################################################################
    error_msg = 'cannot specify row range for the table without fixed length rows'
    try:
        partial_table = PdsTable(label_file=INDEX_PATH,
                                 row_range=(2,4),
                                 table_file=TABLE_FILE_NAME)
    except ValueError as e:
        self.assertIn(error_msg, str(e),
                      f'"{error_msg}" NOT in error messages: "{str(e)}"')

    # PDS4 TODO: Add tests for invalids & replacements
