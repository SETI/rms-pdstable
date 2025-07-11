#!/usr/bin/python
################################################################################
# pdstable.py
#
# Classes and methods to deal with PDS index and table files
#
# Mark R. Showalter, SETI Institute, December 2011
# Revised December 22, 2011 (BSW) - add ability to read, parse, and return data
#                                   that take multiple columns
# Revised December 23, 2011 (BSW) - add adaptation to seconds for TIME fields
# Revised January 3, 2012 (BSW) - changed conversion to floats to happen in one
#                                 step for entire column of TIMEs
#                               - fixed parsing of vectors that were not getting
#                                 all 3 values
#                               - implemented unit tests
#
# Revised 1/11/12 (MRS) - Added PdsTable methods dicts_by_row() and
#                         dicts_by_key(). The former is used by
#                         instrument.cassini.iss.
# Revised 1/17/12 (BSW) - Fixed ordering of values when PdsTable __init__ has
#                         more than one column indicated in the time_format_list
# 6/14/12 MRS - Added column selections in PdsTable() to reduce memory usage;
#   added a callback option to PdsTable() for repairing the values in a table
#   prior to other processing.
# 8/20/12 MRS - A warning now is raised when a column of a table contains one or
#   more badly-formatted entries. The column values are left in string format.
# 4/2/19 MRS & RSF - Many revisions:
#   - Compatible with Python 3. Strings returned are now of the standard str
#     type Python 2 (one-byte ASCII) and in Python 3 (4-byte Unicode).
#   - Still quite fast, because all operations that can be handled via array
#     operations are still handled via array operations.
#   - Each returned column now has an associated boolean mask that identifies
#     invalid values.
#   - Values in the PDS3 label that identify the valid range or that identify
#     invalid, missing, etc. values are used to populate each column's mask.
#   - New input options for replacements, invalid values and valid ranges can be
#     specified for each column. These can be used to augment information in the
#     in the PDS3 label.
#   - Invalid values (e.g., -1.e32) can also be defined globally.
#   - Lots of new unit tests.
# 3/15/20 MRS - Added row_range option for quick access to a few rows of an
#   index.
################################################################################

import sys
import os
import datetime as dt
import warnings
import numpy as np
import numbers

from pdsparser import Pds3Label
import julian

try:
    from ._version import __version__
except ImportError as err:
    __version__ = 'Version unspecified'


# STR_DTYPE is 'S' for Python 2; 'U' for Python 3
STR_DTYPE = np.array(['x']).dtype.kind
PYTHON2 = (sys.version_info[0] == 2)
PYTHON3 = not PYTHON2

if PYTHON3:
    ENCODING = {'encoding': 'latin-1'}  # For open() of ASCII files in Python 3
else:
    ENCODING = {}

# This is an exhaustive tuple of string-like types
STRING_TYPES = (str, bytes, bytearray, np.str_, np.bytes_)

# Needed because the default value of strip is False
def tai_from_iso(string):
    return julian.tai_from_iso(string, strip=True)

FILE_SPECIFICATION_COLUMN_NAMES = (
    'FILE_SPECIFICATION_NAME',
    'FILE SPECIFICATION NAME',
    'FILE_NAME',
    'FILE NAME',
    'FILENAME',
    'PRODUCT_ID',
    'PRODUCT ID',
    'STSCI_GROUP_ID'
)

FILE_SPECIFICATION_COLUMN_NAMES_lc = [x.lower() for x in
                                      FILE_SPECIFICATION_COLUMN_NAMES]

VOLUME_ID_COLUMN_NAMES = (
    'VOLUME_ID',
    'VOLUME ID',
    'VOLUME_NAME',
    'VOLUME NAME'
)

VOLUME_ID_COLUMN_NAMES_lc = [x.lower() for x in VOLUME_ID_COLUMN_NAMES]

