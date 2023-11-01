################################################################################
# UNIT TESTS
################################################################################

from pdstable import *

import unittest

class Test_PdsTable(unittest.TestCase):

  def runTest(self):

    # Testing different values parsed correctly...
    INDEX_PATH = "test_files/cassini_iss_index.lbl"
    EDITED_INDEX_PATH = "test_files/cassini_iss_index_edited.lbl"

    test_table_basic = PdsTable(INDEX_PATH)

    # Test strings
    test_file_names = test_table_basic.column_values['FILE_NAME']
    file_name_test_set = np.array(['N1573186009_1.IMG',
                                   'W1573186009_1.IMG',
                                   'N1573186041_1.IMG',
                                   'W1573186041_1.IMG'])
    self.assertTrue(np.all(file_name_test_set == test_file_names[0:4]))

    # Test floats
    test_cbody_dists = test_table_basic.column_values['CENTRAL_BODY_DISTANCE']
    cent_body_dist_test_set = np.array([2869736.9, 2869736, 2869707,
                                        2869706.9])
    self.assertTrue(np.all(cent_body_dist_test_set == test_cbody_dists[0:4]))

    # test vectors
    test_sc_vels = test_table_basic.column_values['SC_TARGET_VELOCITY_VECTOR']
    sc_vels_test_set = np.array([[1.2223705, -1.1418157, -0.055303727],
                                 [1.2223749, -1.1418146, -0.055303917],
                                 [1.2225166, -1.1417793, -0.055309978],
                                 [1.2225173, -1.1417791, -0.055310007]])
    self.assertTrue(np.all(sc_vels_test_set == test_sc_vels[0:4]))

    # Test times as strings
    test_start_time_strs = test_table_basic.column_values['START_TIME']
    start_time_str_test_set = ['2007-312T03:31:12.392',
                               '2007-312T03:31:14.372',
                               '2007-312T03:31:45.832',
                               '2007-312T03:31:46.132']
    self.assertEqual(start_time_str_test_set[0], test_start_time_strs[0])
    self.assertEqual(start_time_str_test_set[1], test_start_time_strs[1])
    self.assertEqual(start_time_str_test_set[2], test_start_time_strs[2])
    self.assertEqual(start_time_str_test_set[3], test_start_time_strs[3])

    self.assertTrue(isinstance(test_start_time_strs, np.ndarray))
    self.assertTrue(isinstance(test_start_time_strs[0], np.str_))

    # Test dicts_by_row()
    rowdict = test_table_basic.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]["START_TIME"], test_start_time_strs[i])

    rowvals = test_table_basic.get_column("START_TIME")
    rowmasks = test_table_basic.get_column_mask("START_TIME")
    for i in range(10):
        self.assertEqual(rowdict[i]["START_TIME"], rowvals[i])
        self.assertFalse(rowmasks[i])

    ####################################
    # Test times as seconds (floats)
    ####################################

    test_table_secs = PdsTable(INDEX_PATH, times=['START_TIME'])

    test_start_times = test_table_secs.column_values['START_TIME']
    start_time_test_set = np.array([247807905.392, 247807907.372,
                                    247807938.832, 247807939.132])
    self.assertTrue(np.all(start_time_test_set == test_start_times[0:4]))
    self.assertTrue(isinstance(start_time_test_set, np.ndarray))

    # Test dicts_by_row()
    rowdict = test_table_secs.dicts_by_row()
    for i in range(4):
        self.assertEqual(rowdict[i]["START_TIME"], start_time_test_set[i])

    rowvals = test_table_secs.get_column("START_TIME")
    rowmask = test_table_secs.get_column_mask("START_TIME")
    for i in range(10):
        self.assertEqual(rowdict[i]["START_TIME"], rowvals[i])
        self.assertFalse(rowmask[i])

    ####################################
    # Invalids
    ####################################

    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648]})

    rowdict = test_table_secs.dicts_by_row()
    for key in test_table.get_keys():
        if key.endswith('_mask'): continue

        rowmasks = test_table_secs.get_column_mask(key)
        self.assertFalse(np.any(rowmasks))
        self.assertTrue(isinstance(rowmasks, np.ndarray))

    results = {
        'BIAS_STRIP_MEAN': 0,
        'COMMAND_SEQUENCE_NUMBER': 0,
        'DARK_STRIP_MEAN': 0,
        'DETECTOR_TEMPERATURE': 0,
        'ELECTRONICS_BIAS': 0,
        'EXPECTED_PACKETS': 0,
        'EXPOSURE_DURATION': 0,
        'FILTER_TEMPERATURE': 0,
        'INSTRUMENT_DATA_RATE': 0,
        'INST_CMPRS_RATIO': 0,
        'MISSING_LINES': 1102,
        'ORDER_NUMBER': 0,
        'PARALLEL_CLOCK_VOLTAGE_INDEX': 0,
        'PREPARE_CYCLE_INDEX': 0,
        'READOUT_CYCLE_INDEX': 0,
        'RECEIVED_PACKETS': 0,
        'SENSOR_HEAD_ELEC_TEMPERATURE': 0,
        'SEQUENCE_NUMBER': 0,
        'SPACECRAFT_CLOCK_CNT_PARTITION': 0,
        'START_TIME': 0,
        'CENTRAL_BODY_DISTANCE': 0,
        'DECLINATION': 0,
        'EMISSION_ANGLE': 1563,
        'INCIDENCE_ANGLE': 1563,
        'LOWER_LEFT_LATITUDE': 3426,
        'LOWER_LEFT_LONGITUDE': 3426,
        'LOWER_RIGHT_LATITUDE': 3279,
        'LOWER_RIGHT_LONGITUDE': 3279,
        'MAXIMUM_RING_RADIUS': 110,
        'MINIMUM_RING_RADIUS': 110,
        'NORTH_AZIMUTH_CLOCK_ANGLE': 1563,
        'PHASE_ANGLE': 236,
        'PIXEL_SCALE': 236,
        'RIGHT_ASCENSION': 0,
        'RING_CENTER_LATITUDE': 3612,
        'RING_CENTER_LONGITUDE': 3612,
        'RING_EMISSION_ANGLE': 3612,
        'RING_INCIDENCE_ANGLE': 3612,
        'SUB_SOLAR_LATITUDE': 236,
        'SUB_SOLAR_LONGITUDE': 236,
        'SUB_SPACECRAFT_LATITUDE': 236,
        'SUB_SPACECRAFT_LONGITUDE': 236,
        'CENTER_LATITUDE': 1563,
        'CENTER_LONGITUDE': 1563,
        'TARGET_DISTANCE': 236,
        'TARGET_EASTERNMOST_LONGITUDE': 1006,
        'TARGET_NORTHERNMOST_LATITUDE': 1006,
        'TARGET_SOUTHERNMOST_LATITUDE': 1006,
        'TARGET_WESTERNMOST_LONGITUDE': 1006,
        'TWIST_ANGLE': 0,
        'UPPER_LEFT_LATITUDE': 3144,
        'UPPER_LEFT_LONGITUDE': 3144,
        'UPPER_RIGHT_LATITUDE': 3102,
        'UPPER_RIGHT_LONGITUDE': 3102,
    }

    rowdict = test_table_secs.dicts_by_row()
    for key in test_table_secs.get_keys():
        if key.endswith('_mask'): continue

        rowvals = test_table.get_column(key)
        if np.shape(rowvals[0]) != (): continue

        rowmask = test_table.get_column_mask(key)
        if rowvals.dtype.kind == 'f':
            countv = np.sum(rowvals == -1.e32)
            countm = np.sum(rowmask)
            self.assertEqual(countv, countm)
            self.assertEqual(countv, results[key])

        elif rowvals.dtype.kind == 'i':
            countv = np.sum(rowvals == -2147483648)
            countm = np.sum(rowmask)
            self.assertEqual(countv, countm)
            self.assertEqual(countv, results[key])

        else:
            self.assertEqual(np.sum(rowmask), 0)

    # 22.5 is a common value in column BIAS_STRIP_MEAN
    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648, 22.5]})

    key = 'BIAS_STRIP_MEAN'
    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648], key: 22.5})

    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    ####################################
    # Replacements
    ####################################

    # Replacement as a number
    key = 'BIAS_STRIP_MEAN'
    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648]},
                          replacements={key: {22.5: -1.e32}})
    rowvals = test_table.get_column(key)
    self.assertEqual(np.sum(rowvals == 22.5), 0)
    self.assertEqual(np.sum(rowvals == -1.e32), 511)

    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    # Replacement as a string
    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648]},
                          replacements={key: {'       22.5': '     -1.e32'}})
    rowvals = test_table.get_column(key)
    self.assertEqual(np.sum(rowvals == 22.5), 0)
    self.assertEqual(np.sum(rowvals == -1.e32), 511)

    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    # Replacement via a callback
    def test_callback_as_str(arg):
        if arg.strip() == '22.5': return '-1e32'
        return arg

    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648]},
                          callbacks={key: test_callback_as_str})
    rowvals = test_table.get_column(key)
    self.assertEqual(np.sum(rowvals == 22.5), 0)
    self.assertEqual(np.sum(rowvals == -1.e32), 511)

    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    # Replacement via an ASCII byte string callback
    def test_callback_as_bytes(arg):
        if arg.strip() == b'22.5': return b'-1e32'
        return arg

    test_table = PdsTable(INDEX_PATH, times=['START_TIME'],
                          invalid={'default': [-1.e32, -2147483648]},
                          callbacks={key: test_callback_as_bytes}, ascii=True)
    rowvals = test_table.get_column(key)
    self.assertEqual(np.sum(rowvals == 22.5), 0)
    self.assertEqual(np.sum(rowvals == -1.e32), 511)

    rowmask = test_table.get_column_mask(key)
    self.assertEqual(np.sum(rowmask), 511)

    ####################################
    # "UNK" values replace 22.5 in BIAS_STRIP_MEAN
    # "NULL" in second row of table for CALIBRATION_LAMP_STATE_FLAG
    # "UNK" in the first row for IMAGE_MID_TIME
    # Label says INVALID_CONSTANT = 19.5 for DARK_STRIP_MEAN
    # Label says VALID_RANGE = (2,3) for INST_CMPRS_RATE
    # Manually disallow negative values for FILTER_TEMPERATURE
    # Every value of INSTRUMENT_DATA_RATE is exactly 182.783997 except one.
    ####################################

