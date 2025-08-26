################################################################################
# pdstable/pds3table.py
# Pds3TableInfo and Pds3ColumnInfo
################################################################################

import numbers
import warnings

from pdsparser import Pds3Label

from .pdsxtable import PdsColumnInfo, PdsTableInfo
from .utils import tai_from_iso, STRING_TYPES


# A list of possible table column names that store the volume ID.
PDS3_VOLUME_COLNAMES_lc = (
    'volume_id',
    'volume id',
    'volume_name',
    'volume name'
)

# A list of possible table column names (unique) that store the path of the file spec or
# the file name. This will be used to get the index of the column containing file
# specification path or name. The order of the values matters in this variable; we
# would like to look for the file*specification* first and the file*name, and then the
# rest.
PDS3_FILE_SPECIFICATION_COLUMN_NAMES_lc = (
    'file_specification',
    'file specification',
    'file_specification_name',
    'file specification name',
    'file_name',
    'file name',
    'filename',
    'product_id',
    'product id',
    'stsci_group_id'
)


################################################################################
# Class Pds3TableInfo
################################################################################

class Pds3TableInfo(PdsTableInfo):
    """The Pds3TableInfo class holds the attributes of a PDS3-labeled table."""

    def __init__(self, label_file_path, *, label_contents=None, invalid=None,
                       valid_ranges=None, label_method='strict'):
        """Load a PDS table based on its associated label file.

        Parameters:
            label_file_path (str or Path or FCPath): Path to the PDS3 label file. Even if
                the label contents is provided in `label_list`, `label_file_path` must be
                be specificed because it is needed to locate the table file. If this
                parameter is an FCPath object, it will be downloaded from the remote
                source.
            label_contents (list or dict or Pds3Label, optional): An option to override
                the parsing of the label. If this is a list, it is interpreted as
                containing all the records of the PDS label. If it is a dict, it is
                treated as a parsed label keyed by label item. If it is a Pds3Label
                object, it is assumed to be the label file that was already parsed. If
                None, the label file specified by `label_file_path` is read and parsed.
            invalid (dict, optional): An optional dictionary keyed by column name. The
                returned value must be a list or set of values that are to be treated as
                invalid, missing, or unknown.
            valid_ranges (dict, optional): An optional dictionary keyed by column name.
                The returned value must be a tuple or list containing the minimum and
                maximum numeric values in that column.
            label_method (str, optional): The method to use to parse the label. One of:

                * "strict" performs strict parsing, which requires that the label conform
                  to the full PDS3 standard.
                * "loose" is similar to the above, but tolerates some common syntax
                  errors.
                * "compound" is similar to "loose", but it parses a "compound" label,
                  i.e., one that might contain more than one "END" statement. This option
                  is not supported for attached labels.
                * "fast": uses a different parser, which executes ~ 30x fast than the
                  above and handles all the most common aspects of the PDS3 standard.
                  However, it is not guaranteed to provide an accurate parsing under all
                  circumstances.
        """

        super().__init__(label_file_path)

        if invalid is None:
            invalid = {}
        if valid_ranges is None:
            valid_ranges = {}

        self._header_bytes = 0

        # Parse the label
        if isinstance(label_contents, (Pds3Label, dict)):
            self._label = label_contents
        elif label_contents:
            self._label = Pds3Label(label_contents, method=label_method)
        else:
            self._label = Pds3Label(label_file_path, method=label_method)

        # Get the basic file info...
        if self._label['RECORD_TYPE'] != 'FIXED_LENGTH':
            raise IOError('PDS table does not contain fixed-length records')

        # PDS3 table always has fixed length rows (for now)
        self._fixed_length_row = True

        # Find the pointer to the table file
        # Confirm that the value is a PdsSimplePointer
        self._table_file_name = None
        for key, value in self._label.items():
            if key[0] == '^' and key.endswith('TABLE'):
                self._table_file_name = value
                if key + '_OFFSET' in self._label:
                    msg = ('Table file pointer ' + self._label[key + '_fmt'] +
                           ' is not a Simple Pointer and isn\'t fully ' +
                           'supported')
                    warnings.warn(msg)
                break

        if self._table_file_name is None:
            raise IOError('Pointer to a data file was not found in PDS label')

        # Locate the root of the table object
        table_dict = self._label[key[1:]]

        # Save key info about the table
        interchange_format = (table_dict.get('INTERCHANGE_FORMAT')
                              or table_dict.get('INTERCHANGE_FORMAT_1'))
        if not interchange_format:
            raise ValueError('Table interchange format not specified in label')
        if interchange_format != 'ASCII':
            raise IOError('PDS table is not in ASCII format')

        try:
            self._rows = table_dict['ROWS']
            self._columns = table_dict['COLUMNS']
            self._row_bytes = table_dict['ROW_BYTES']
        except KeyError as e:
            raise ValueError(f'Table definition is missing required field: {e}')

        # Save the key info about each column in a list and a dictionary
        self._column_info_list = []
        self._column_info_dict = {}

        # Construct the dtype0 dictionary
        self._dtype0 = {'crlf': ('|S2', self._row_bytes-2)}

        default_invalid = set(invalid.get('default', []))
        counter = 0
        for key, column_dict in table_dict.items():
            if not isinstance(column_dict, dict):
                continue
            if column_dict['OBJECT'] == 'COLUMN':
                name = column_dict['NAME']
                pdscol = Pds3ColumnInfo(column_dict, counter,
                                        invalid=invalid.get(name, default_invalid),
                                        valid_range=valid_ranges.get(name, None))
                counter += 1

                if name in self._column_info_dict:
                    raise ValueError('duplicated column name: ' + name)

                self._column_info_list.append(pdscol)
                self._column_info_dict[pdscol.name] = pdscol
                self._dtype0[pdscol.name] = pdscol.dtype0

        table_file_remote_path = (self._label_file_remote_path
                                  .with_name(self._table_file_name))
        self._table_file_path = table_file_remote_path.retrieve()