class PdsTable(object):
    """The PdsTable class holds the contents of a PDS-labeled table. It is
    represented by a list of Numpy arrays, one for each column.

    Current limitations:
        (1) ASCII tables only, no binary formats.
        (2) Detached PDS labels only.
        (3) Only one data file per label.
        (4) No row or record offsets in the label's pointer to the table file.
        (5) STRUCTURE fields in the label are not supported.
        (6) Columns containing multiple items are not loaded. MUST BE FIXED.
        (7) Time fields are represented as character strings at this stage.
    """

    def __init__(self, label_file, label_contents=None, times=[], columns=[],
                       nostrip=[], callbacks={}, ascii=False, replacements={},
                       invalid={}, valid_ranges={}, table_callback=None,
                       merge_masks=False, filename_keylen=0, row_range=None,
                       label_method='strict'):
        """Constructor for a PdsTable object.

        Input:
            label_file      the path to the PDS label of the table file. Must be
                            supplied to get proper relative path resolution.
            label_contents  The contents of the label as a list of strings if
                            we shouldn't read it from the file. Alternatively, a
                            Pds3Label object to avoid label parsing entirely.
            columns         an optional list of the names of the columns to
                            return. If the list is empty, then every column is
                            returned.
            times           an optional list of the names of time columns to be
                            stored as floats in units of seconds TAI rather than
                            as strings.
            nostrip         an optional list of the names of string columns that
                            are not to be stripped of surrounding whitespace.
            callbacks       an optional dictionary that returns a callback
                            function given the name of a column. If a callback
                            is provided for any column, then the function is
                            called on the string value of that column before it
                            is parsed. This can be used to update known syntax
                            errors in a particular table.
            ascii           True to interpret the callbacks as translating
                            ASCII byte strings; False to interpret them as
                            translating the default str type, which is 1-byte
                            ASCII in Python 2 but 4-byte Unicode in Python 3.
                            This parameter is ignored in Python 2.
            replacements    an optional dictionary that returns a replacement
                            dictionary given the name of a column. If a
                            replacement dictionary is provided for any column,
                            then any value in that column (as a string or as its
                            native value) that matches a key in the dictionary
                            is replaced by the value resulting from the
                            dictionary lookup.
            invalid         an optional dictionary keyed by column name. The
                            returned value must be a list or set of values that
                            are to be treated as invalid, missing or unknown.
                            An optional entry keyed by "default" can be a list
                            or set of values that are invalid by default; these
                            are used for any column whose name does not apppear
                            as a key in the dictionary.
            valid_ranges    an optional dictionary keyed by column name. The
                            returned value must be a tuple or list containing
                            the minimum and maximum numeric values in that
                            column.
            table_callback  an optional function to be called after reading
                            the data table contents before processing them. Note
                            that this callback must handle bytestrings in Python
                            3.
            merge_masks     True to return a single mask value for each column,
                            regardless of how many items might be in that
                            column. False to return a separate mask value for
                            each value in a column.
            filename_keylen number of characters in the filename to use as the
                            key of the index if this table is to be indexed by
                            filename. Zero to use the entire file basename after
                            stripping off the extension.
            row_range       a tuple or list integers containing the index of the
                            first row to read and the first row to omit. If not
                            specified, then all the rows are read.
            label_method    the method to use to parse the label. Valid values
                            are 'strict' (default) or 'fast'. The 'fast' method
                            is faster but may not be as accurate.

        Notes: If both a replacement and a callback are provided for the same
        column, the callback is applied first. The invalid and valid_ranges
        parameters are applied afterward.

        Note that, in Python 3, performance will be slightly faster if
        ascii=True.
        """

        # Parse the label
        self.info = PdsTableInfo(label_file, label_list=label_contents,
                                 invalid=invalid, valid_ranges=valid_ranges,
                                 label_method=label_method)

        # Select the columns
        if len(columns) == 0:
            self.keys = [info.name for info in self.info.column_info_list]
        else:
            self.keys = columns
        # self.keys is an ordered list containing the name of every column to be
        # returned

        self.keys_lc = [k.lower() for k in self.keys]

        # Load the table data in binary
        if row_range is None:
            self.first = 0
            self.rows = self.info.rows

            with open(self.info.table_file_path, "rb") as f:
                lines = f.readlines()

            # Check line count
            if len(lines) != self.info.rows:
                raise ValueError('row count mismatch in %s: ' % label_file +
                                 '%d rows in file; ' % len(lines) +
                                 'label says ROWS = %d' % self.info.rows)

        else:
            self.first = row_range[0]
            self.rows = row_range[1] - row_range[0]

            record_bytes = self.info.label['RECORD_BYTES']
            with open(self.info.table_file_path, "rb") as f:
                f.seek(row_range[0] * record_bytes)
                lines = f.readlines(self.rows * record_bytes - 1)

            # Check line count
            if len(lines) > self.rows:
                lines = lines[:self.rows]

            if len(lines) != self.rows:
                raise ValueError(
                    'row count mismatch: ' +
                    '%d row%s read; ' % (len(lines),
                                        '' if len(lines) == 1 else 's') +
                    '%d row%s requested' % (count,
                                            '' if count == 1 else 's'))

        if table_callback is not None:
            lines = table_callback(lines)

        table = np.array(lines, dtype='S')
        try:
            table.dtype = np.dtype(self.info.dtype0)
        except ValueError:
            raise ValueError('Error in PDS3 row description:\n' +
                             'old dtype = ' + str(table.dtype) +
                             ';\nnew dtype = ' + str(np.dtype(self.info.dtype0)))
        # table is now a 1-D array in which the ASCII content of each column
        # can be accessed by name. In Python 3, these are bytes, not strings

        # Extract the substring arrays and save in a dictionary...
        self.column_values = {}
        self.column_masks = {}
        for key in self.keys:
            column_info = self.info.column_info_dict[key]
            column = table[key]
            # column is now a 1-D array containing the ASCII content of this
            # column within each row.

            # For multiple items...
            if column_info.items > 1:

                # Replace the column substring with a list of sub-substrings
                column.dtype = np.dtype(column_info.dtype1)

                items = []
                masks = []
                for i in range(column_info.items):
                    item = column["item_" + str(i)]
                    items.append(item)
                    masks.append(False)
                # items is now a list containing one 1-D array for each item in
                # this column.

                self.column_values[key] = items

            else:
                self.column_values[key] = [column]

        # self.column_values now contains a list with one element for each item
        # in that column. Each element is a 1-D array of ASCII strings, one for
        # each row.

        if STR_DTYPE == 'S': ascii = False

        # Replace each 1-D array of items from ASCII strings to the proper type
        for key in self.keys:
            column_info  = self.info.column_info_dict[key]
            column_items = self.column_values[key]

            data_type = column_info.data_type
            dtype     = column_info.dtype2
            func      = column_info.scalar_func
            callback  = callbacks.get(key, None)
            repdict   = replacements.get(key, {})
            strip     = (key not in nostrip)

            invalid_values = column_info.invalid_values
            valid_range    = column_info.valid_range

            error_count    = 0
            error_example  = None

            # For each item in the column...
            new_column_items = []
            new_column_masks = []
            for items in column_items:
                invalid_mask = np.zeros(len(items), dtype='bool')

                # Apply the callback if any
                if callback:

                    # Convert string to input format for callback
                    if PYTHON3 and not ascii:
                       items = items.astype(STR_DTYPE)

                    # Apply the callback row by row
                    new_items = []
                    for item in items:
                        new_item = callback(item)
                        new_items.append(new_item)

                    items = np.array(new_items)

                # Apply the replacement dictionary if any pairs are strings
                for (before, after) in repdict.items():
                    if not isinstance(before, STRING_TYPES): continue
                    if not isinstance(after,  STRING_TYPES): continue

                    # The file is read as binary, so the replacements have
                    # to be applied as ASCII byte strings

                    if PYTHON3 and isinstance(before, (str, np.str_)):
                        before = before.encode(**ENCODING)

                    if PYTHON3 and isinstance(after, (str, np.str_)):
                        after  = after.encode(**ENCODING)

                    # Replace values (suppressing FutureWarning)
                    items = items.astype('S')
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        items[items == before] = after

                # Handle the data type...

                # Handle a string
                if data_type == 'string' or (data_type == 'time' and
                                             key not in times):
                    items = items.astype(STR_DTYPE)

                    if strip:
                        items = [i.strip() for i in items]
                        items = np.array(items)

                # If this is an int, float or time...

                # Try to convert array dtype
                else:
                    try:
                        items = items.astype(dtype)

                        # Apply the replacements for pairs of this type
                        for (before, after) in repdict.items():
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                items[items == before] = after

                        # Convert times if necessary
                        if key in times:
                            items = tai_from_iso(items)

                    # If something went wrong, array processing won't work.
                    # Convert to list and process row by row
                    except Exception:

                        # Process row by row
                        new_items = []
                        for k in range(len(items)):
                            item = items[k]
                            try:
                                # Translate the item
                                item = func(item)

                                # Apply a possible replacement
                                item = repdict.get(item, item)

                            # If something went wrong...
                            except Exception:
                                invalid_mask[k] = True

                                error_count += 1
                                if not isinstance(item, str):
                                    item = item.decode(**ENCODING)

                                if strip:
                                    item = item.strip()

                                if error_example is None:
                                    error_example = item

                            # Apply validity criteria to this row
                            invalid_mask[k] |= (item in invalid_values)
                            if valid_range:
                                invalid_mask[k] |= (item < valid_range[0])
                                invalid_mask[k] |= (item > valid_range[1])

                            new_items.append(item)

                        items = new_items

                # Determine validity mask if not already done
                if type(items) == np.ndarray:
                    for invalid_value in invalid_values:

                        # Hide FutureWarning for comparisons of different types
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            invalid_mask |= (items == invalid_value)

                    if valid_range:

                        # Hide FutureWarning for comparisons of different types
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            invalid_mask |= (items < valid_range[0])
                            invalid_mask |= (items > valid_range[1])

                new_column_items.append(items)
                new_column_masks.append(invalid_mask)

            # Swap indices for multiple items
            if len(new_column_items) == 1:
                self.column_values[key] = new_column_items[0]
                self.column_masks[key]  = new_column_masks[0]

            else:
                theyre_all_arrays = np.all([type(c) == np.ndarray
                                            for c in new_column_items])

                if theyre_all_arrays:
                    array = np.stack(new_column_items, axis=1)
                    if array.dtype.kind in ('S', 'U'):
                        array = [tuple(x) for x in array]
                    self.column_values[key] = array
                else:
                    self.column_values[key] = list(zip(*new_column_items))

                if merge_masks:
                    self.column_masks[key] = np.any(np.stack(new_column_masks),
                                                    axis=0)
                else:
                    mask_array = np.stack(new_column_masks)
                    self.column_masks[key] = mask_array.swapaxes(0,1)

            # Report errors as warnings
            if error_count:
                if error_count == 1:
                    template = 'Illegally formatted %s value in column %s: %s'
                else:
                    template = (str(error_count) +
                                ' illegally formatted %s values in column ' +
                                '%s; first example is "%s"')

                warnings.warn(template % (column_info.data_type,
                                          column_info.name,
                                          error_example.strip()))

        # Cache dicts_by_row and other info when first requested
        self.filename_keylen = filename_keylen
        self._dicts_by_row = {}

        self._volume_colname_index   = None
        self._volume_colname         = None
        self._volume_colname_lc      = None

        self._filespec_colname_index = None
        self._filespec_colname       = None
        self._filespec_colname_lc    = None

        self._rows_by_filename = None
        self.filename_keys     = None

    @property
    def pdslabel(self):
        """Property to return the Pds3Label object, so that it can be used as a
        label_contents input parameter in subsequent calls."""

        return self.info.label

    ############################################################################
    # Support for extracting rows and columns
    ############################################################################

    def dicts_by_row(self, lowercase=(False,False)):
        """Returns a list of dictionaries, one for each row in the table, and
        with each dictionary containing all of the column values in that
        particular row. The dictionary keys are the column names; append "_mask"
        to the key to get the mask value, which is True if the column value is
        invalid; False otherwise.

        Input parameter lowercase is a tuple of two booleans. If the first is
        True, then the dictionary is also keyed by column names converted to
        lower case. If the second is True, then keys with "_lower" appended
        return values converted to lower case.
        """

        # Duplicate the lowercase value if only one is provided
        if type(lowercase) == bool:
            lowercase = (lowercase, lowercase)

        # If we already have the needed list of dictionaries, return it
        try:
            return self._dicts_by_row[lowercase]
        except KeyError:
            pass

        # For each row...
        row_dicts = []
        for row in range(self.rows):

            # Create and append the dictionary
            row_dict = {}
            for (column_name, items) in self.column_values.items():
              for key in set([column_name, column_name.replace(' ', '_')]):
                value = items[row]
                mask  = self.column_masks[key][row]

                # Key and value unchanged
                row_dict[key] = value
                row_dict[key + "_mask"] = mask

                # Key in lower case; value unchanged
                if lowercase[0]:
                    key_lc = key.lower()
                    row_dict[key_lc] = value
                    row_dict[key_lc + "_mask"] = mask

                # Value in lower case
                if lowercase[1]:
                    value_lc = lowercase_value(value)

                    row_dict[key + '_lower'] = value_lc
                    if lowercase[0]:
                        row_dict[key_lc + '_lower'] = value_lc

            row_dicts.append(row_dict)

        # Cache results for later re-use
        self._dicts_by_row[lowercase] = row_dicts

        return row_dicts

    def get_column(self, name):
        """Return the values in the specified column as a list or 1-D array."""

        return self.column_values[name]

    def get_column_mask(self, name):
        """Return the masks for the specified column as a list or 1-D array."""

        return self.column_masks[name]

    def get_keys(self):
        return list(self.keys)

    ############################################################################
    # Support for finding rows by specified column values
    ############################################################################

    def find_row_indices(self, lowercase=(False,False), limit=None,
                               substrings=[], **params):
        """A list of indices of rows in the table where each named parameter
        equals the specified value.

        Input parameter lowercase is a tuple of two booleans. If the first is
        True, then the dictionary is also keyed by column names converted to
        lower case. If the second is True, then keys with "_lower" appended
        return values converted to lower case.

        If limit is not zero or None, this is the maximum number of matching
        rows that are return.

        Input parameter substrings is a list of column names for which a match
        occurs if the given parameter value is embedded within the string; an
        exact match is not required.
        """

        dicts_by_row = self.dicts_by_row(lowercase=lowercase)

        # Make a list (key, value, test_substring, mask_key)
        test_info = []
        for (key, match_value) in params.items():
            if key.endswith('_lower'):
                mask_key = key[:-6] + '_mask'
                match_value = lowercase_value(match_value)
                test_substring = (key in substrings or key[:-6] in substrings)
            else:
                mask_key = key + '_mask'
                test_substring = (key in substrings)

            test_info.append((key, match_value, test_substring, mask_key))

        matches = []

        # For each row in the table...
        for k in range(len(dicts_by_row)):
            row_dict = dicts_by_row[k]

            # Assume it's a match
            match = True

            # Apply each test...
            for (key, match_value, test_substring, mask_key) in test_info:

                # Reject all masked values
                if np.any(row_dict[mask_key]):
                    match = False
                    break

                # Test column value(s)
                column_values = row_dict[key]
                if test_substring:
                    if isinstance(column_values, str):
                        failures = [match_value not in column_values]
                    else:
                        failures = [match_value not in c for c in column_values]
                elif isinstance(column_values, (str, int, float)):
                    failures = [match_value != column_values]
                else:
                    failures = [match_value != c for c in column_values]

                if np.any(failures):
                    match = False
                    break

            # If there were no failures, we have a match
            if match:
                matches.append(k)
                if limit and len(matches) >= limit:
                    return matches

        return matches

    def find_row_index(self, lowercase=(False,False), substrings=[], **params):
        """The index of the first row in the table where each named parameter
        equals the specified value.

        Input parameter lowercase is a tuple of two booleans. If the first is
        True, then the dictionary is also keyed by column names converted to
        lower case. If the second is True, then keys with "_lower" appended
        return values converted to lower case.
        """

        matches = self.find_row_indices(lowercase=lowercase, limit=1,
                                        substrings=substrings, **params)

        if matches:
            return matches[0]

        raise ValueError('row not found: ' + str(params))

    def find_rows(self, lowercase=(False,False), **params):
        """A list of dictionaries representing rows in the table where each
        named parameter equals the specified value.

        Input parameter lowercase is a tuple of two booleans. If the first is
        True, then the dictionary is also keyed by column names converted to
        lower case. If the second is True, then keys with "_lower" appended
        return values converted to lower case.
        """

        indices = self.find_row_indices(lowercase=lowercase, **params)
        return [self.dicts_by_row()[k] for k in indices]

    def find_row(self, lowercase=(False,False), **params):
        """A dictionary representing the first row of the table where each
        named parameter equals the specified value.

        Input parameter lowercase is a tuple of two booleans. If the first is
        True, then the dictionary is also keyed by column names converted to
        lower case. If the second is True, then keys with "_lower" appended
        return values converted to lower case.
        """

        k = self.find_row_index(lowercase=lowercase, **params)
        return self.dicts_by_row()[k]

    ############################################################################
    # Support for finding rows by filename
    ############################################################################

    def filename_key(self, filename):
        """Convert a filename to a key for indexing the rows. The key is the
        basename with the extension removed."""

        basename = os.path.basename(filename)
        key = os.path.splitext(basename)[0]
        if self.filename_keylen and len(key) > self.filename_keylen:
            key = key[:self.filename_keylen]

        return key

    def volume_column_index(self):
        """The index of the column containing volume IDs, or -1 if none."""

        if self._volume_colname_index is None:
            self._volume_colname_index = -1
            self._volume_colname = ''
            self._volume_colname_lc = ''

            for guess in VOLUME_ID_COLUMN_NAMES_lc:
                if guess in self.keys_lc:
                    k = self.keys_lc.index(guess)
                    self._volume_colname_index = k
                    self._volume_colname_lc = guess
                    self._volume_colname = self.keys[k]
                    return k

        return self._volume_colname_index

    def filespec_column_index(self):
        """The index of the column containing file specification name, or -1 if
        none."""

        if self._filespec_colname_index is None:
            self.filespec_colname_index = -1
            self.filespec_colname = ''
            self.filespec_colname_lc = ''

            for guess in FILE_SPECIFICATION_COLUMN_NAMES_lc:
                if guess in self.keys_lc:
                    k = self.keys_lc.index(guess)
                    self._filespec_colname_index = k
                    self._filespec_colname_lc = guess
                    self._filespec_colname = self.keys[k]
                    return k

        return self._filespec_colname_index

    def find_row_indices_by_volume_filespec(self, volume_id, filespec=None,
                                                  limit=None, substring=False):
        """The row indices of the table with the specified volume_id and
        file_specification_name.

        The search is case-insensitive.

        If the table does not contain the volume ID or if the given value of
        volume_id is blank, the search is performed on the filespec alone,
        ignoring the volume ID. Also, if only one argument is specified, it is
        treated as the filespec.

        The search ignores the extension of filespec so it does not matter
        whether the column contains paths to labels or data files. It also works
        in tables that contain columns of file names without directory paths.

        If input parameter substring is True, then a match occurs whenever the
        given filespec appears inside what is tabulated in the file, so a
        complete match is not required.
        """

        dicts_by_row = self.dicts_by_row(lowercase=(True,True))
        keys = dicts_by_row[0].keys()

        if filespec is None:
            filespec = volume_id
            volume_id = ''

        # Find the name of the columns containing the VOLUME_ID and
        # FILE_SPECIFICATION_NAME
        _ = self.volume_column_index()
        _ = self.filespec_column_index()

        if self._volume_colname is None:
            volume_colname = ''
        else:
            volume_colname = self._volume_colname_lc + '_lower'

        if self._filespec_colname_lc is None:
            raise ValueError('FILE SPECIFICATION NAME column not found')
        else:
            filespec_colname = self._filespec_colname_lc + '_lower'

        # Convert to VMS format for really old indices
        example = dicts_by_row[0][self._filespec_colname_lc]
        if '[' in example:
            parts = filespec.split('/')
            filespec = '[' + '.'.join(parts[:-1]) + ']' + parts[-1]

        # Strip away the directory path if not present
        elif '/' not in example:
            filespec = os.path.basename(filespec)

        # Copy the extension of the example
        filespec = os.path.splitext(filespec)[0]
        if not substring:
            ext = os.path.splitext(example)[1]
            filespec += ext

        # OK now search
        volume_id = volume_id.lower()
        filespec = filespec.lower()
        if substring:
            substrings = [filespec_colname]
        else:
            substrings = []

        if volume_colname and volume_id:
            return self.find_row_indices(lowercase=(True,True),
                                         substrings=substrings, limit=limit,
                                         **{filespec_colname: filespec,
                                            volume_colname: volume_id})
        else:
            return self.find_row_indices(lowercase=(True,True),
                                         substrings=substrings, limit=limit,
                                         **{filespec_colname: filespec})

    def find_row_index_by_volume_filespec(self, volume_id, filespec=None,
                                                substring=False):
        """The row index with the specified volume_id and
        file_specification_name.

        The search is case-insensitive.

        If the table does not contain the volume ID or if the given value of
        volume_id is blank, the search is performed on the filespec alone,
        ignoring the volume ID. Also, if only one argument is specified, it is
        treated as the filespec.

        The search ignores the extension of filespec so it does not matter
        whether the column contains paths to labels or data files. It also works
        in tables that contain columns of file names without directory paths.

        If input parameter substring is True, then a match occurs whenever the
        given filespec appears inside what is tabulated in the file, so a
        complete match is not required.
        """

        indices = self.find_row_indices_by_volume_filespec(volume_id, filespec,
                                                           limit=1,
                                                           substring=substring)
        if indices:
            return indices[0]

        if volume_id and not filespec:
            raise ValueError('row not found: filespec=%s; ' % volume_id)
        elif volume_id:
            raise ValueError('row not found: volume_id=%s; ' % volume_id +
                                            'filespec=%s' % filespec)
        else:
            raise ValueError('row not found: filespec=%s' % filespec)

    def find_rows_by_volume_filespec(self, volume_id, filespec=None,
                                           limit=None, substring=False):
        """The rows of the table with the specified volume_id and
        file_specification_name.

        The search is case-insensitive.

        If the table does not contain the volume ID or if the given value of
        volume_id is blank, the search is performed on the filespec alone,
        ignoring the volume ID. Also, if only one argument is specified, it is
        treated as the filespec.

        The search ignores the extension of filespec so it does not matter
        whether the column contains paths to labels or data files. It also works
        in tables that contain columns of file names without directory paths.

        If input parameter substring is True, then a match occurs whenever the
        given filespec appears inside what is tabulated in the file, so a
        complete match is not required.
        """

        indices = self.find_row_indices_by_volume_filespec(volume_id, filespec,
                                                           limit=limit,
                                                           substring=substring)
        return [self.dicts_by_row()[k] for k in indices]

    def find_row_by_volume_filespec(self, volume_id, filespec=None,
                                          substring=False):
        """The first row of the table with the specified volume_id and
        file_specification_name.

        The search is case-insensitive.

        If the table does not contain the volume ID or if the given value of
        volume_id is blank, the search is performed on the filespec alone,
        ignoring the volume ID. Also, if only one argument is specified, it is
        treated as the filespec.

        The search ignores the extension of filespec so it does not matter
        whether the column contains paths to labels or data files. It also works
        in tables that contain columns of file names without directory paths.

        If input parameter substring is True, then a match occurs whenever the
        given filespec appears inside what is tabulated in the file, so a
        complete match is not required.
        """

        k = self.find_row_index_by_volume_filespec(volume_id, filespec,
                                                   substring=substring)
        return self.dicts_by_row()[k]

    def index_rows_by_filename_key(self):
        """A dictionary of row indices keyed by the file basename associated
        with the row. The key has the file extension stripped away and is
        converted to lower case."""

        if self._rows_by_filename is None:
            _ = self.volume_column_index()
            _ = self.filespec_column_index()

            filespecs = self.column_values[self._filespec_colname]
            masks = self.column_masks[self._filespec_colname]

            rows_by_filename = {}
            filename_keys = []
            for k in range(len(filespecs)):
                if masks[k]: continue

                key = self.filename_key(filespecs[k])
                key_lc = key.lower()
                if key_lc not in rows_by_filename:
                    rows_by_filename[key_lc] = []
                    filename_keys.append(key)

                rows_by_filename[key_lc].append(k)

            self._rows_by_filename = rows_by_filename
            self.filename_keys = filename_keys

    def row_indices_by_filename_key(self, key):
        """Quick lookup of the row indices associated with a filename key."""

        # Create the index if necessary
        self.index_rows_by_filename_key()

        return self._rows_by_filename[key.lower()]

    def rows_by_filename_key(self, key):
        """Quick lookup of the rows associated with a filename key."""

        # Create the index if necessary
        self.index_rows_by_filename_key()

        indices = self._rows_by_filename[key.lower()]

        rows = []
        for k in indices:
            rows.append(self.dicts_by_row()[k])

        return rows

