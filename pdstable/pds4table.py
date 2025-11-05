################################################################################
# pdstable/pds4table.py
# Pds4TableInfo and Pds4ColumnInfo
################################################################################

from collections import defaultdict
import numbers
import re

from pds4_tools.reader.label_objects import Label

from .pdsxtable import PdsColumnInfo, PdsTableInfo
from .utils import (int_from_base2,
                    int_from_base8,
                    int_from_base16,
                    string_collapsed,
                    tai_from_iso,
                    STRING_TYPES)


# A list of possible table column names that store the bundle name.
PDS4_BUNDLE_COLNAMES_lc = (
    'bundle_name',
    'bundle name',
    'bundle',
)

# A list of possible table column names (unique) that store the path of the file spec or
# the file name. This will be used to get the index of the column containing file
# specification path or name. The order of the values matters in this variable.
# Since there is no standard name in PDS4 for this column (if it's even present),
# we look for these fields that are created by the RMS Node's
# pds4_create_xml_index tool.
PDS4_FILE_SPECIFICATION_COLUMN_NAMES_lc = (
    'file_specification',
    'file specification',
    'file_specification_name',
    'file specification name',
    'filepath',
    'filename',
    'file name',
    'file_name',
)

# The mapping of a product tag to its corresponding file area tags
# The key is a product component tag, and the value is its corresponding file area tag,
# it could be just one (string) or multiple (tuple) file area tags
_PDS4_PRODUCT_TO_FILE_AREA_TAGS_MAPPING = {
    'Product_Ancillary': ('File_Area_Ancillary',),
    'Product_Browse': ('File_Area_Browse',),
    'Product_Bundle': ('File_Area_Text',),
    'Product_Collection': ('File_Area_Inventory',),
    'Product_External': ('File_Area_External',),
    'Product_File_Repository': ('File_Area_Binary',),
    'Product_File_Text': ('File_Area_Text',),
    'Product_Metadata_Supplemental': ('File_Area_Metadata',),
    'Product_Native': ('File_Area_Native',),
    'Product_Observational': ('File_Area_Observational',
                              'File_Area_Observational_Supplemental'),
    'Product_Proxy_PDS3': ('File_Area_Binary',),
    'Product_SPICE_Kernel': ('File_Area_SPICE_Kernel',),
    'Product_XML_Schema': ('File_Area_XML_Schema',),
}

# The mapping of a table tag to its corresponding record and field tags
# The key is a table tag, and the value is a tuple of the record and field tags
_PDS4_TABLE_TO_RECORD_FIELD_TAGS_MAPPING = {
    'Inventory': ('Record_Delimited', 'Field_Delimited'),
    'Manifest_SIP_Deep_Archive': ('Record_Delimited', 'Field_Delimited'),
    'Table_Binary': ('Record_Binary', 'Field_Binary'),
    'Table_Character': ('Record_Character', 'Field_Character'),
    'Table_Delimited': ('Record_Delimited', 'Field_Delimited'),
    'Table_Delimited_Source_Product_External': ('Record_Delimited', 'Field_Delimited'),
    'Table_Delimited_Source_Product_Internal': ('Record_Delimited', 'Field_Delimited'),
    'Transfer_Manifest': ('Record_Character', 'Field_Character'),
}

# PDS4 label tags under Special_Constants
_PDS4_SPECIAL_CONSTANTS_TAGS = {
    'error_constant',
    'high_instrument_saturation',
    'high_representation_saturation',
    'invalid_constant',
    'low_instrument_saturation',
    'low_representation_saturation',
    'missing_constant',
    'not_applicable_constant',
    'saturated_constant',
    'unknown_constant',
    # 'valid_maximum',
    # 'valid_minimum'
}

# Delimiter used to separate column values in the same row
# It's encoded by 'UTF-8'
PDS4_FIELD_DELIMITER = {
    'Carriage-Return Line-Feed': b'\r\n',
    'Comma': b',',
    'Horizontal Tab': b'\t',
    'Semicolon': b';',
    'Vertical Bar': b'|'
}

