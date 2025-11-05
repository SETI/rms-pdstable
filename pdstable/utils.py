##########################################################################################
# pdstable/utils.py
# Utility functions for pdstable
##########################################################################################
import julian

import numpy as np


# This is an exhaustive tuple of string-like types
STRING_TYPES = (str, bytes, bytearray, np.str_, np.bytes_)

_PDS4_LBL_EXTENSIONS = {'.xml', '.lblx'}


def is_pds4_label(label_name):
    """Check if the given label is a PDS4 label.

    Parameters:
        label_name (str or Path or FCPath): The name of the label file to check.

    Returns:
        bool: True if the label is a PDS4 label, False otherwise.
    """

    label_name = str(label_name)
    for ext in _PDS4_LBL_EXTENSIONS:
        if label_name.endswith(ext):
            return True
    return False


# Needed because the default value of strip is False
def tai_from_iso(string):
    """Convert ISO time string to TAI seconds.

    Parameters:
        string (str): The ISO time string to convert.

    Returns:
        float: The time in TAI seconds.
    """
    return julian.tai_from_iso(string, strip=True)


def int_from_base2(string):
    """Convert a base-2 string to an integer.

    Parameters:
        string (str): The base-2 string to convert.

    Returns:
        int: The integer value.
    """
    return int(string, 2)


def int_from_base8(string):
    """Convert a base-8 string to an integer.

    Parameters:
        string (str): The base-8 string to convert.

    Returns:
        int: The integer value.
    """
    return int(string, 8)


def int_from_base16(string):
    """Convert a base-16 string to an integer.

    Parameters:
        string (str): The base-16 string to convert.

    Returns:
        int: The integer value.
    """
    return int(string, 16)


def string_collapsed(s):
    """Collapse a string by removing whitespace and converting to lowercase.

    Parameters:
        s (str): The string to collapse.

    Returns:
        str: The collapsed string.
    """
    return s.strip()


def lowercase_value(value):
    """Convert a table value to lower case.

    Handles strings and tuples; leaves ints and floats unchanged.

    Parameters:
        value: The value to convert to lowercase. Can be a string, tuple, numpy array, or
        other type.

    Returns:
        The value converted to lowercase where applicable. Strings are converted to
        lowercase, tuples have their string elements converted to lowercase, numpy arrays
        have their string elements converted to lowercase, and other types are returned
        unchanged.
    """

    if isinstance(value, str):
        value_lc = value.lower()
    elif isinstance(value, tuple):
        value_lc = []
        for item in value:
            if isinstance(item, str):
                value_lc.append(item.lower())
            else:
                value_lc.append(item)
        value_lc = tuple(value_lc)
    elif isinstance(value, np.ndarray):
        value_lc = value.copy()
        for k, val in enumerate(value):
            if isinstance(val, STRING_TYPES):
                value_lc[k] = str(val).lower()
    else:
        value_lc = value

    return value_lc
