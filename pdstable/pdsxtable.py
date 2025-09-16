################################################################################
# pdstable/pdsxtable.py
# PdsTableInfo and PdsColumnInfo
# These are the parent classes for Pds3TableInfo and Pds4TableInfo,
# and Pds3ColumnInfo and Pds4ColumnInfo.
################################################################################

from filecache import FCPath


################################################################################
# Class PdsTableInfo
################################################################################

class PdsTableInfo:
    """Class to hold the attributes of a PDS-labeled table.

    Direct access to this class's attributes by the end user is deprecated and only
    supported for backwards compatibility. Use the properties of PdsTable instead.
    """

    def __init__(self, label_file_path):

        self._label_file_remote_path = FCPath(label_file_path)
        self._label_file_path = self._label_file_remote_path.retrieve()
        self._label_file_name = self._label_file_path.name

        self._label = None
        self._table_file_name = None
        self._table_file_path = None
        self._header_bytes = 0
        self._fixed_length_row = False
        self._field_delimiter = None
        self._rows = 0
        self._columns = 0
        self._row_bytes = 0
        self._column_info_list = []
        self._column_info_dict = {}
        self._dtype0 = {}

    @property
    def label(self):
        """The label of the table as a Pds3Label for PDS3 or dict for PDS4."""
        return self._label

    @property
    def label_file_name(self):
        """The name of the label file (without the path)."""
        return self._label_file_name

    @property
    def label_file_path(self):
        """The local path to the label file."""
        return self._label_file_path

    @property
    def table_file_name(self):
        """The name of the table file (without the path)."""
        return self._table_file_name

    @property
    def table_file_path(self):
        """The local path to the table file."""
        return self._table_file_path

    @property
    def header_bytes(self):
        """The number of bytes in the header of the table."""
        return self._header_bytes

    @property
    def fixed_length_row(self):
        """True if the table has fixed-length rows."""
        return self._fixed_length_row

    @property
    def field_delimiter(self):
        """The field delimiter for the table."""
        return self._field_delimiter

    @property
    def rows(self):
        """The number of rows in the table."""
        return self._rows

    @property
    def columns(self):
        """The number of columns in the table."""
        return self._columns

    @property
    def row_bytes(self):
        """The number of bytes in a single row of the table."""
        return self._row_bytes

    @property
    def column_info_list(self):
        """The list of PdsColumnInfo objects for the columns in the table."""
        return self._column_info_list

    @property
    def column_info_dict(self):
        """The dict of PdsColumnInfo objects for the columns in the table, keyed by
        the column name."""
        return self._column_info_dict

    @property
    def dtype0(self):
        """The dtype dictionary for the table, keyed by the column name.

        Each value is a tuple of (dtype_string, start_byte) where dtype_string is the
        string representation of the dtype (e.g., 'S10' for a 10-character string)
        and start_byte is the starting byte position of the column in a row.
        """
        return self._dtype0


################################################################################
# Class PdsColumnInfo
################################################################################

class PdsColumnInfo:
    """Class to hold the attributes of one column in a PDS-labeled table.

    Direct access of this class's attributes by the end user is not generally necessary,
    but is permitted if you want the inner details of each column.
    """

    def __init__(self):
        self._name = None
        self._colno = None
        self._start_byte = None
        self._bytes = None
        self._items = None
        self._item_bytes = None
        self._item_offset = None
        self._data_type = None
        self._dtype0 = None
        self._dtype1 = None
        self._dtype2 = None
        self._scalar_func = None
        self._valid_range = None
        self._invalid_values = None

    @property
    def name(self):
        """The name of the column."""
        return self._name

    @property
    def colno(self):
        """The index number of the column, starting at zero."""
        return self._colno

    @property
    def start_byte(self):
        """The starting byte of the column in the row (1-based)."""
        return self._start_byte

    @property
    def bytes(self):
        """The number of bytes in the column."""
        return self._bytes

    @property
    def items(self):
        """The number of items in the column (PDS3 only)."""
        return self._items

    @property
    def item_bytes(self):
        """The number of bytes in an item of the column (PDS3 only)."""
        return self._item_bytes

    @property
    def item_offset(self):
        """The incremental offset of each item within the column."""
        return self._item_offset

    @property
    def data_type(self):
        """The data type of the column.

        Possible values are 'int', 'float', 'time', and 'string'.
        """
        return self._data_type

    @property
    def dtype0(self):
        """The dtype of the entire column as a string.

        Each value is a tuple of (dtype_string, start_byte) where dtype_string is the
        string representation of the dtype (e.g., 'S10' for a 10-character string)
        and start_byte is the starting byte position of the column in a row.
        """
        return self._dtype0

    @property
    def dtype1(self):
        """The dtype of a multiple-item column.

        If items == 0, this value is None. Otherwise, it is a dict keyed by 'item_0',
        'item_1', etc. with the value being a tuple of the string representation of
        the dtype used to isolate each item as a string (Snnn) and the starting byte
        relative to the beginning of the column for that item.
        """
        return self._dtype1

    @property
    def dtype2(self):
        """The dtype of the column with the actual data type.

        Possible values are 'int', 'float', 'S', and 'U'.
        """
        return self._dtype2

    @property
    def scalar_func(self):
        """The scalar function used to convert the column's string value to its data
        value."""
        return self._scalar_func

    @property
    def valid_range(self):
        """The valid range of the column as a tuple (lower, upper) or None."""
        return self._valid_range

    @property
    def invalid_values(self):
        """The set of invalid value markers for the column.

        If the column's value equals one of these markers, the column value is considered
        invalid.
        """
        return self._invalid_values
