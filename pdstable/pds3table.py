##########################################################################################
# pdstable/pds3table.py
# Store Pds3TableInfo and Pds3ColumnInfo
##########################################################################################
import julian
import numbers
import numpy as np
import os
from pdsparser import Pds3Label
import warnings


# STR_DTYPE is 'U'
STR_DTYPE = np.array(['x']).dtype.kind

# This is an exhaustive tuple of string-like types
STRING_TYPES = (str, bytes, bytearray, np.str_, np.bytes_)

# Needed because the default value of strip is False
def tai_from_iso(string):
    return julian.tai_from_iso(string, strip=True)


################################################################################
# Class Pds3TableInfo
################################################################################
class Pds3TableInfo(object):
    """The Pds3TableInfo class holds the attributes of a PDS3-labeled table."""

    def __init__(self, label_file_path, label_list=None, invalid={},
                                                         valid_ranges={}):
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
        """

        # Parse the label
        if isinstance(label_list, (Pds3Label, dict)):
            self.label = label_list
        elif label_list:
            self.label = Pds3Label(label_list)
        else:
            self.label = Pds3Label(label_file_path)

        # Get the basic file info...
        if self.label["RECORD_TYPE"] != "FIXED_LENGTH":
            raise IOError('PDS table does not contain fixed-length records')
        else:
            # PDS3 table has fixed length rows
            self.fixed_length_row = True

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
        if table_dict["INTERCHANGE_FORMAT"] != "ASCII":
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
                pdscol = Pds3ColumnInfo(column_dict, counter,
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
# class Pds3ColumnInfo
################################################################################

class Pds3ColumnInfo(object):
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
            raise IOError("unsupported data type: " + self.data_type)

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