# key: PDS4 data type
# value: a tuple of (self._data_type, self._dtype2, self._scalar_func)
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
    'ASCII_AnyURI': ('string', 'U', None),
    'ASCII_Directory_Path_Name': ('string', 'U', None),
    'ASCII_DOI': ('string', 'U', None),
    'ASCII_File_Name': ('string', 'U', None),
    'ASCII_File_Specification_Name': ('string', 'U', None),
    'ASCII_LID': ('string', 'U', None),
    'ASCII_LIDVID': ('string', 'U', None),
    'ASCII_LIDVID_LID': ('string', 'U', None),
    'ASCII_MD5_Checksum': ('string', 'U', None),
    'ASCII_String': ('string', 'U', None),
    'ASCII_Short_String_Collapsed': ('string', 'U', string_collapsed),
    'ASCII_Short_String_Preserved': ('string_preserved', 'U', None),
    'ASCII_Text_Collapsed': ('string', 'U', string_collapsed),
    'ASCII_Text_Preserved': ('string_preserved', 'U', None),
    'ASCII_VID': ('string', 'U', None),
    'UTF8_String': ('string', 'U', None),
    'UTF8_Short_String_Collapsed': ('string', 'U', string_collapsed),
    'UTF8_Short_String_Preserved': ('string_preserved', 'U', None),
    'ASCII_Boolean': ('boolean', 'bool', None),
    'ASCII_Numeric_Base2': ('int', 'int', int_from_base2),
    'ASCII_Numeric_Base8': ('int', 'int', int_from_base8),
    'ASCII_Numeric_Base16': ('int', 'int', int_from_base16),
}


################################################################################
# Class Pds4TableInfo
################################################################################