def lowercase_value(value):
    """Convert a table value to lower case. Handles strings and tuples; leaves
    ints and floats unchanged."""

    if isinstance(value, str):
        value_lc = value.lower()
    elif type(value) == tuple:
        value_lc = []
        for item in value:
            if type(item) == str:
                value_lc.append(item.lower())
            else:
                value_lc.append(item)
    elif type(value) == np.ndarray:
        value_lc = value.copy()
        for k in range(len(value)):
            if isinstance(value[k], str):
                value_lc[k] = value[k].lower()
    else:
        value_lc = value

    return value_lc

################################################################################
# Class PdsTableInfo
################################################################################

class PdsTableInfo(object):
    """The PdsTableInfo class holds the attributes of a PDS-labeled table."""

    def __init__(self, label_file_path, label_list=None, invalid={},
                                                         valid_ranges={},
                                                         label_method='strict'):
        """Loads a PDS table based on its associated label file.

        Input:
            label_file_path path to the label file
            label_list      an option to override the parsing of the label.
                            If this is a list, it is interpreted as containing
                            all the records of the PDS label, in which case the
                            overrides the contents of the label file.
                            Alternatively, this can be a Pds3Label object that
                            was already parsed.
            invalid         an optional dictionary keyed by column name. The
                            returned value must be a list or set of values that
                            are to be treated as invalid, missing or unknown.
            valid_ranges    an optional dictionary keyed by column name. The
                            returned value must be a tuple or list containing
                            the minimum and maximum numeric values in that
                            column.
            label_method    the method to use to parse the label. Valid values
                            are 'strict' (default) or 'fast'. The 'fast' method
                            is faster but may not be as accurate.
        """

        # Parse the label
        if isinstance(label_list, (Pds3Label, dict)):
            self.label = label_list
        elif label_list:
            self.label = Pds3Label(label_list, method=label_method)
        else:
            self.label = Pds3Label(label_file_path, method=label_method)

        # Get the basic file info...
        if self.label["RECORD_TYPE"] != "FIXED_LENGTH":
            raise IOError('PDS table does not contain fixed-length records')

        # Find the pointer to the table file
        # Confirm that the value is a PdsSimplePointer
        self.table_file_name = None
        for key, value in self.label.items():
            if key[0] == "^" and key.endswith('TABLE'):
                self.table_file_name = value
                if key + '_offset' in self.label:
                    msg = ("Table file pointer " + self.label[key + '_fmt'] +
                           " is not a Simple Pointer and isn't fully "+
                           "supported")
                    warnings.warn(msg)
                else:
                    self.table_file_name = value
                break

        if self.table_file_name is None:
            raise IOError("Pointer to a data file was not found in PDS label")

        # Locate the root of the table object
        table_dict = self.label[key[1:]]

        # Save key info about the table
        interchange_format = (table_dict.get("INTERCHANGE_FORMAT", '')
                              or table_dict["INTERCHANGE_FORMAT_1"])
        if interchange_format != "ASCII":
            raise IOError('PDS table is not in ASCII format')

        self.rows = table_dict["ROWS"]
        self.columns = table_dict["COLUMNS"]
        self.row_bytes = table_dict["ROW_BYTES"]

        # Save the key info about each column in a list and a dictionary
        self.column_info_list = []
        self.column_info_dict = {}

        # Construct the dtype0 dictionary
        self.dtype0 = {'crlf': ('|S2', self.row_bytes-2)}

        default_invalid = set(invalid.get("default", []))
        counter = 0
        for key, column_dict in table_dict.items():
            if not isinstance(column_dict, dict):
                continue
            if column_dict['OBJECT'] == "COLUMN":
                name = column_dict["NAME"]
                pdscol = PdsColumnInfo(column_dict, counter,
                            invalid = invalid.get(name, default_invalid),
                            valid_range = valid_ranges.get(name, None))
                counter += 1

                if name in self.column_info_dict:
                    raise ValueError('duplicated column name: ' + name)

                self.column_info_list.append(pdscol)
                self.column_info_dict[pdscol.name] = pdscol
                self.dtype0[pdscol.name] = pdscol.dtype0

        # Fill in the complete table file name
        self.table_file_path = os.path.join(os.path.dirname(label_file_path),
                                            self.table_file_name)

