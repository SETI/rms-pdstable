################################################################################
# UNIT TESTS
################################################################################

from pdstable import *

import unittest

class Test_Pds4Table(unittest.TestCase):

  def runTest(self):

    INDEX_PATH = 'test_files/cassini_iss_cruise_index_edited.xml'

    test_table_basic = PdsTable(INDEX_PATH)

    # Test strings
    test_file_names = test_table_basic.column_values['File Name']
    file_name_test_set = np.array(['1294561143w.img',
                                   '1294561202w.img',
                                   '1294561261w.img',
                                   '1294561333w.img'])

    self.assertTrue(np.all(file_name_test_set == test_file_names[:4]))

    # Test ints
    test_cmd_seq_num_idx = test_table_basic.column_values['COMMAND_SEQUENCE_NUMBER']
    cmd_seq_num_idx_test_set = np.array([65534, 65534, 65534, 65534])
    self.assertTrue(np.all(cmd_seq_num_idx_test_set == test_cmd_seq_num_idx[:4]))

    # Test floats
    test_dark_strip_mean = test_table_basic.column_values['DARK_STRIP_MEAN']
    dark_strip_mean_test_set = np.array([68.44, 68.47, 68.39, 68.47])
    self.assertTrue(np.all(dark_strip_mean_test_set == test_dark_strip_mean[:4]))

    # Test times as strings
    test_start_time_strs = test_table_basic.column_values['START_TIME']
    start_time_str_test_set = ['1999-009T08:14:21.687',
                               '1999-009T08:15:20.687',
                               '1999-009T08:16:19.687',
                               '1999-009T08:17:31.686']

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
    start_time_test_set = np.array([-30858306.313,
                                    -30858247.313,
                                    -30858188.313,
                                    -30858116.314])

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
    # FILE_SPECIFICATION_NAME
    self.assertEqual(test_table_basic.filespec_column_index(), 3)
    # VOLUME_ID
    self.assertEqual(test_table_basic.volume_column_index(), 4)
    # FILE_SPECIFICATION_NAME
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561261_1.IMG'), 2)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561261_1.IMG'), [2])
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561333_1.IMG'), 3)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561333_1.IMG'), [3])
    # VOLUME_ID & FILE_SPECIFICATION_NAME
    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            'COISS_1001',
            'data/1294561143_1295221348/N1294562836_1.IMG'), 15)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            'COISS_1001',
            'data/1294561143_1295221348/N1294562836_1.IMG'), [15])


    ####################################
    # Row ranges
    ####################################

    partial_table = PdsTable(INDEX_PATH, row_range=(2,4))
    self.assertEqual(partial_table.rows, 2)

    self.assertEqual(partial_table.filespec_column_index(), 3)
    self.assertEqual(partial_table.volume_column_index(), 4)

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561261_1.IMG'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561261_1.IMG'), [0])

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561333_1.IMG'), 1)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            '', 'data/1294561143_1295221348/W1294561333_1.IMG'), [1])
    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            'COISS_1001',
            'data/1294561143_1295221348/W1294561261_1.IMG'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            'COISS_1001',
            'data/1294561143_1295221348/W1294561261_1.IMG'), [0])

    ####################################
    # PdsLabel input option
    ####################################
    # For PDS4, we store the label dictionary in .lable instead of pdsparser.PdsLabel
    # instance, therefore we use "==" here instead of "is"
    test = PdsTable(INDEX_PATH, label_contents=partial_table.pdslabel)
    self.assertTrue(test.pdslabel == partial_table.pdslabel)

    # PDS4 TODO: Add tests for invalids & replacements