class Pds4TableInfo(PdsTableInfo):
    """The Pds4TableInfo class holds the attributes of a PDS4-labeled table."""

    def __init__(self, label_file_path, *, label_contents=None, invalid=None,
                 valid_ranges=None, table_file=None):
        """Load a PDS4 table based on its associated label file.

        Parameters:
            label_file_path (str or Path or FCPath): Path to the PDS4 label file. Even if
                the label contents is provided in `label_list`, `label_file_path` must be
                be specificed because it is needed to locate the table file. If this
                parameter is an FCPath object, it will be downloaded from the remote
                source.
            label_contents (pds4_tools.Label or dict, optional): An option to override
                the parsing of the label. If this is a dict, it is treated as the complete
                structure of the parsed label. If it is a pds4_tools.Label object, it is
                assumed to be the label file that was already parsed. If None, the label
                file specified by `label_file_path` is read and parsed.
            invalid (dict, optional): An optional dictionary keyed by column name. The
                returned value must be a list or set of values that are to be treated as
                invalid, missing, or unknown.
            valid_ranges (dict, optional): An optional dictionary keyed by column name.
                The returned value must be a tuple or list containing the minimum and
                maximum numeric values in that column.
            table_file (str or int, optional): Specify a table file name to be read or an
                integer (1-based) representing the order in which the table appears in the
                label file. A string is treated as a regular expression. If the provided
                table name doesn't exist in the label or the integer is out of the range,
                an error will be raised.
        """

        super().__init__(label_file_path)

        if invalid is None:
            invalid = {}
        if valid_ranges is None:
            valid_ranges = {}

        # Parse the label
        if isinstance(label_contents, Label):
            self._label = label_contents.to_dict()
        elif isinstance(label_contents, dict):
            self._label = label_contents
        elif label_contents:
            raise TypeError('label_contents must be a pds4_tools.Label object, a ' +
                            'dictionary, or None')
        else:
            lbl = Label.from_file(self._label_file_path)
            self._label = lbl.to_dict()

        # Get the file area (table file) info from the label dictionary
        file_areas = []
        for prod_tag, prod_component in self._label.items():
            if prod_tag not in _PDS4_PRODUCT_TO_FILE_AREA_TAGS_MAPPING:
                continue
            file_area_tags = _PDS4_PRODUCT_TO_FILE_AREA_TAGS_MAPPING[prod_tag]
            for current_file_area_tag, current_file_area in prod_component.items():
                if current_file_area_tag not in file_area_tags:
                    continue
                if not isinstance(current_file_area, list):
                    current_file_area = [current_file_area]
                file_areas += current_file_area

        self._table_file_name = None

        if len(file_areas) == 0:
            raise ValueError(f'{label_file_path} does not contain any table file info.')

        try:
            table_name_li = [f['File']['file_name'] for f in file_areas]
        except KeyError:
            raise ValueError('"File/file_name" element not found in PDS4 label for '
                             'one of the File_Area classes')

        if table_file is None:
            if len(file_areas) > 1:
                raise ValueError('The table_file parameter was not specified; it is '
                                 'required because the label contains '
                                 f'{len(table_name_li)} table files: '
                                 f'{", ".join(table_name_li)}')
            else:
                self._table_file_name = table_name_li[0]
                file_area = file_areas[0]
        elif isinstance(table_file, str):
            for idx, name in enumerate(table_name_li):
                if re.match(table_file, name):
                    self._table_file_name = name
                    file_area = file_areas[idx]
                    break
            else:
                raise ValueError(f'The requested table file name "{table_file}" '
                                 'doesn\'t exist. '
                                 f'The label contains {len(table_name_li)} table '
                                 f'files: {", ".join(table_name_li)}')
        elif isinstance(table_file, int):
            if not 1 <= table_file <= len(table_name_li):
                raise ValueError(f'The table_file parameter ({table_file}) is out of the '
                                 f'valid range 1 to {len(table_name_li)}')
            else:
                self._table_file_name = table_name_li[table_file - 1]
                file_area = file_areas[table_file - 1]
        else:
            raise TypeError('table_file must be a string or integer')

        try:
            self._header_bytes = int(file_area['Header']['object_length'])
        except KeyError:
            # Some tables don't have a header
            self._header_bytes = 0

        # Get the table/record/field info by searching the tags in the file area
        table_tag = None
        table_area = None
        record_area = None
        columns = None
        for table_type, (record_tag, field_tag) in \
                _PDS4_TABLE_TO_RECORD_FIELD_TAGS_MAPPING.items():
            # There will only be one table type in the file area so the search order
            # doesn't matter
            if table_type in file_area:
                table_tag = table_type
                table_area = file_area[table_type]
                record_area = table_area.get(record_tag, None)
                columns = record_area.get(field_tag, None)
                break

        if table_area is None:
            raise ValueError(f'No Table type found for "{self._table_file_name}" in '
                             f'"{label_file_path}"; this probably means the File type '
                             'is currently not supported by PdsTable')
        if record_area is None:
            raise ValueError(f'No Record element found for "{self._table_file_name}" in '
                             f'"{label_file_path}"')
        if columns is None:
            raise ValueError(f'No Field element found for "{self._table_file_name}" in '
                             f'"{label_file_path}"')
        if table_tag == 'Table_Binary':
            raise ValueError('Binary table is not supported for '
                             f'"{self._table_file_name}" in "{label_file_path}"')

        try:
            self._rows = int(table_area['records'])
        except (KeyError, ValueError):
            raise ValueError('Missing or bad "records" element for '
                             f'"{self._table_file_name}" in "{label_file_path}"')
        try:
            self._columns = int(record_area['fields'])
        except (KeyError, ValueError):
            raise ValueError('Missing or bad "fields" element for '
                             f'"{self._table_file_name}" in "{label_file_path}"')

        try:
            # for a table with fixed row length
            self._row_bytes = int(record_area['record_length'])
            self._fixed_length_row = True
            self._field_delimiter = None
        except KeyError:
            # for a non-fixed-length table, the row length is not used
            try:
                self._row_bytes = int(record_area['maximum_record_length'])
            except KeyError:
                self._row_bytes = None
            self._fixed_length_row = False
            self._field_delimiter = PDS4_FIELD_DELIMITER[table_area['field_delimiter']]

        # Save the key info about each column in a list and a dictionary
        self._column_info_list = []
        self._column_info_dict = {}

        # Construct the dtype0 dictionary
        self._dtype0 = {'crlf': ('|S2', self._row_bytes-2)}

        default_invalid = set(invalid.get('default', []))

        # Check all the column names, append the suffix _{num} to the duplicated names
        colname = defaultdict(list)
        for idx, col in enumerate(columns):
            name = col['name']
            colname[name].append(idx)

        for name, idx_li in colname.items():
            # append _{num} if there are duplicated names
            if len(idx_li) > 1:
                for num, i in enumerate(idx_li):
                    columns[i]['name'] += f'_{num+1}'

        for col in columns:
            name = col['name']
            field_num = int(col['field_number'])

            pdscol = Pds4ColumnInfo(col, field_num,
                                    invalid=invalid.get(name, default_invalid),
                                    valid_range=valid_ranges.get(name, None))

            self._column_info_list.append(pdscol)
            self._column_info_dict[pdscol.name] = pdscol
            self._dtype0[pdscol.name] = pdscol.dtype0

        table_file_remote_path = (self._label_file_remote_path
                                  .with_name(self._table_file_name))
        self._table_file_path = table_file_remote_path.retrieve()