################################################################################
# class PdsColumnInfo
################################################################################

class PdsColumnInfo(object):
    """The PdsColumnInfo class holds the attributes of one column in a PDS
    label."""

    def __init__(self, node_dict, column_no, invalid=set(), valid_range=None):
        """Constructor for a PdsColumn.

        Input:
            node_dict   the dictionary associated with the pdsparser.PdsNode
                        object defining the column.
            column_no   the index number of this column, starting at zero.
            invalid     an optional set of discrete values that are to be
                        treated as invalid, missing or unknown.
            valid_range an optional tuple or list identifying the lower and
                        upper limits of the valid range for a numeric column.
        """

        self.name = node_dict["NAME"]
        self.colno = column_no

        self.start_byte = node_dict["START_BYTE"]
        self.bytes      = node_dict["BYTES"]

        self.items = node_dict.get("ITEMS", 1)
        self.item_bytes = node_dict.get("ITEM_BYTES", self.bytes)
        self.item_offset = node_dict.get("ITEM_OFFSET", self.bytes)

        # Define dtype0 to isolate each column in a record
        self.dtype0 = ("S" + str(self.bytes), self.start_byte - 1)

        # Define dtype1 as a list of dtypes needed to isolate each item
        if self.items == 1:
            self.dtype1 = None
        else:
            self.dtype1 = {}
            byte0 = 0
            for i in range(self.items):
                self.dtype1["item_" + str(i)] = ("S" + str(self.item_bytes),
                                                 byte0)
                byte0 += self.item_offset

        # Define dtype2 as the intended dtype of the values in the column
        self.data_type = node_dict["DATA_TYPE"]
        if "INTEGER" in self.data_type:
            self.data_type = "int"
            self.dtype2 = "int"
            self.scalar_func = int
        elif "REAL" in self.data_type:
            self.data_type = "float"
            self.dtype2 = "float"
            self.scalar_func = float
        elif ("TIME" in self.data_type or "DATE" in self.data_type or
              self.name.endswith("_TIME") or self.name.endswith("_DATE")):
            self.data_type = "time"
            self.dtype2 = 'S'
            self.scalar_func = tai_from_iso
        elif "CHAR" in self.data_type:
            self.data_type = "string"
            self.dtype2 = STR_DTYPE
            self.scalar_func = None
        else:
            raise IOError("unsupported data type: " + data_type)

        # Identify validity criteria
        self.valid_range = valid_range or node_dict.get("VALID_RANGE", None)

        if isinstance(invalid, (numbers.Real,) + STRING_TYPES):
            invalid = set([invalid])

        self.invalid_values = set(invalid)

        self.invalid_values.add(node_dict.get("INVALID_CONSTANT"       , None))
        self.invalid_values.add(node_dict.get("MISSING_CONSTANT"       , None))
        self.invalid_values.add(node_dict.get("UNKNOWN_CONSTANT"       , None))
        self.invalid_values.add(node_dict.get("NOT_APPLICABLE_CONSTANT", None))
        self.invalid_values.add(node_dict.get("NULL_CONSTANT"          , None))
        self.invalid_values.add(node_dict.get("INVALID"                , None))
        self.invalid_values.add(node_dict.get("MISSING"                , None))
        self.invalid_values.add(node_dict.get("UNKNOWN"                , None))
        self.invalid_values.add(node_dict.get("NOT_APPLICABLE"         , None))
        self.invalid_values.add(node_dict.get("NULL"                   , None))
        self.invalid_values -= {None}
