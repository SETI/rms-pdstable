################################################################################
# UNIT TESTS
################################################################################

from pathlib import Path
import unittest

import numpy as np

from pdstable import PdsTable


class Test_Pds4Table(unittest.TestCase):

    def runTest(self):

        INDEX_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'
        #######################################################################
        # Test csv table
        #######################################################################
        # CSV_TABLE_FILE_NAME =
        #   'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv'
        CSV_TABLE_FILE_ORDER = 6
        test_csv_table_basic = PdsTable(label_file=INDEX_PATH,
                                        table_file=CSV_TABLE_FILE_ORDER)

        cwd = Path.cwd()

        self.assertEqual(test_csv_table_basic.label_file_name,
                         INDEX_PATH.split('/')[-1])
        self.assertEqual(test_csv_table_basic.label_file_path, cwd / INDEX_PATH)
        self.assertEqual(test_csv_table_basic.table_file_name,
                         'uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv')
        self.assertEqual(test_csv_table_basic.table_file_path,
                         cwd /
                         ('test_files/uranus_occultation_ring_fit_rfrench_'
                          'input_stars_20201201.csv'))
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

        #########################################################################
        # Test table_file pointing to a file not a table
        #########################################################################
        error_msg = 'No Table type found for'
        try:
            _ = PdsTable(label_file=INDEX_PATH, table_file=2)
        except ValueError as e:
            self.assertIn(error_msg, str(e),
                          f'"{error_msg}" NOT in error messages: "{str(e)}"')

        try:
            _ = PdsTable(label_file=INDEX_PATH,
                         table_file='uranus_occultation_ring_fit_rfrench_20201201.txt')
        except ValueError as e:
            self.assertIn(error_msg, str(e),
                          f'"{error_msg}" NOT in error messages: "{str(e)}"')

        #########################################################################
        # Test PdsTable instantiation without specifying a valid table name if
        # multiple tables are available
        #########################################################################
        table_files = (
            "uranus_occultation_ring_fit_rfrench_20201201.tab, "
            "uranus_occultation_ring_fit_rfrench_20201201.txt, "
            "uranus_occultation_ring_fit_rfrench_input_data_20201201.tab, "
            "uranus_occultation_ring_fit_rfrench_input_events_20201201.tab, "
            "uranus_occultation_ring_fit_rfrench_input_observatories_20201201.tab, "
            "uranus_occultation_ring_fit_rfrench_input_stars_20201201.csv"
        )
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
        error_msg = 'Cannot specify row range for the table without fixed length rows'
        try:
            partial_table = PdsTable(label_file=INDEX_PATH,
                                     row_range=(2, 4),
                                     table_file=CSV_TABLE_FILE_ORDER)
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
                                 row_range=(2, 4),
                                 table_file=TAB_TABLE_FILE_NAME)
        self.assertEqual(partial_table.rows, 2)

        self.assertEqual(partial_table.filespec_column_index(), -1)
        self.assertEqual(partial_table.volume_column_index(), -1)

        self.assertEqual(partial_table.find_row_index(**{'Ring name': 'four'}), 0)
        self.assertEqual(partial_table.find_row_index(**{'Ring name': 'alpha'}), 1)

        ####################################
        # PdsLabel input option
        ####################################
        # For PDS4, we store the label dictionary instead of pdsparser.PdsLabel
        # in ._label; therefore we use "==" here instead of "is"
        test = PdsTable(label_file=INDEX_PATH,
                        label_contents=partial_table.pdslabel,
                        table_file=TAB_TABLE_FILE_NAME)
        self.assertTrue(test.pdslabel == partial_table.pdslabel)

        #################################### Invalids
        ####################################
        # A dictionary stores the invalid results of each column at different rows in
        # table: uranus_occultation_ring_fit_rfrench_20201201.tab
        # key is the column name, and value is the number of invalid results in that
        # column.
        cols_with_invalid_results = {
            'Ring name': 0,
            'Semimajor axis': 0,
            'Semimajor axis uncertainty': 0,
            'Eccentricity': 0,
            'Eccentricity uncertainty': 0,
            'Periapse longitude': 0,
            'Periapse uncertainty': 0,
            'Periapse precession rate': 0,
            'Periapse precession rate uncertainty': 1,
            'Periapse precession rate method': 0,
            'Inclination': 0,
            'Inclination uncertainty': 0,
            'Node longitude': 0,
            'Node uncertainty': 0,
            'Nodal regression rate': 0,
            'Nodal regression rate uncertainty': 6,
            'Nodal regression rate method': 0,
            'Wavenumber': 6,
            'Normal mode amplitude': 6,
            'Normal mode amplitude uncertainty': 6,
            'Normal mode phase': 6,
            'Normal mode phase uncertainty': 6,
            'Normal mode pattern speed': 6,
            'Normal mode pattern speed uncertainty': 6,
            'Number of points (Npts)': 0,
            'RMS': 0,
        }

        test_table = PdsTable(label_file=INDEX_PATH, table_file=TAB_TABLE_FILE_NAME)

        rowdict = test_table.dicts_by_row()
        for key in test_table.get_keys():
            if key.endswith('_mask'):
                continue
            rowmasks = test_table.get_column_mask(key)

            if cols_with_invalid_results[key] != 0:
                self.assertTrue(np.any(rowmasks))
            else:
                self.assertFalse(np.any(rowmasks))
            self.assertTrue(isinstance(rowmasks, np.ndarray))

        # rowdict = test_table.dicts_by_row()
        for key in test_table.get_keys():
            if key.endswith('_mask'):
                continue

            rowvals = test_table.get_column(key)
            if np.shape(rowvals[0]) != ():
                continue

            rowmask = test_table.get_column_mask(key)

            if cols_with_invalid_results[key] != 0:
                if rowvals.dtype.kind == 'i':
                    # Wavenumber
                    countv = np.sum(rowvals == -999)
                    self.assertEqual(countv, cols_with_invalid_results[key])
                else:
                    # Rest of columns that have invalid values
                    countv = np.sum(rowvals == -9.99e+99)
                    self.assertEqual(countv, cols_with_invalid_results[key])
            else:
                # columns without invalid values in the table
                countv = 0

            countm = np.sum(rowmask)
            self.assertEqual(countv, countm)

        # 3.0377050292398E-04 appears 4 times in column 'Inclination'
        test_table = PdsTable(label_file=INDEX_PATH,
                              invalid={'default': [3.0377050292398E-04]},
                              table_file=TAB_TABLE_FILE_NAME)
        key = 'Inclination'
        rowmask = test_table.get_column_mask(key)
        self.assertEqual(np.sum(rowmask), 4)

        test_table = PdsTable(label_file=INDEX_PATH,
                              invalid={'default': [3.0377050292398E-04],
                                       key: 3.0377050292398E-04},
                              table_file=TAB_TABLE_FILE_NAME)

        rowmask = test_table.get_column_mask(key)
        self.assertEqual(np.sum(rowmask), 4)

        ####################################
        # Replacements
        ####################################

        # Replacement as a number
        key = 'Inclination'
        test_table = PdsTable(label_file=INDEX_PATH,
                              invalid={'default': [3.0377050292398E-04, -1.e32]},
                              replacements={key: {3.0377050292398E-04: -1.e32}},
                              table_file=TAB_TABLE_FILE_NAME)

        # replace 3.0377050292398E-04 with -1.e32
        rowvals = test_table.get_column(key)
        self.assertEqual(np.sum(rowvals == 3.0377050292398E-04), 0)
        self.assertEqual(np.sum(rowvals == -1.e32), 4)

        # still 4 invalid values because we put -1.e32 in invalid
        rowmask = test_table.get_column_mask(key)
        self.assertEqual(np.sum(rowmask), 4)

        # Replacement as a string
        test_table = PdsTable(label_file=INDEX_PATH,
                              invalid={'default': [3.0377050292398E-04, -1.e32]},
                              replacements={key: {'  3.0377050292398E-04': '  -1.e32'}},
                              table_file=TAB_TABLE_FILE_NAME)

        rowvals = test_table.get_column(key)
        self.assertEqual(np.sum(rowvals == 3.0377050292398E-04), 0)
        self.assertEqual(np.sum(rowvals == -1.e32), 4)

        rowmask = test_table.get_column_mask(key)
        self.assertEqual(np.sum(rowmask), 4)

        # Replacement via a callback
        def test_callback_as_str(arg):
            if arg.strip() == '3.0377050292398E-04':
                return '-1e32'
            return arg

        test_table = PdsTable(label_file=INDEX_PATH,
                              invalid={'default': [3.0377050292398E-04, -1.e32]},
                              callbacks={key: test_callback_as_str},
                              table_file=TAB_TABLE_FILE_NAME)

        rowvals = test_table.get_column(key)
        self.assertEqual(np.sum(rowvals == 3.0377050292398E-04), 0)
        self.assertEqual(np.sum(rowvals == -1.e32), 4)

        rowmask = test_table.get_column_mask(key)
        self.assertEqual(np.sum(rowmask), 4)
