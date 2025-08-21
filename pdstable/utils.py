##########################################################################################
# pdstable/utils.py
# Utility functions for pdstable
##########################################################################################
import julian


_PDS4_LBL_EXTENSIONS = {'.xml', '.lblx'}


def is_pds4_label(label_name):
    """Check if the given label is a PDS4 label.

    Parameters:
        label_name (str): The name of the label file to check.

    Returns:
        bool: True if the label is a PDS4 label, False otherwise.
    """

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
