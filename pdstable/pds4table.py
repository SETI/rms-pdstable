##########################################################################################
# pdstable/pds4table.py
# Store Pds4TableInfo and Pds4ColumnInfo
##########################################################################################
import julian
import numbers
import numpy as np
import os

from pds4_tools.reader.label_objects import Label

PDS4_LBL_EXTENSIONS = ('.xml', '.lblx')

PDS4_FILE_SPEC_NAME_COLNAME = (
    'File Name'
    'File Specification',
)

PDS4_BUNDLE_COLNAME = (
    'Bundle Name',
)

# STR_DTYPE is 'U'
STR_DTYPE = np.array(['x']).dtype.kind

# This is an exhaustive tuple of string-like types
STRING_TYPES = (str, bytes, bytearray, np.str_, np.bytes_)

# Needed because the default value of strip is False
def tai_from_iso(string):
    return julian.tai_from_iso(string, strip=True)

def int_from_base2(string):
    return int(string, 2)

def int_from_base8(string):
    return int(string, 8)

def int_from_base16(string):
    return int(string, 16)

# key: PDS4 data type
# value: a tuple of (self.data_type, self.dtype2, self.scalar_func)
PDS4_CHR_DATA_TYPE_MAPPING = {
    'ASCII_Date_DOY': ('time', 'S', tai_from_iso),
    'ASCII_Date_Time_DOY': ('time', 'S', tai_from_iso),
    'ASCII_Date_Time_DOY_UTC': ('time', 'S', tai_from_iso),
    'ASCII_Date_Time_YMD': ('time', 'S', tai_from_iso),
    'ASCII_Date_Time_YMD_UTC': ('time', 'S', tai_from_iso),
    'ASCII_Date_YMD': ('time', 'S', tai_from_iso),
    'ASCII_Time': ('time', 'S', tai_from_iso),
    'ASCII_Integer': ('int', 'int', int),
    'ASCII_NonNegative_Integer': ('int', 'int', int),
    'ASCII_Real': ('float', 'float', float),
    'ASCII_AnyURI': ('string', STR_DTYPE, None),
    'ASCII_Directory_Path_Name': ('string', STR_DTYPE, None),
    'ASCII_DOI': ('string', STR_DTYPE, None),
    'ASCII_File_Name': ('string', STR_DTYPE, None),
    'ASCII_File_Specification_Name': ('string', STR_DTYPE, None),
    'ASCII_LID': ('string', STR_DTYPE, None),
    'ASCII_LIDVID': ('string', STR_DTYPE, None),
    'ASCII_LIDVID_LID': ('string', STR_DTYPE, None),
    'ASCII_MD5_Checksum': ('string', STR_DTYPE, None),
    'ASCII_String': ('string', STR_DTYPE, None),
    'ASCII_VID': ('string', STR_DTYPE, None),
    'UTF8_String': ('string', STR_DTYPE, None),
    'ASCII_Boolean': ('boolean', 'bool', None),
    'ASCII_Numeric_Base2': ('int', 'int', int_from_base2),
    'ASCII_Numeric_Base8': ('int', 'int', int_from_base8),
    'ASCII_Numeric_Base16': ('int', 'int', int_from_base16),
}

