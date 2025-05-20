################################################################################
# UNIT TESTS
################################################################################

from pdstable import *

import unittest

class Test_Pds4Table(unittest.TestCase):

  def runTest(self):

    INDEX_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'
    #######################################################################
    # Test csv table
    #######################################################################
    CSV_TABLE_FILE_NAME = 'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv'

    test_csv_table_basic = PdsTable(label_file=INDEX_PATH,
                                    table_file=CSV_TABLE_FILE_NAME)

    # Test strings
    test_star_names = test_csv_table_basic.column_values['Star Name']
    star_name_test_set = np.array(['Bper', 'SSgr', 'U0', 'U0201'])
    self.assertTrue(np.all(star_name_test_set == test_star_names[:4]))

    # Test ints
    test_star_num = test_csv_table_basic.column_values['Star Number']
    star_num_test_set = np.array([3, 8, 12, 16])
    self.assertTrue(np.all(star_num_test_set == test_star_num[:4]))

    # Test floats
    test_ra = test_csv_table_basic.column_values['RA(ICRS)']
    ra_test_set = np.array([47.04220716,
                            283.8163196 ,
                            219.5492129 ,
                            330.1143053])
    self.assertTrue(np.all(ra_test_set == test_ra[:4]))

    # Test dicts_by_row()
    rowdict = test_csv_table_basic.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]['RA(ICRS)'], ra_test_set[i])

    ######################################################################################
    # Test PdsTable instantiation without specifying a valid table name if multiple tables
    # are available
    ######################################################################################
    table_files = ("['uranus_occultation_ring_fit_rfrench_20201201.tab', " +
        "'uranus_occultation_ring_fit_rfrench_20201201.txt', " +
        "'uranus_occultation_ring_fit_rfrench_input_data_20201201.tab', " +
        "'uranus_occultation_ring_fit_rfrench_input_events_20201201.tab', " +
        "'uranus_occultation_ring_fit_rfrench_input_observatories_20201201.tab', " +
        "'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv']")
    try:
        test_csv_table_basic = PdsTable(label_file=INDEX_PATH)
    except ValueError as e:
        self.assertIn(table_files, str(e),
                      f'"{table_files}" NOT in error messages: "{str(e)}"')

    try:
        test_csv_table_basic = PdsTable(label_file=INDEX_PATH, table_file='xxx')
    except ValueError as e:
        self.assertIn(table_files, str(e),
                      f'"{table_files}" NOT in error messages: "{str(e)}"')

    ########################################################################
    # Row lookups
    # No File Specification or Bundle Name in .csv table, so return -1
    ########################################################################
    # File Specification
    self.assertEqual(test_csv_table_basic.filespec_column_index(), -1)
    # Bundle Name
    self.assertEqual(test_csv_table_basic.volume_column_index(), -1)

    ########################################################################
    # Row ranges
    # Can't specify row range since rows are not fixed length
    ########################################################################
    error_msg = 'cannot specify row range for the table without fixed length rows'
    try:
        partial_table = PdsTable(label_file=INDEX_PATH,
                                 row_range=(2,4),
                                 table_file=CSV_TABLE_FILE_NAME)
    except ValueError as e:
        self.assertIn(error_msg, str(e),
                      f'"{error_msg}" NOT in error messages: "{str(e)}"')

    # PDS4 TODO: Add tests for invalids & replacements

    #######################################################################
    # Test tab table
    #######################################################################
    TAB_TABLE_FILE_NAME = 'uranus_occultation_ring_fit_rfrench_20201201.tab'
    test_tab_table_basic = PdsTable(label_file=INDEX_PATH,
                                    table_file=TAB_TABLE_FILE_NAME)

    # Test strings
    test_ring_names = test_tab_table_basic.column_values['Ring name']
    ring_name_test_set = np.array(['six', 'five', 'four', 'alpha'])
    self.assertTrue(np.all(ring_name_test_set == test_ring_names[0:4]))

    # Test ints
    test_wavenum = test_tab_table_basic.column_values['Wavenumber']
    wavenum_test_set = np.array([-999, -999, -999, -999])
    self.assertTrue(np.all(wavenum_test_set == test_wavenum[:4]))

    # Test floats
    test_semimajor_axis = test_tab_table_basic.column_values['Semimajor axis']
    semimajor_axis_test_set = np.array([4.1837319048797E+04,
                                      4.2235094301041E+04,
                                      4.2571302273527E+04,
                                      4.4718670266706E+04])

    self.assertTrue(np.all(semimajor_axis_test_set == test_semimajor_axis[:4]))

    # Test dicts_by_row()
    rowdict = test_tab_table_basic.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]['Semimajor axis'], semimajor_axis_test_set[i])

    ########################################################################
    # Row lookups, no file spec or bundle name in this table, so return -1
    ########################################################################
    # File Specification
    self.assertEqual(test_tab_table_basic.filespec_column_index(), -1)
    # Bundle Name
    self.assertEqual(test_tab_table_basic.volume_column_index(), -1)

    ####################################
    # Row ranges
    ####################################

    partial_table = PdsTable(label_file=INDEX_PATH,
                             row_range=(2,4),
                             table_file=TAB_TABLE_FILE_NAME)
    self.assertEqual(partial_table.rows, 2)

    self.assertEqual(partial_table.filespec_column_index(), -1)
    self.assertEqual(partial_table.volume_column_index(), -1)

    self.assertEqual(partial_table.find_row_index(**{'Ring name': 'four'}), 0)
    self.assertEqual(partial_table.find_row_index(**{'Ring name': 'alpha'}), 1)


    ####################################
    # PdsLabel input option
    ####################################
    # For PDS4, we store the label dictionary in .lable instead of pdsparser.PdsLabel
    # instance, therefore we use "==" here instead of "is"
    test = PdsTable(label_file=INDEX_PATH,
                    label_contents=partial_table.pdslabel,
                    table_file=TAB_TABLE_FILE_NAME)
    self.assertTrue(test.pdslabel == partial_table.pdslabel)

    # PDS4 TODO: Add tests for invalids & replacements
