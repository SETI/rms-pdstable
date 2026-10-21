################################################################################
# UNIT TESTS FOR UTILS.PY
################################################################################


import numpy as np

from pdstable.utils import (is_pds4_label, tai_from_iso, int_from_base2,
                            int_from_base8, int_from_base16, lowercase_value)
import pytest


"""Test cases for utility functions in utils.py."""

def test_is_pds4_label() -> None:
    """Test is_pds4_label function with various file extensions."""

    # Test PDS4 label extensions
    assert is_pds4_label('data.xml')
    assert is_pds4_label('data.lblx')
    assert is_pds4_label('/path/to/file.xml')
    assert is_pds4_label('C:\\path\\to\\file.lblx')

    # Test non-PDS4 label extensions
    assert not is_pds4_label('data.lbl')
    assert not is_pds4_label('data.tab')
    assert not is_pds4_label('data.txt')
    assert not is_pds4_label('data')
    assert not is_pds4_label('')

    # Test edge cases - the function only checks if the string ends with the
    # extensions
    assert is_pds4_label('.xml')  # Just extension
    assert not is_pds4_label('xml')   # No dot
    assert not is_pds4_label('data.xml.bak')  # Multiple extensions doesn't
    # end with .xml

    # Test case sensitivity - the function is case-sensitive
    assert not is_pds4_label('data.XML')  # Uppercase extension
    assert not is_pds4_label('data.LBLX')  # Uppercase extension

def test_tai_from_iso() -> None:
    """Test tai_from_iso function with various ISO time strings."""

    # Test basic ISO time strings
    # Note: These are example values - actual TAI values may differ
    # We're testing that the function doesn't crash and returns a number

    # Test various ISO formats
    result1 = tai_from_iso('2007-312T03:31:12.392')
    assert isinstance(result1, (int, float))  # Can be either int or float
    assert result1 > 0

    result2 = tai_from_iso('2007-01-01T00:00:00')
    assert isinstance(result2, (int, float))  # Can be either int or float
    assert result2 > 0

    result3 = tai_from_iso('2007-001T00:00:00.000')
    assert isinstance(result3, (int, float))  # Can be either int or float
    assert result3 > 0

    # Test that strip=True works (removes whitespace)
    result4 = tai_from_iso('  2007-312T03:31:12.392  ')
    assert isinstance(result4, (int, float))  # Can be either int or float
    assert result4 == result1

    # Test edge cases
    with pytest.raises(ValueError, match='unrecognized ISO date format'):
        tai_from_iso('invalid_time')

    with pytest.raises(ValueError, match='unrecognized ISO date format'):
        tai_from_iso('')

    with pytest.raises(ValueError, match='month must be between 1 and 12'):
        tai_from_iso('2007-13-45T25:70:99')  # Invalid date/time

def test_int_from_base2() -> None:
    """Test int_from_base2 function with various binary strings."""

    # Test valid binary strings
    assert int_from_base2('0') == 0
    assert int_from_base2('1') == 1
    assert int_from_base2('10') == 2
    assert int_from_base2('11') == 3
    assert int_from_base2('100') == 4
    assert int_from_base2('101') == 5
    assert int_from_base2('110') == 6
    assert int_from_base2('111') == 7
    assert int_from_base2('1000') == 8
    assert int_from_base2('1001') == 9
    assert int_from_base2('1010') == 10

    # Test longer binary strings
    assert int_from_base2('10101010') == 170
    assert int_from_base2('11111111') == 255
    assert int_from_base2('100000000') == 256

    # Test edge cases
    assert int_from_base2('0000') == 0
    assert int_from_base2('0001') == 1

    # Test error cases
    with pytest.raises(ValueError):
        int_from_base2('2')  # Invalid binary digit

    with pytest.raises(ValueError):
        int_from_base2('10a')  # Invalid binary digit

    with pytest.raises(ValueError):
        int_from_base2('')  # Empty string

    with pytest.raises(ValueError):
        int_from_base2('abc')  # No valid digits

def test_int_from_base8() -> None:
    """Test int_from_base8 function with various octal strings."""

    # Test valid octal strings
    assert int_from_base8('0') == 0
    assert int_from_base8('1') == 1
    assert int_from_base8('7') == 7
    assert int_from_base8('10') == 8
    assert int_from_base8('11') == 9
    assert int_from_base8('17') == 15
    assert int_from_base8('20') == 16
    assert int_from_base8('77') == 63
    assert int_from_base8('100') == 64
    assert int_from_base8('777') == 511

    # Test edge cases
    assert int_from_base8('0000') == 0
    assert int_from_base8('0001') == 1

    # Test error cases
    with pytest.raises(ValueError):
        int_from_base8('8')  # Invalid octal digit

    with pytest.raises(ValueError):
        int_from_base8('18')  # Invalid octal digit

    with pytest.raises(ValueError):
        int_from_base8('')  # Empty string

    with pytest.raises(ValueError):
        int_from_base8('abc')  # No valid digits

def test_int_from_base16() -> None:
    """Test int_from_base16 function with various hexadecimal strings."""

    # Test valid hex strings
    assert int_from_base16('0') == 0
    assert int_from_base16('1') == 1
    assert int_from_base16('9') == 9
    assert int_from_base16('a') == 10
    assert int_from_base16('A') == 10
    assert int_from_base16('f') == 15
    assert int_from_base16('F') == 15
    assert int_from_base16('10') == 16
    assert int_from_base16('1f') == 31
    assert int_from_base16('20') == 32
    assert int_from_base16('ff') == 255
    assert int_from_base16('FF') == 255
    assert int_from_base16('100') == 256

    # Test longer hex strings
    assert int_from_base16('ffff') == 65535
    assert int_from_base16('10000') == 65536

    # Test edge cases
    assert int_from_base16('0000') == 0
    assert int_from_base16('0001') == 1

    # Test error cases
    with pytest.raises(ValueError):
        int_from_base16('g')  # Invalid hex digit

    with pytest.raises(ValueError):
        int_from_base16('1g')  # Invalid hex digit

    with pytest.raises(ValueError):
        int_from_base16('')  # Empty string

    with pytest.raises(ValueError):
        int_from_base16('xyz')  # No valid digits

