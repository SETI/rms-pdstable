##########################################################################################
# pdstable/pds_table_info.py
# PdsTableInfo and PdsColumnInfo
# These are the parent classes for Pds3TableInfo and Pds4TableInfo,
# and Pds3ColumnInfo and Pds4ColumnInfo.
##########################################################################################



################################################################################
# Class PdsTableInfo
################################################################################

class PdsTableInfo:
    """Class to hold the attributes of a PDS-labeled table."""

    @property
    def label(self):
        """The label of the table as a Pds3Label or dict for PDS4."""
        return self._label

    @property
    def table_file_name(self):
        """The name of the table file."""
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
        """The number of bytes in a row of the table."""
        return self._row_bytes

    @property
    def column_info_list(self):
        """The list of PdsColumnInfo objects for the columns in the table."""
        return self._column_info_list

    @property
    def column_info_dict(self):
        """The dictionary of PdsColumnInfo objects for the columns in the table."""
        return self._column_info_dict

    @property
    def dtype0(self):
        """The dtype dictionary for the table.

        The key is the name of the column, and the value is a tuple of the dtype and the
        number of bytes in the column.
        """
        return self._dtype0


################################################################################
# Class PdsColumnInfo
################################################################################

class PdsColumnInfo:
    """Class to hold the attributes of one column in a PDS-labeled table."""

    @property
    def name(self):
        """The name of the column."""
        return self._name

    @property
    def colno(self):
        """The index number of the column."""
        return self._colno

    @property
    def start_byte(self):
        """The starting byte of the column."""
        return self._start_byte

    @property
    def bytes(self):
        """The number of bytes in the column."""
        return self._bytes

    @property
    def items(self):
        """The number of items in the column."""
        return self._items

    @property
    def item_bytes(self):
        """The number of bytes in an item of the column."""
        return self._item_bytes

    @property
    def item_offset(self):
        """The offset of an item of the column."""
        return self._item_offset

    @property
    def data_type(self):
        """The data type of the column."""
        return self._data_type

    @property
    def dtype0(self):
        """The dtype0 of the column."""
        return self._dtype0

    @property
    def dtype1(self):
        """The dtype1 of the column."""
        return self._dtype1

    @property
    def dtype2(self):
        """The dtype2 of the column."""
        return self._dtype2

    @property
    def scalar_func(self):
        """The scalar function of the column."""
        return self._scalar_func

    @property
    def valid_range(self):
        """The valid range of the column."""
        return self._valid_range

    @property
    def invalid_values(self):
        """The invalid values of the column."""
        return self._invalid_values