################################################################################
# class Pds4ColumnInfo
################################################################################

class Pds4ColumnInfo(PdsColumnInfo):
    """The Pds4ColumnInfo class holds the attributes of one column in a PDS4 label."""

    def __init__(self, node_dict, column_no, *, invalid=None, valid_range=None):
        """Constructor for a Pds4ColumnInfo.

        Parameters:
            node_dict (dict): The dictionary associated with the column info obtained
                from a pds4_tools.Label object.
            column_no (int): The index number of this column, starting at zero.
            invalid (set, optional): An optional set of discrete values that are to be
                treated as invalid, missing or unknown.
            valid_range (tuple or list, optional): An optional tuple or list identifying
                the lower and upper limits of the valid range for a numeric column.
        """

        super().__init__()

        if invalid is None:
            invalid = set()

        self._name = node_dict['name']
        self._colno = column_no

        try:
            self._start_byte = int(node_dict['field_location'])
            self._bytes      = int(node_dict['field_length'])
        except KeyError:
            # For a .csv table, each column length is not fixed (and the row is not
            # fixed), so we don't have these values.
            self._start_byte = None
            self._bytes = None

        if self._start_byte is not None and self._bytes is not None:
            self._items = 1
            # Define dtype0 to isolate each column in a record
            self._dtype0 = ('S' + str(self._bytes), self._start_byte - 1)
            self._dtype1 = None  # Multi-item columns are not used in PDS4
        else:
            self._dtype0 = None
            self._dtype1 = None  # Multi-item columns are not used in PDS4

        # Define dtype2 as the intended dtype of the values in the column
        self._data_type = node_dict['data_type']
        # Convert PDS4 data_type
        try:
            (self._data_type,
             self._dtype2,
             self._scalar_func) = PDS4_CHR_DATA_TYPE_MAPPING[self._data_type]
        except KeyError:
            raise ValueError('unsupported data type: ' + self._data_type)

        # Identify validity criteria
        invalid_set = set()
        if valid_range is not None:
            self._valid_range = valid_range
        else:
            valid_max = None
            valid_min = None
            # Search for the 'Special_Constants' tag. If it exists, get the invalid values
            # from tags in PDS4_SPECIAL_CONSTANTS_TAGS and store them in invalid_set.
            if 'Special_Constants' in node_dict:
                special_const_area = node_dict['Special_Constants']
                for invalid_tag in _PDS4_SPECIAL_CONSTANTS_TAGS:
                    invalid_val = special_const_area.get(invalid_tag, None)
                    if invalid_val:
                        if self._scalar_func:
                            try:
                                invalid_val = self._scalar_func(invalid_val)
                            except ValueError:
                                # if the invalid value can't be converted, we will keep
                                # its original value and data type
                                invalid_val = invalid_val

                        invalid_set.add(invalid_val)

                valid_max = special_const_area.get('valid_maximum', None)
                valid_min = special_const_area.get('valid_minimum', None)
                if self._scalar_func:
                    if valid_max is not None:
                        valid_max = self._scalar_func(valid_max)
                    if valid_min is not None:
                        valid_min = self._scalar_func(valid_min)

            if valid_min is not None and valid_max is not None:
                self._valid_range = (valid_min, valid_max)
            else:
                self._valid_range = None

        if isinstance(invalid, (numbers.Real,) + STRING_TYPES):
            invalid_set.add(invalid)
        else:
            invalid_set |= invalid

        self._invalid_values = invalid_set
