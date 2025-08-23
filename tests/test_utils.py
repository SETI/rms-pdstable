################################################################################
# UNIT TESTS FOR UTILS.PY
################################################################################

import unittest

import numpy as np

from pdstable.utils import (is_pds4_label, tai_from_iso, int_from_base2,
                            int_from_base8, int_from_base16, lowercase_value)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions in utils.py."""

    def test_is_pds4_label(self):
        """Test is_pds4_label function with various file extensions."""

        # Test PDS4 label extensions
        self.assertTrue(is_pds4_label('data.xml'))
        self.assertTrue(is_pds4_label('data.lblx'))
        self.assertTrue(is_pds4_label('/path/to/file.xml'))
        self.assertTrue(is_pds4_label('C:\\path\\to\\file.lblx'))

        # Test non-PDS4 label extensions
        self.assertFalse(is_pds4_label('data.lbl'))
        self.assertFalse(is_pds4_label('data.tab'))
        self.assertFalse(is_pds4_label('data.txt'))
        self.assertFalse(is_pds4_label('data'))
        self.assertFalse(is_pds4_label(''))

        # Test edge cases - the function only checks if the string ends with the
        # extensions
        self.assertTrue(is_pds4_label('.xml'))  # Just extension
        self.assertFalse(is_pds4_label('xml'))   # No dot
        self.assertFalse(is_pds4_label('data.xml.bak'))  # Multiple extensions doesn't
        # end with .xml

        # Test case sensitivity - the function is case-sensitive
        self.assertFalse(is_pds4_label('data.XML'))  # Uppercase extension
        self.assertFalse(is_pds4_label('data.LBLX'))  # Uppercase extension

    def test_tai_from_iso(self):
        """Test tai_from_iso function with various ISO time strings."""

        # Test basic ISO time strings
        # Note: These are example values - actual TAI values may differ
        # We're testing that the function doesn't crash and returns a number

        # Test various ISO formats
        result1 = tai_from_iso('2007-312T03:31:12.392')
        self.assertIsInstance(result1, (int, float))  # Can be either int or float
        self.assertGreater(result1, 0)

        result2 = tai_from_iso('2007-01-01T00:00:00')
        self.assertIsInstance(result2, (int, float))  # Can be either int or float
        self.assertGreater(result2, 0)

        result3 = tai_from_iso('2007-001T00:00:00.000')
        self.assertIsInstance(result3, (int, float))  # Can be either int or float
        self.assertGreater(result3, 0)

        # Test that strip=True works (removes whitespace)
        result4 = tai_from_iso('  2007-312T03:31:12.392  ')
        self.assertIsInstance(result4, (int, float))  # Can be either int or float
        self.assertEqual(result4, result1)

        # Test edge cases
        with self.assertRaises(Exception):  # Should raise some kind of error
            tai_from_iso('invalid_time')

        with self.assertRaises(Exception):
            tai_from_iso('')

        with self.assertRaises(Exception):
            tai_from_iso('2007-13-45T25:70:99')  # Invalid date/time

    def test_int_from_base2(self):
        """Test int_from_base2 function with various binary strings."""

        # Test valid binary strings
        self.assertEqual(int_from_base2('0'), 0)
        self.assertEqual(int_from_base2('1'), 1)
        self.assertEqual(int_from_base2('10'), 2)
        self.assertEqual(int_from_base2('11'), 3)
        self.assertEqual(int_from_base2('100'), 4)
        self.assertEqual(int_from_base2('101'), 5)
        self.assertEqual(int_from_base2('110'), 6)
        self.assertEqual(int_from_base2('111'), 7)
        self.assertEqual(int_from_base2('1000'), 8)
        self.assertEqual(int_from_base2('1001'), 9)
        self.assertEqual(int_from_base2('1010'), 10)

        # Test longer binary strings
        self.assertEqual(int_from_base2('10101010'), 170)
        self.assertEqual(int_from_base2('11111111'), 255)
        self.assertEqual(int_from_base2('100000000'), 256)

        # Test edge cases
        self.assertEqual(int_from_base2('0000'), 0)
        self.assertEqual(int_from_base2('0001'), 1)

        # Test error cases
        with self.assertRaises(ValueError):
            int_from_base2('2')  # Invalid binary digit

        with self.assertRaises(ValueError):
            int_from_base2('10a')  # Invalid binary digit

        with self.assertRaises(ValueError):
            int_from_base2('')  # Empty string

        with self.assertRaises(ValueError):
            int_from_base2('abc')  # No valid digits

    def test_int_from_base8(self):
        """Test int_from_base8 function with various octal strings."""

        # Test valid octal strings
        self.assertEqual(int_from_base8('0'), 0)
        self.assertEqual(int_from_base8('1'), 1)
        self.assertEqual(int_from_base8('7'), 7)
        self.assertEqual(int_from_base8('10'), 8)
        self.assertEqual(int_from_base8('11'), 9)
        self.assertEqual(int_from_base8('17'), 15)
        self.assertEqual(int_from_base8('20'), 16)
        self.assertEqual(int_from_base8('77'), 63)
        self.assertEqual(int_from_base8('100'), 64)
        self.assertEqual(int_from_base8('777'), 511)

        # Test edge cases
        self.assertEqual(int_from_base8('0000'), 0)
        self.assertEqual(int_from_base8('0001'), 1)

        # Test error cases
        with self.assertRaises(ValueError):
            int_from_base8('8')  # Invalid octal digit

        with self.assertRaises(ValueError):
            int_from_base8('18')  # Invalid octal digit

        with self.assertRaises(ValueError):
            int_from_base8('')  # Empty string

        with self.assertRaises(ValueError):
            int_from_base8('abc')  # No valid digits

    def test_int_from_base16(self):
        """Test int_from_base16 function with various hexadecimal strings."""

        # Test valid hex strings
        self.assertEqual(int_from_base16('0'), 0)
        self.assertEqual(int_from_base16('1'), 1)
        self.assertEqual(int_from_base16('9'), 9)
        self.assertEqual(int_from_base16('a'), 10)
        self.assertEqual(int_from_base16('A'), 10)
        self.assertEqual(int_from_base16('f'), 15)
        self.assertEqual(int_from_base16('F'), 15)
        self.assertEqual(int_from_base16('10'), 16)
        self.assertEqual(int_from_base16('1f'), 31)
        self.assertEqual(int_from_base16('20'), 32)
        self.assertEqual(int_from_base16('ff'), 255)
        self.assertEqual(int_from_base16('FF'), 255)
        self.assertEqual(int_from_base16('100'), 256)

        # Test longer hex strings
        self.assertEqual(int_from_base16('ffff'), 65535)
        self.assertEqual(int_from_base16('10000'), 65536)

        # Test edge cases
        self.assertEqual(int_from_base16('0000'), 0)
        self.assertEqual(int_from_base16('0001'), 1)

        # Test error cases
        with self.assertRaises(ValueError):
            int_from_base16('g')  # Invalid hex digit

        with self.assertRaises(ValueError):
            int_from_base16('1g')  # Invalid hex digit

        with self.assertRaises(ValueError):
            int_from_base16('')  # Empty string

        with self.assertRaises(ValueError):
            int_from_base16('xyz')  # No valid digits

    def test_lowercase_value_string(self):
        """Test lowercase_value function with string inputs."""

        # Test basic string conversion
        self.assertEqual(lowercase_value('Hello'), 'hello')
        self.assertEqual(lowercase_value('WORLD'), 'world')
        self.assertEqual(lowercase_value('MiXeD'), 'mixed')
        self.assertEqual(lowercase_value(''), '')
        self.assertEqual(lowercase_value('123'), '123')
        self.assertEqual(lowercase_value('!@#'), '!@#')

        # Test unicode strings
        self.assertEqual(lowercase_value('HÉLLÖ'), 'héllö')
        self.assertEqual(lowercase_value('ÑOÑO'), 'ñoño')

    def test_lowercase_value_tuple(self):
        """Test lowercase_value function with tuple inputs."""

        # Test tuple with strings
        input_tuple = ('Hello', 'WORLD', 'MiXeD')
        expected = ('hello', 'world', 'mixed')  # Function returns a list, not tuple
        result = lowercase_value(input_tuple)
        self.assertEqual(result, expected)

        # Test tuple with mixed types
        input_tuple = ('Hello', 123, 'WORLD', 45.67, 'MiXeD')
        expected = ('hello', 123, 'world', 45.67, 'mixed')  # Function returns a list
        result = lowercase_value(input_tuple)
        self.assertEqual(result, expected)

        # Test empty tuple
        self.assertEqual(lowercase_value(()), ())  # Function returns empty list

        # Test single element tuple
        self.assertEqual(lowercase_value(('Hello',)), ('hello',))  # Function returns list

        # Test nested tuples (should not be processed)
        input_tuple = ('Hello', ('WORLD', 'MiXeD'))
        expected = ('hello', ('WORLD', 'MiXeD'))  # Nested tuple unchanged, but result is
        # tuple
        result = lowercase_value(input_tuple)
        self.assertEqual(result, expected)

    def test_lowercase_value_numpy_array(self):
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

    def test_lowercase_value_other_types(self):
        """Test lowercase_value function with non-string types."""

        # Test numeric types (should be unchanged)
        self.assertEqual(lowercase_value(123), 123)
        self.assertEqual(lowercase_value(45.67), 45.67)
        self.assertEqual(lowercase_value(True), True)
        self.assertEqual(lowercase_value(False), False)
        self.assertEqual(lowercase_value(None), None)

        # Test list (should be unchanged)
        input_list = ['Hello', 'WORLD']
        result = lowercase_value(input_list)
        self.assertEqual(result, input_list)  # Lists are not processed

        # Test dict (should be unchanged)
        input_dict = {'key': 'value'}
        result = lowercase_value(input_dict)
        self.assertEqual(result, input_dict)  # Dicts are not processed

        # Test custom object (should be unchanged)
        class CustomObject:
            pass
        custom_obj = CustomObject()
        result = lowercase_value(custom_obj)
        self.assertEqual(result, custom_obj)

    def test_lowercase_value_edge_cases(self):
        """Test lowercase_value function with edge cases."""

        # Test very long strings
        long_string = 'A' * 1000
        result = lowercase_value(long_string)
        self.assertEqual(result, 'a' * 1000)

        # Test strings with special characters
        special_string = '!@#$%^&*()_+-=[]{}|;:\',./<>?'
        result = lowercase_value(special_string)
        self.assertEqual(result, special_string)  # Special chars unchanged

        # Test strings with numbers
        mixed_string = 'Hello123World456'
        result = lowercase_value(mixed_string)
        self.assertEqual(result, 'hello123world456')

        # Test strings with spaces
        spaced_string = '  Hello  World  '
        result = lowercase_value(spaced_string)
        self.assertEqual(result, '  hello  world  ')

    def test_lowercase_value_performance(self):
        """Test lowercase_value function performance with large inputs."""

        # Test with large numpy array
        large_array = np.array(['Hello'] * 10000)
        result = lowercase_value(large_array)
        self.assertEqual(len(result), 10000)
        self.assertEqual(result[0], 'hello')
        self.assertEqual(result[-1], 'hello')

        # Test with large tuple
        large_tuple = ('Hello',) * 1000
        result = lowercase_value(large_tuple)
        self.assertEqual(len(result), 1000)
        self.assertEqual(result[0], 'hello')
        self.assertEqual(result[-1], 'hello')