def test_lowercase_value_string() -> None:
    """Test lowercase_value function with string inputs."""

    # Test basic string conversion
    assert lowercase_value('Hello') == 'hello'
    assert lowercase_value('WORLD') == 'world'
    assert lowercase_value('MiXeD') == 'mixed'
    assert lowercase_value('') == ''
    assert lowercase_value('123') == '123'
    assert lowercase_value('!@#') == '!@#'

    # Test unicode strings
    assert lowercase_value('HÉLLÖ') == 'héllö'
    assert lowercase_value('ÑOÑO') == 'ñoño'

def test_lowercase_value_tuple() -> None:
    """Test lowercase_value function with tuple inputs."""

    # Test tuple with strings
    input_tuple = ('Hello', 'WORLD', 'MiXeD')
    expected = ('hello', 'world', 'mixed')
    result = lowercase_value(input_tuple)
    assert result == expected

    # Test tuple with mixed types
    mixed_tuple = ('Hello', 123, 'WORLD', 45.67, 'MiXeD')
    mixed_expected = ('hello', 123, 'world', 45.67, 'mixed')
    result = lowercase_value(mixed_tuple)
    assert result == mixed_expected

    # Test empty tuple
    assert lowercase_value(()) == ()

    # Test single element tuple
    assert lowercase_value(('Hello',)) == ('hello',)

    # Test nested tuples (should not be processed)
    nested_tuple = ('Hello', ('WORLD', 'MiXeD'))
    nested_expected = ('hello', ('WORLD', 'MiXeD'))  # Nested tuple unchanged
    result = lowercase_value(nested_tuple)
    assert result == nested_expected

def test_lowercase_value_numpy_array() -> None:
    """Test lowercase_value function with numpy array inputs."""

    # Test numpy array with strings
    input_array = np.array(['Hello', 'WORLD', 'MiXeD'])
    expected = np.array(['hello', 'world', 'mixed'])
    result = lowercase_value(input_array)
    np.testing.assert_array_equal(result, expected)

    # Test numpy array with mixed types
    input_array = np.array(['Hello', 'WORLD', 'MiXeD'], dtype=object)
    expected = np.array(['hello', 'world', 'mixed'], dtype=object)
    result = lowercase_value(input_array)
    np.testing.assert_array_equal(result, expected)

    # Test empty numpy array
    input_array = np.array([])
    result = lowercase_value(input_array)
    np.testing.assert_array_equal(result, input_array)

    # Test single element numpy array
    input_array = np.array(['Hello'])
    expected = np.array(['hello'])
    result = lowercase_value(input_array)
    np.testing.assert_array_equal(result, expected)

    # Test 2D numpy array - the function only processes 1D arrays
    # For 2D arrays, it doesn't process the nested elements
    input_array = np.array([['Hello', 'WORLD'], ['MiXeD', 'Case']])
    result = lowercase_value(input_array)
    # The function doesn't process 2D arrays recursively, so the result should be
    # unchanged
    np.testing.assert_array_equal(result, input_array)

def test_lowercase_value_other_types() -> None:
    """Test lowercase_value function with non-string types."""

    # Test numeric types (should be unchanged)
    assert lowercase_value(123) == 123
    assert lowercase_value(45.67) == 45.67
    assert lowercase_value(True) is True
    assert lowercase_value(False) is False
    assert lowercase_value(None) is None

    # Test list (should be unchanged)
    input_list = ['Hello', 'WORLD']
    result = lowercase_value(input_list)
    assert result == input_list  # Lists are not processed

    # Test dict (should be unchanged)
    input_dict = {'key': 'value'}
    result = lowercase_value(input_dict)
    assert result == input_dict  # Dicts are not processed

    # Test custom object (should be unchanged)
    class CustomObject:
        pass
    custom_obj = CustomObject()
    result = lowercase_value(custom_obj)
    assert result == custom_obj

def test_lowercase_value_edge_cases() -> None:
    """Test lowercase_value function with edge cases."""

    # Test very long strings
    long_string = 'A' * 1000
    result = lowercase_value(long_string)
    assert result == 'a' * 1000

    # Test strings with special characters
    special_string = '!@#$%^&*()_+-=[]{}|;:\',./<>?'
    result = lowercase_value(special_string)
    assert result == special_string  # Special chars unchanged

    # Test strings with numbers
    mixed_string = 'Hello123World456'
    result = lowercase_value(mixed_string)
    assert result == 'hello123world456'

    # Test strings with spaces
    spaced_string = '  Hello  World  '
    result = lowercase_value(spaced_string)
    assert result == '  hello  world  '

def test_lowercase_value_performance() -> None:
    """Test lowercase_value function performance with large inputs."""

    # Test with large numpy array
    large_array = np.array(['Hello'] * 10000)
    result = lowercase_value(large_array)
    assert len(result) == 10000
    assert result[0] == 'hello'
    assert result[-1] == 'hello'

    # Test with large tuple
    large_tuple = ('Hello',) * 1000
    result = lowercase_value(large_tuple)
    assert len(result) == 1000
    assert result[0] == 'hello'
    assert result[-1] == 'hello'