#     print('')
#     print('Two UserWarnings should follow...')
#     print('')
#     print('25 illegally formatted float values in column BIAS_STRIP_MEAN; ' +
#           'first example is "UNK"')
#     print('Illegally formatted time value in column IMAGE_MID_TIME: UNK')
#     print('')

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        test_table = PdsTable(EDITED_INDEX_PATH, times=['IMAGE_MID_TIME'],
                              invalid={'default': [-1.e32, -2147483648]},
                              replacements={'INSTRUMENT_DATA_RATE':
                                            {182.783997: 1.}},
                              valid_ranges={'FILTER_TEMPERATURE': [0., 1.e99]})

#     print('')
#     print('')

    image_mid_time = test_table.get_column('IMAGE_MID_TIME')
    bias_strip_mean = test_table.get_column('BIAS_STRIP_MEAN')
    self.assertEqual(type(image_mid_time), list)
    self.assertEqual(type(image_mid_time), list)

    self.assertEqual(image_mid_time[0], 'UNK')
    self.assertEqual(type(image_mid_time[0]), str)
    for value in image_mid_time[1:]:
        self.assertTrue(isinstance(value, float))

    for value in bias_strip_mean:
        self.assertTrue((value == 'UNK') or isinstance(value, float))

    dark_strip_mean = test_table.get_column('DARK_STRIP_MEAN')
    dsm_mask = test_table.get_column_mask('DARK_STRIP_MEAN')
    for (value, flag) in zip(dark_strip_mean, dsm_mask):
        self.assertTrue(flag == (value == 19.5))

    inst_cmprs_rate = test_table.get_column('INST_CMPRS_RATE')
    icr_mask = test_table.get_column_mask('INST_CMPRS_RATE')
    for (value, flag) in zip(inst_cmprs_rate, icr_mask):
        self.assertTrue(flag[0] == (value[0] < 2 or value[0] > 3))
        self.assertTrue(flag[1] == (value[1] < 2 or value[1] > 3))

    filter_temperature = test_table.get_column('FILTER_TEMPERATURE')
    ft_mask = test_table.get_column_mask('FILTER_TEMPERATURE')
    for (value, flag) in zip(filter_temperature, ft_mask):
        self.assertTrue(flag == (value < 0.))

    instrument_data_rate = test_table.get_column('INSTRUMENT_DATA_RATE')
    idr_mask = test_table.get_column_mask('INSTRUMENT_DATA_RATE')
    self.assertTrue(np.sum(instrument_data_rate == 1.) == 99)
    self.assertTrue(np.all(instrument_data_rate != 182.783997))
    self.assertTrue(not np.any(idr_mask))

    ####################################
    # Row lookups
    ####################################

    self.assertEqual(test_table_basic.filespec_column_index(), 1)
    self.assertEqual(test_table_basic.volume_column_index(), 2)

    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            '', 'data/1573186009_1573197826/N1573186041_1.IMG'), 2)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            '', 'data/1573186009_1573197826/N1573186041_1.IMG'), [2])

    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            'COISS_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), 2)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            'COISS_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), [2])

    self.assertEqual(test_table_basic.find_row_index_by_volume_filespec(
            'coiss_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), 2)
    self.assertEqual(test_table_basic.find_row_indices_by_volume_filespec(
            'coiss_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), [2])

    ####################################
    # Row ranges
    ####################################

    partial_table = PdsTable(INDEX_PATH, row_range=(2,4))
    self.assertEqual(partial_table.rows, 2)

    self.assertEqual(partial_table.filespec_column_index(), 1)
    self.assertEqual(partial_table.volume_column_index(), 2)

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            '', 'data/1573186009_1573197826/N1573186041_1.IMG'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            '', 'data/1573186009_1573197826/N1573186041_1.IMG'), [0])

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            'COISS_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            'COISS_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), [0])

    self.assertEqual(partial_table.find_row_index_by_volume_filespec(
            'coiss_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), 0)
    self.assertEqual(partial_table.find_row_indices_by_volume_filespec(
            'coiss_2039', 'data/1573186009_1573197826/N1573186041_1.IMG'), [0])

    ####################################
    # PdsLabel input option
    ####################################

    test = PdsTable(INDEX_PATH, label_contents=partial_table.pdslabel)
    self.assertTrue(test.pdslabel is partial_table.pdslabel)