################################################################################
# Class Pds4TableInfo
################################################################################
class Pds4TableInfo(object):
    """The Pds4TableInfo class holds the attributes of a PDS4-labeled table."""

    def __init__(self, label_file_path, label_list=None, invalid={},
                                                         valid_ranges={}):
        """Loads a PDS4 table based on its associated label file.

        Input:
            label_file_path path to the label file
            label_list      an option to override the parsing of the label.
                            If this is a list, it is interpreted as containing
                            all the records of the PDS4 label, in which case the
                            overrides the contents of the label file.
                            Alternatively, this can be a PdsLabel object that
                            was already parsed.
            invalid         an optional dictionary keyed by column name. The
                            returned value must be a list or set of values that
                            are to be treated as invalid, missing or unknown.
            valid_ranges    an optional dictionary keyed by column name. The
                            returned value must be a tuple or list containing
                            the minimum and maximum numeric values in that
                            column.
        """

        # Parse PDS4 label, store the label dictionary from the pds4_tools Label object
        lbl = Label.from_file(label_file_path)
        lbl_dict = lbl.to_dict()
        self.label = lbl_dict

        # Get the table info from the label dictionary
        file_area = lbl_dict['Product_Ancillary']['File_Area_Ancillary']
        try:
            self.table_file_name = file_area['File']['file_name']
        except:
            raise IOError('Table file name was not found in PDS4 label')


        self.header_bytes = int(file_area['Header']['object_length'])
        table_char = file_area['Table_Character']
        self.rows = int(table_char['records'])
        self.columns = int(table_char['Record_Character']['fields'])
        self.row_bytes = int(table_char['Record_Character']['record_length'])

        # Save the key info about each column in a list and a dictionary
        self.column_info_list = []
        self.column_info_dict = {}

        # Construct the dtype0 dictionary
        self.dtype0 = {'crlf': ('|S2', self.row_bytes-2)}

        default_invalid = set(invalid.get('default', []))
        # Get all the columns info from the 'Field_Character' tags in the xml file
        columns = lbl.findall('.//Field_Character')
        for col in columns:
            node_dict = col.to_dict()['Field_Character']
            name = node_dict['name']
            field_num = int(node_dict['field_number'])

            pdscol = Pds4ColumnInfo(node_dict, field_num,
                        invalid = invalid.get(name, default_invalid),
                        valid_range = valid_ranges.get(name, None))

            # PDS4 TODO: Do we have more duplicated column names, except the 'Target'?
            # Handle duplicated column name 'Target'
            if name in self.column_info_dict and name != 'Target':
            # if name in self.column_info_dict:
                raise ValueError('duplicated column name: ' + name)

            self.column_info_list.append(pdscol)
            # Add '_Specific' for specific target column to avoid multiple pdscol
            # instances having the same name and riase the error np.stack is called
            # in pdstable/__init__.py. We don't need to do this if all column names
            # are unique.
            if pdscol.name in self.column_info_dict and pdscol.name == 'Target':
                pdscol.name += '_Specific'
            self.column_info_dict[pdscol.name] = pdscol
            self.dtype0[pdscol.name] = pdscol.dtype0


        self.table_file_path = os.path.join(os.path.dirname(label_file_path),
                                            self.table_file_name)


################################################################################
# class Pds4ColumnInfo
################################################################################

class Pds4ColumnInfo(object):
    """The Pds4ColumnInfo class holds the attributes of one column in a PDS4
    label."""

    def __init__(self, node_dict, column_no, invalid=set(), valid_range=None):
        """Constructor for a Pds4Column.

        Input:
            node_dict   the dictionary associated with the pdsparser.PdsNode
                        object defining the column.
            column_no   the index number of this column, starting at zero.
            invalid     an optional set of discrete values that are to be
                        treated as invalid, missing or unknown.
            valid_range an optional tuple or list identifying the lower and
                        upper limits of the valid range for a numeric column.
        """

        self.name = node_dict['name']
        self.colno = column_no

        self.start_byte = int(node_dict['field_location'])
        self.bytes      = int(node_dict['field_length'])

        self.items = node_dict.get('ITEMS', 1)
        self.item_bytes = node_dict.get('ITEM_BYTES', self.bytes)
        self.item_offset = node_dict.get('ITEM_OFFSET', self.bytes)

        # Define dtype0 to isolate each column in a record
        self.dtype0 = ('S' + str(self.bytes), self.start_byte - 1)

        # Define dtype1 as a list of dtypes needed to isolate each item
        if self.items == 1:
            self.dtype1 = None
        else:
            self.dtype1 = {}
            byte0 = 0
            for i in range(self.items):
                self.dtype1['item_' + str(i)] = ('S' + str(self.item_bytes),
                                                 byte0)
                byte0 += self.item_offset

        # PDS4 TODO: review the data type conversion
        # Define dtype2 as the intended dtype of the values in the column
        self.data_type = node_dict['data_type']
        # Convert PDS4 data_type
        try:
            (self.data_type,
             self.dtype2,
             self.scalar_func) = PDS4_CHR_DATA_TYPE_MAPPING[self.data_type]
        except:
            raise IOError('unsupported data type: ' + self.data_type)

        # Identify validity criteria
        self.valid_range = valid_range or node_dict.get('VALID_RANGE', None)

        if isinstance(invalid, (numbers.Real,) + STRING_TYPES):
            invalid = set([invalid])

        self.invalid_values = set(invalid)

        # PDS4 TODO: update these with PDS4 invalid values
        self.invalid_values.add(node_dict.get('INVALID_CONSTANT'       , None))
        self.invalid_values.add(node_dict.get('MISSING_CONSTANT'       , None))
        self.invalid_values.add(node_dict.get('UNKNOWN_CONSTANT'       , None))
        self.invalid_values.add(node_dict.get('NOT_APPLICABLE_CONSTANT', None))
        self.invalid_values.add(node_dict.get('NULL_CONSTANT'          , None))
        self.invalid_values.add(node_dict.get('INVALID'                , None))
        self.invalid_values.add(node_dict.get('MISSING'                , None))
        self.invalid_values.add(node_dict.get('UNKNOWN'                , None))
        self.invalid_values.add(node_dict.get('NOT_APPLICABLE'         , None))
        self.invalid_values.add(node_dict.get('NULL'                   , None))
        self.invalid_values -= {None}
