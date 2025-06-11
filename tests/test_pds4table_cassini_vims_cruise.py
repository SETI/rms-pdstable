################################################################################
# UNIT TESTS
################################################################################

from pdstable import *

import unittest

class Test_Pds4Table(unittest.TestCase):

  def runTest(self):

    INDEX_PATH = 'test_files/cassini_vims_cruise_index_edited.xml'

    test_table_basic = PdsTable(INDEX_PATH)

    # Test strings
    test_file_names = test_table_basic.column_values['File Name']
    file_name_test_set = np.array(['1294638283.qub',
                                   '1294638377.qub',
                                   '1294638472.qub',
                                   '1294638567.qub'])

    self.assertTrue(np.all(file_name_test_set == test_file_names[:4]))

    # Test ints
    test_swath_width = test_table_basic.column_values['SWATH_WIDTH']
    swath_width_test_set = np.array([1, 1, 1, 1])
    self.assertTrue(np.all(swath_width_test_set == test_swath_width[:4]))

    # Test floats
    test_ir_exposure = test_table_basic.column_values['IR_EXPOSURE']
    ir_exposure_test_set = np.array([80.00, 80.00, 80.00, 80.00])
    self.assertTrue(np.all(ir_exposure_test_set == test_ir_exposure[:4]))

    # Test times as strings
    test_start_time_strs = test_table_basic.column_values['START_TIME']
    start_time_str_test_set = ['1999-01-10T05:40:00.157',
                               '1999-01-10T05:40:26.914',
                               '1999-01-10T05:40:53.671',
                               '1999-01-10T05:41:20.428']

    self.assertEqual(start_time_str_test_set[0], test_start_time_strs[0])
    self.assertEqual(start_time_str_test_set[1], test_start_time_strs[1])
    self.assertEqual(start_time_str_test_set[2], test_start_time_strs[2])
    self.assertEqual(start_time_str_test_set[3], test_start_time_strs[3])

    self.assertTrue(isinstance(test_start_time_strs, np.ndarray))
    self.assertTrue(isinstance(test_start_time_strs[0], np.str_))

    # Test dicts_by_row()
    rowdict = test_table_basic.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]['START_TIME'], test_start_time_strs[i])

    rowvals = test_table_basic.get_column('START_TIME')
    rowmasks = test_table_basic.get_column_mask('START_TIME')
    for i in range(10):
        self.assertEqual(rowdict[i]['START_TIME'], rowvals[i])
        self.assertFalse(rowmasks[i])

    ####################################
    # Test times as seconds (floats)
    ####################################

    test_table_secs = PdsTable(INDEX_PATH, times=['START_TIME'])

    test_start_times = test_table_secs.column_values['START_TIME']
    start_time_test_set = np.array([-30781167.843,
                                    -30781141.086,
                                    -30781114.329,
                                    -30781087.572])

    self.assertTrue(np.all(start_time_test_set == test_start_times[:4]))
    self.assertTrue(isinstance(start_time_test_set, np.ndarray))

    # Test dicts_by_row()
    rowdict = test_table_secs.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]['START_TIME'], start_time_test_set[i])

    rowvals = test_table_secs.get_column('START_TIME')
    rowmask = test_table_secs.get_column_mask('START_TIME')
    for i in range(10):
        self.assertEqual(rowdict[i]['START_TIME'], rowvals[i])
        self.assertFalse(rowmask[i])

    ####################################
    # Row lookups
    ####################################
    # File Name
    self.assertEqual(test_table_basic.filespec_column_index(), 1)
    # VOLUME_ID
    self.assertEqual(test_table_basic.volume_column_index(), 22)
    # File Name
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            '', '1294638472.qub'), 2)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            '', '1294638472.qub'), [2])
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            '', '1294638567.qub'), 3)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            '', '1294638567.qub'), [3])
    # VOLUME_ID & File Name
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            'COVIMS_0001',
            '1294639703.qub '), 15)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            'COVIMS_0001',
            '1294639703.qub '), [15])

    ####################################
    # Row ranges
    ####################################

    partial_table = PdsTable(INDEX_PATH, row_range=(2,4))
    self.assertEqual(partial_table.rows, 2)

    self.assertEqual(partial_table.filespec_column_index(), 1)
    self.assertEqual(partial_table.volume_column_index(), 22)

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            '', '1294638472.qub'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            '', '1294638472.qub'), [0])

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            '', '1294638567.qub'), 1)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            '', '1294638567.qub'), [1])
    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            'COVIMS_0001',
            '1294638472.qub'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            'COVIMS_0001',
            '1294638472.qub'), [0])

    ####################################
    # PdsLabel input option
    ####################################
    # For PDS4, we store the label dictionary in .lable instead of pdsparser.PdsLabel
    # instance, therefore we use "==" here instead of "is"
    test = PdsTable(INDEX_PATH, label_contents=partial_table.pdslabel)
    self.assertTrue(test.pdslabel == partial_table.pdslabel)

    # PDS4 TODO: Add tests for invalids & replacements