################################################################################
# class Pds3ColumnInfo
################################################################################

class Pds3ColumnInfo(PdsColumnInfo):
    """The Pds3ColumnInfo class holds the attributes of one column in a PDS3 label."""

    def __init__(self, node_dict, column_no, *, invalid=None, valid_range=None):
        """Constructor for a Pds3ColumnInfo.

        Parameters:
            node_dict (dict): The dictionary associated with the pdsparser.PdsNode
                object defining the column.
            column_no (int): The index number of this column, starting at zero.
            invalid (set, optional): An optional set of discrete values that are to be
                treated as invalid, missing, or unknown.
            valid_range (tuple or list, optional): An optional tuple or list identifying
                the lower and upper limits of the valid range for a numeric column.
        """

        super().__init__()

        if invalid is None:  # pragma: no cover
            # This can never be reached because we always just pass an empty set
            invalid = set()

        self._name = node_dict['NAME']
        self._colno = column_no

        try:
            self._start_byte = node_dict['START_BYTE']
            self._bytes      = node_dict['BYTES']
        except KeyError as e:
            raise ValueError(f'Column definition is missing required field: {e}')

        self._items = node_dict.get('ITEMS', 1)
        self._item_bytes = node_dict.get('ITEM_BYTES', self._bytes)
        self._item_offset = node_dict.get('ITEM_OFFSET', self._bytes)

        # Define dtype0 to isolate each column in a record
        self._dtype0 = ('S' + str(self._bytes), self._start_byte - 1)

        # Define dtype1 as a list of dtypes needed to isolate each item
        if self._items == 1:
            self._dtype1 = None
        else:
            self._dtype1 = {}
            byte0 = 0
            for i in range(self._items):
                self._dtype1['item_' + str(i)] = ('S' + str(self._item_bytes), byte0)
                byte0 += self._item_offset

        # Define dtype2 as the intended dtype of the values in the column
        self._data_type = node_dict['DATA_TYPE']
        if 'INTEGER' in self._data_type:
            self._data_type = 'int'
            self._dtype2 = 'int'
            self._scalar_func = int
        elif 'REAL' in self._data_type:
            self._data_type = 'float'
            self._dtype2 = 'float'
            self._scalar_func = float
        elif ('TIME' in self._data_type or 'DATE' in self._data_type or
              self._name.endswith('_TIME') or self._name.endswith('_DATE')):
            self._data_type = 'time'
            self._dtype2 = 'S'
            self._scalar_func = tai_from_iso
        elif 'CHAR' in self._data_type:
            self._data_type = 'string'
            self._dtype2 = 'U'
            self._scalar_func = None
        else:
            raise IOError('unsupported data type: ' + self._data_type)

        # Identify validity criteria
        self._valid_range = valid_range or node_dict.get('VALID_RANGE', None)

        if isinstance(invalid, (numbers.Real,) + STRING_TYPES):
            invalid = set([invalid])

        self._invalid_values = set(invalid)

        self._invalid_values.add(node_dict.get('INVALID_CONSTANT'       , None))
        self._invalid_values.add(node_dict.get('MISSING_CONSTANT'       , None))
        self._invalid_values.add(node_dict.get('UNKNOWN_CONSTANT'       , None))
        self._invalid_values.add(node_dict.get('NOT_APPLICABLE_CONSTANT', None))
        self._invalid_values.add(node_dict.get('NULL_CONSTANT'          , None))
        self._invalid_values.add(node_dict.get('INVALID'                , None))
        self._invalid_values.add(node_dict.get('MISSING'                , None))
        self._invalid_values.add(node_dict.get('UNKNOWN'                , None))
        self._invalid_values.add(node_dict.get('NOT_APPLICABLE'         , None))
        self._invalid_values.add(node_dict.get('NULL'                   , None))
        self._invalid_values -= {None}
