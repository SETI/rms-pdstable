##########################################################################################
# pdstable/__init__.py
##########################################################################################

import contextlib
import itertools
import os
from pathlib import Path
from typing import Any
import warnings

import numpy as np
from pdsparser import Pds3Label

from .pdsxtable import PdsTableInfo, PdsColumnInfo
from .pds3table import (Pds3TableInfo,
                        PDS3_VOLUME_COLNAMES_lc,
                        PDS3_FILE_SPECIFICATION_COLUMN_NAMES_lc)
from .pds4table import (Pds4TableInfo,
                        PDS4_BUNDLE_COLNAMES_lc,
                        PDS4_FILE_SPECIFICATION_COLUMN_NAMES_lc)
from .utils import is_pds4_label, lowercase_value, tai_from_iso, STRING_TYPES

try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    __version__ = 'Version unspecified'


# The default number of rows that PdsTable.iter_dicts reads and parses at a time
_DEFAULT_CHUNK_ROWS = 1000

# This is mainly to make the documentation look good
__all__ = ['PdsColumnInfo', 'PdsTable', 'PdsTableInfo']


class PdsTable:
    """The PdsTable class holds the contents of a PDS-labeled table.

    It is represented by a list of Numpy arrays, one for each column.

    Current limitations for PDS3:
        (1) ASCII tables only, no binary formats.
        (2) Detached PDS labels only.
        (3) Only one data file per label.
        (4) No row or record offsets in the label's pointer to the table file.
        (5) CONTAINER objects in the label are not supported.
        (6) Columns containing multiple items are not loaded.
        (7) Time fields are represented as character strings unless explicitly listed for
            conversion.
    """
    def __init__(self, label_file, *, label_contents=None, times=None, columns=None,
                 nostrip=None, callbacks=None, ascii=False,  # noqa: A002
                 replacements=None, invalid=None, valid_ranges=None, table_callback=None,
                 merge_masks=False, filename_keylen=0, row_range=None, table_file=None,
                 label_method='strict', fmt_dirs=None, defer_load=False):
        """Constructor for a PdsTable object.

        Parameters:
            label_file (str | Path | FCPath): The path to the PDS label of the table file.
                Must be supplied to get proper relative path resolution.
            label_contents (str | list[str] | dict[str, Any] | Pds3Label, optional):
                The contents of the label as a single string or a list of strings if we
                shouldn't read it from the file. Alternatively, a parsed label as a dict,
                or a Pds3Label object, to avoid label parsing entirely. Note: this param
                is for PDS3 labels only; it is ignored for PDS4.
            columns (list[str] | None, optional): An optional list of the names of the
                columns to return. If the list is empty, then every column is returned.
            times (list[str] | None, optional): An optional list of the names of time
                columns to be stored as floats in units of seconds TAI rather than as
                strings.
            nostrip (list[str] | None, optional): An optional list of the names of string
                columns that are not to be stripped of surrounding whitespace.
            callbacks (dict[str, Callable[..., str | bytes]] | None, optional): An
                optional dictionary that returns a callback function given the name of a
                column. If a callback is provided for any column, then the function is
                called on the string value of that column before it is parsed. This can be
                used to update known syntax errors in a particular table. The callback
                receives and returns bytes if `ascii` is True, str otherwise.
            ascii (bool, optional): True to interpret the callbacks as translating
                ASCII byte strings; False to interpret them as translating the default str
                type (Unicode).
            replacements (dict[str, dict[Any, Any]] | None, optional): An optional
                dictionary that returns a replacement dictionary given the name of a
                column. If a replacement dictionary is provided for any column, then any
                value in that column (as a string or as its native value) that matches a
                key in the dictionary is replaced by the value resulting from the
                dictionary lookup.
            invalid (dict[str, list[Any] | set[Any] | float | str] | None, optional): An
                optional dictionary keyed by column name. The returned value must be a
                list or set of values, or a single number or string, that are to be
                treated as invalid, missing, or unknown. An optional entry keyed by
                "default" can be a list or set of values that are invalid by default;
                these are used for any column whose name does not appear as a key in the
                dictionary.
            valid_ranges (dict[str, tuple[float, float] | list[float]] | None, optional):
                An optional dictionary keyed by column name. The returned value must be a
                tuple or list containing the minimum and maximum numeric values in that
                column.
            table_callback (Callable[[list[bytes]], list[bytes]] | None, optional): An
                optional function to be called after reading the data table contents
                before processing them. Note that this callback must handle bytestrings.
            merge_masks (bool, optional): True to return a single mask value for each
                column, regardless of how many items might be in that column. False to
                return a separate mask value for each value in a column.
            filename_keylen (int, optional): Number of characters in the filename to use
                as the key of the index if this table is to be indexed by filename. Zero
                to use the entire file basename after stripping off the extension.
            row_range (tuple[int, int] | list[int] | None, optional): A tuple or list of
                integers containing the index of the first row to read and the first row
                to omit. If not specified, then all the rows are read.
            table_file (str | int | None, optional): Specify a table file name to be read
                or an integer (1-based) representing the order in which the table appears
                in the label file. If the provided table name doesn't exist in the label
                or the integer is out of the range, an error will be raised. Only relevant
                for PDS4 labels.
            label_method (str, optional): The method to use to parse the label. Valid
                values are 'strict' (default) or 'fast'. The 'fast' method is faster but
                may not be as accurate. Only relevant for PDS3 labels.
            fmt_dirs (str | Path | FCPath | list[str | Path | FCPath] | None, optional):
                One or more directories to search for the ".FMT" files named by
                ^STRUCTURE keywords in a PDS3 label, after the directory containing the
                label file. Each ^STRUCTURE keyword is replaced by the columns its ".FMT"
                file describes. Only relevant for PDS3 labels.
            defer_load (bool, optional): True to read only the label now, and read the
                table file when its data is first needed: by :attr:`column_values`,
                :attr:`column_masks`, :meth:`get_column`, :meth:`get_column_mask`,
                :meth:`dicts_by_row`, the ``find_*`` methods, or the filename index.
                Properties that come from the label, such as :attr:`rows`, never read
                the table file. :meth:`iter_dicts` on a deferred table reads the file a
                chunk at a time without loading the whole table. Errors and warnings
                about the table file's contents are then raised by whichever of these
                first reads it.

        Raises:
            FileNotFoundError: If a ".FMT" file named by a ^STRUCTURE keyword in a PDS3
                label is not in the label's directory or any of `fmt_dirs`.
            OSError: If the label or table file cannot be read.
            ValueError: If the label or table contents are invalid or unsupported, for
                example a column with an unsupported data type, or if `row_range` or
                `table_file` does not identify rows or a table in the label. Also raised
                if `label_contents` is a Pds3Label or dict that was parsed without
                expanding its ^STRUCTURE keywords.

        Warns:
            UserWarning: If a PDS3 table contains an object other than COLUMN, such as a
                CONTAINER, whose columns are therefore not loaded; or if the number of
                COLUMN objects differs from the table's COLUMNS value.

        Notes:
            If both a replacement and a callback are provided for the same column, the
            callback is applied first. The invalid and valid_ranges parameters are applied
            afterward.

            Note that performance will be slightly faster if ascii=True.
        """

        if times is None:
            times = []
        if columns is None:
            columns = []
        if nostrip is None:
            nostrip = []
        if callbacks is None:
            callbacks = {}
        if replacements is None:
            replacements = {}
        if invalid is None:
            invalid = {}
        if valid_ranges is None:
            valid_ranges = {}

        self._is_pds4_lbl = is_pds4_label(label_file)
        self._info = PdsTable._table_info(label_file, label_contents=label_contents,
                                          invalid=invalid, valid_ranges=valid_ranges,
                                          table_file=table_file,
                                          label_method=label_method, fmt_dirs=fmt_dirs)
        self._encoding = {'encoding': 'utf-8' if self._is_pds4_lbl else 'latin-1'}

        # Select the columns
        if len(columns) == 0:
            self._keys = [info.name for info in self._info.column_info_list]
        else:
            self._keys = columns
        # self._keys is an ordered list containing the name of every column to be returned

        self._keys_lc = [k.lower() for k in self._keys]

        # Raise KeyError now, not when the data is loaded, for a column not in the table
        for key in self._keys:
            self._info.column_info_dict[key]

        # Options applied whenever lines of the table are parsed
        self._label_file = label_file
        self._times = times
        self._nostrip = nostrip
        self._callbacks = callbacks
        self._ascii = ascii
        self._replacements = replacements
        self._merge_masks = merge_masks
        self._table_callback = table_callback

        # Select the rows
        self._row_range = row_range
        if row_range is None:
            self._first = 0
            self._rows = self._info.rows
        else:
            if not self._info.fixed_length_row:
                raise ValueError('Cannot specify row range for the table without fixed '
                                 'length rows.')

            self._first = row_range[0]
            self._rows = row_range[1] - row_range[0]
            if self._rows <= 0:
                raise ValueError('row_range must have at least one row')

        # The column data, read by _load() now or when first needed
        self._column_values = None
        self._column_masks = None

        # Columns whose illegally formatted values iter_dicts has already reported
        self._warned_columns = set()

        # Cache dicts_by_row and other info when first requested
        self._filename_keylen = filename_keylen
        self._dicts_by_row = {}

        self._volume_colname_index   = None
        self._volume_colname         = None
        self._volume_colname_lc      = None

        self._filespec_colname_index = None
        self._filespec_colname       = None
        self._filespec_colname_lc    = None

        self._rows_by_filename = None
        self._filename_keys    = None

        if not defer_load:
            self._load()

    def __iter__(self):
        """Iterate over the rows of the table as dictionaries.

        This is the same as :meth:`iter_dicts` with its default arguments.

        Returns:
            Iterator[dict[str, Any]]: One dictionary per row; see :meth:`iter_dicts`.
        """

        return self.iter_dicts()

    def iter_dicts(self, chunk_rows=_DEFAULT_CHUNK_ROWS, *, lowercase=(False, False)):
        """Iterate over the rows of the table as dictionaries, reading a chunk at a time.

        Each dictionary is identical to the corresponding entry of :meth:`dicts_by_row`
        with the same `lowercase`. The rows are those selected by the constructor's
        `row_range`, or every row of the table.

        If the table data has not been loaded (the table was constructed with
        `defer_load=True` and nothing has needed the data since), the table file is read
        `chunk_rows` rows at a time, and only the current chunk is held in memory. Each
        chunk is parsed with the constructor's options; note that `table_callback`
        therefore receives one chunk of lines at a time rather than the whole table. The
        file is opened when iteration starts and closed when it ends or the iterator is
        closed. Nothing is cached, so each iteration reads the file again.

        If the table data has already been loaded, the rows come from memory and
        `chunk_rows` has no effect.

        Parameters:
            chunk_rows (int, optional): The number of rows to read and parse at a time.
            lowercase (bool | tuple[bool, bool], optional): As for :meth:`dicts_by_row`.

        Returns:
            Generator[dict[str, Any]]: One dictionary per row, in table order.

        Raises:
            ValueError: Immediately, if `chunk_rows` is less than one. During iteration,
                if the table file has fewer rows than selected; or, when no `row_range`
                was given, more rows than the label states, after the last row has been
                yielded. Rows yielded before the error are valid.
            OSError: During iteration, if the table file cannot be read.

        Warns:
            UserWarning: When a chunk contains illegally formatted values in a column.
                The message gives the count for that chunk and the chunk's rows (0-based
                row numbers in the table file). Each column is reported at most once per
                table, however many chunks or iterations contain such values; this does
                not affect the warnings issued when the whole table is loaded.
        """

        if chunk_rows < 1:
            raise ValueError(f'chunk_rows must be at least 1: {chunk_rows}')

        if isinstance(lowercase, bool):
            lowercase = (lowercase, lowercase)

        if self._column_values is not None:
            return (self._row_dict(self._column_values, self._column_masks, row,
                                   lowercase)
                    for row in range(self._rows))

        return self._stream_dicts(chunk_rows, lowercase)

    def _stream_dicts(self, chunk_rows, lowercase):
        """Read, parse, and yield the selected rows of the table file a chunk at a time.

        Parameters:
            chunk_rows (int): The number of rows to read and parse at a time.
            lowercase (tuple[bool, bool]): As for :meth:`dicts_by_row`.

        Yields:
            dict[str, Any]: One dictionary per row.

        Raises:
            ValueError: If the table file does not hold the rows the label or `row_range`
                calls for.
        """

        with self._open_table() as f:
            done = 0
            while done < self._rows:
                lines = list(itertools.islice(f, min(chunk_rows, self._rows - done)))
                if len(lines) == 0:
                    raise self._row_count_error(done)

                values, masks, errors = self._parse_lines(lines)
                first = self._first + done
                for column_info, count, example in errors:
                    if column_info.name in self._warned_columns:
                        continue
                    self._warned_columns.add(column_info.name)
                    message = self._illegal_values_message(
                        column_info, count, example, rows=(first, first + len(lines)))
                    warnings.warn(message, stacklevel=2)

                for row in range(len(lines)):
                    yield self._row_dict(values, masks, row, lowercase)

                done += len(lines)
                if len(lines) < chunk_rows and done < self._rows:
                    raise self._row_count_error(done)

            if self._row_range is None:
                extra = sum(1 for _ in f)
                if extra:
                    raise self._row_count_error(self._rows + extra)

    @contextlib.contextmanager
    def _open_table(self):
        """Open the table file, positioned at the first selected row.

        The file is closed when the context exits.

        Yields:
            BufferedReader: The open table file, in binary mode.
        """

        with open(self._info.table_file_path, 'rb') as f:
            offset = self._info.header_bytes
            if self._first:
                offset += self._first * self._info.row_bytes
            f.seek(offset)
            yield f

    def _row_count_error(self, found):
        """Return the error for a table file that does not hold the selected rows.

        Parameters:
            found (int): The number of rows found: in the whole file if no `row_range`
                was given, otherwise in the selected range.

        Returns:
            ValueError: The exception to raise.
        """

        if self._row_range is None:
            return ValueError(f'row count mismatch in {self._label_file}: '
                              f'{found} rows in file; '
                              f'label says {self._info.rows} rows')
        return ValueError(f'row count mismatch: {found} row(s) read; '
                          f'{self._rows} row(s) requested')

    @staticmethod
    def _illegal_values_message(column_info, count, example, rows=None):
        """Return the warning text for illegally formatted values in one column.

        Parameters:
            column_info (PdsColumnInfo): The column.
            count (int): The number of illegally formatted values.
            example (str): The first illegally formatted value.
            rows (tuple[int, int] | None, optional): The first row checked and the first
                row after it, if only part of the table was checked.

        Returns:
            str: The warning text.
        """

        where = '' if rows is None else f' in rows {rows[0]}-{rows[1] - 1}'
        if count == 1:
            return (f'Illegally formatted {column_info.data_type} value in column '
                    f'{column_info.name}{where}: {example.strip()}')
        return (f'{count!s} illegally formatted {column_info.data_type} values in '
                f'column {column_info.name}{where}; first example is '
                f'"{example.strip()}"')

    def _load(self):
        """Read and parse every selected row of the table, unless that is already done.

        Raises:
            OSError: If the table file cannot be read.
            ValueError: If the table file does not hold the rows the label or `row_range`
                calls for, or its contents do not match the label.

        Warns:
            UserWarning: For each column that contains illegally formatted values.
        """

        if self._column_values is not None:
            return

        with self._open_table() as f:
            lines = list(itertools.islice(f, self._rows))
            if len(lines) != self._rows:
                raise self._row_count_error(len(lines))
            if self._row_range is None:
                extra = sum(1 for _ in f)
                if extra:
                    raise self._row_count_error(self._rows + extra)

        values, masks, errors = self._parse_lines(lines)
        for column_info, count, example in errors:
            warnings.warn(self._illegal_values_message(column_info, count, example),
                          stacklevel=3)

        self._column_values = values
        self._column_masks = masks

    def _parse_lines(self, lines):
        """Convert lines of the table file into column values and masks.

        Parameters:
            lines (list[bytes]): Consecutive rows of the table file, each with its line
                terminator.

        Returns:
            tuple[dict[str, Any], dict[str, numpy.ndarray], list[tuple]]: The values
            and masks of each selected column, keyed by column name; and, for each
            column with illegally formatted values, a tuple of its
            :class:`PdsColumnInfo`, the number of such values, and the first of them.

        Raises:
            ValueError: If the lines do not match the row description in the label.
        """

        if self._table_callback is not None:
            lines = self._table_callback(lines)

        # For table file with fixed length row:
        # table is now a 1-D array in which the ASCII content of each column
        # can be accessed by name. These are bytes, not strings
        if self._info.fixed_length_row:
            table = np.array(lines)
            try:
                table = table.view(np.dtype(self._info.dtype0))
            except ValueError as e:
                raise ValueError('Error in row description:\n'
                                 f'old dtype = {table.dtype};\n'
                                 f'new dtype = {np.dtype(self._info.dtype0)}') from e
        # For a table file that doesn't have fixed length row, like a .csv file:
        # table is a 2-D array, each row is an array of the column values for the row.
        else:
            table = np.array([np.array(line.split(self._info.field_delimiter))
                              for line in lines])

        # Extract the substring arrays and save in a dictionary...
        column_values = {}
        column_masks = {}
        errors = []

        for idx, key in enumerate(self._keys):
            column_info = self._info.column_info_dict[key]
            if self._info.fixed_length_row:
                column = table[key]
            else:
                # Use indexing to access the values of a column for all the rows if the
                # table rows are not fixed length
                column = table[:, idx]

            # column is now a 1-D array containing the ASCII content of this
            # column within each row.

            # For multiple items...
            if self._info.fixed_length_row and column_info.items > 1:

                # Replace the column substring with a list of sub-substrings
                column = column.view(np.dtype(column_info.dtype1))

                items = []
                masks = []
                for i in range(column_info.items):
                    item = column[f'item_{i}']
                    items.append(item)
                    masks.append(False)
                # items is now a list containing one 1-D array for each item in this
                # column.

                column_values[key] = items
            else:
                column_values[key] = [column]

        # Replace each 1-D array of items from ASCII strings to the proper type
        for key in self._keys:
            column_info  = self._info.column_info_dict[key]
            column_items = column_values[key]

            data_type = column_info.data_type
            dtype     = column_info.dtype2
            func      = column_info.scalar_func
            callback  = self._callbacks.get(key)
            repdict   = self._replacements.get(key, {})
            strip     = (key not in self._nostrip)

            invalid_values = column_info.invalid_values
            valid_range    = column_info.valid_range

            error_count    = 0
            error_example  = None

            # For each item in the column...
            new_column_items = []
            new_column_masks = []
            for items in column_items:

                invalid_mask = np.zeros(len(items), dtype='bool')

                # Apply the callback if any
                if callback:

                    # Convert string to input format for callback
                    if not self._ascii:
                        items = items.astype('U')

                    # Apply the callback row by row
                    new_items = []
                    for item in items:
                        new_item = callback(item)
                        new_items.append(new_item)

                    items = np.array(new_items)

                # Apply the replacement dictionary if any pairs are strings
                for (before, after) in repdict.items():
                    if not isinstance(before, STRING_TYPES):
                        continue
                    if not isinstance(after,  STRING_TYPES):
                        continue

                    # The file is read as binary, so the replacements have to be applied
                    # as ASCII byte strings

                    if isinstance(before, (str, np.str_)):
                        before = before.encode(**self._encoding)

                    if isinstance(after, (str, np.str_)):
                        after  = after.encode(**self._encoding)

                    # Replace values (suppressing FutureWarning)
                    items = items.astype('S')
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        items[items == before] = after

                # Handle the data type...

                # Handle a string
                if data_type == 'string_preserved':
                    items = items.astype('U')  # No strip

                elif (data_type == 'string'
                      or (data_type == 'time' and key not in self._times)):
                    items = items.astype('U')

                    if strip:
                        items = [i.strip() for i in items]
                        items = np.array(items)

                # If this is an int, float or time...

                # Try to convert array dtype
                else:
                    try:
                        items = items.astype(dtype)

                        # Apply the replacements for pairs of this type
                        for (before, after) in repdict.items():
                            with warnings.catch_warnings():
                                warnings.simplefilter('ignore')
                                items[items == before] = after

                        # Convert times if necessary
                        if key in self._times:
                            items = tai_from_iso(items)

                    # If something went wrong, array processing won't work.
                    # Convert to list and process row by row
                    except Exception:
                        # Process row by row
                        new_items = []
                        for k, item in enumerate(items):
                            try:
                                # Translate the item
                                item = func(item)

                                # Apply a possible replacement
                                item = repdict.get(item, item)

                            # If something went wrong...
                            except Exception:
                                invalid_mask[k] = True

                                error_count += 1
                                if not isinstance(item, str):
                                    item = item.decode(**self._encoding)

                                if strip:
                                    item = item.strip()

                                if error_example is None:
                                    error_example = item

                            # Apply validity criteria to this row
                            invalid_mask[k] |= (item in invalid_values)
                            if valid_range:
                                invalid_mask[k] |= (item < valid_range[0])
                                invalid_mask[k] |= (item > valid_range[1])

                            new_items.append(item)

                        items = new_items

                # Determine validity mask if not already done
                if isinstance(items, np.ndarray):
                    for invalid_value in invalid_values:
                        # Hide FutureWarning for comparisons of different types
                        with warnings.catch_warnings():
                            warnings.simplefilter('ignore')
                            invalid_mask |= (items == invalid_value)

                    if valid_range:
                        # Hide FutureWarning for comparisons of different types
                        with warnings.catch_warnings():
                            warnings.simplefilter('ignore')
                            invalid_mask |= (items < valid_range[0])
                            invalid_mask |= (items > valid_range[1])

                new_column_items.append(items)
                new_column_masks.append(invalid_mask)

            # Swap indices for multiple items
            if len(new_column_items) == 1:
                column_values[key] = new_column_items[0]
                column_masks[key]  = new_column_masks[0]

            else:
                all_arrays = np.all([isinstance(c, np.ndarray) for c in new_column_items])

                if all_arrays:
                    array = np.stack(new_column_items, axis=1)
                    if array.dtype.kind in ('S', 'U'):
                        array = [tuple(x) for x in array]
                    column_values[key] = array
                else:
                    column_values[key] = list(zip(*new_column_items, strict=True))

                if self._merge_masks:
                    column_masks[key] = np.any(np.stack(new_column_masks), axis=0)
                else:
                    mask_array = np.stack(new_column_masks)
                    column_masks[key] = mask_array.swapaxes(0, 1)

            if error_count:
                errors.append((column_info, error_count, error_example))

        return column_values, column_masks, errors


    @staticmethod
    def _table_info(label_file, *, label_contents, invalid, valid_ranges, table_file,
                    label_method, fmt_dirs):
        """Parse a PDS3 or PDS4 label into the description of its table.

        The table file itself is not read.

        Parameters:
            label_file (str | Path | FCPath): The path to the label.
            label_contents (str | list[str] | dict[str, Any] | Pds3Label | None): The
                label contents, for PDS3 labels; see :class:`PdsTable`.
            invalid (dict[str, list[Any] | set[Any] | float | str]): Invalid values by
                column name.
            valid_ranges (dict[str, tuple[float, float] | list[float]]): Valid ranges by
                column name.
            table_file (str | int | None): The table to select, for PDS4 labels.
            label_method (str): The PDS3 label parsing method.
            fmt_dirs (str | Path | FCPath | list[str | Path | FCPath] | None): The
                directories to search for PDS3 ".FMT" files.

        Returns:
            PdsTableInfo: The description of the table.

        Raises:
            ValueError: If `table_file` is given for a PDS3 label, or if the label does
                not describe a readable table.
        """

        if is_pds4_label(label_file):
            return Pds4TableInfo(label_file, invalid=invalid, valid_ranges=valid_ranges,
                                 table_file=table_file)
        if table_file is not None:
            raise ValueError('table_file is not supported for PDS3 labels')
        return Pds3TableInfo(label_file, label_contents=label_contents, invalid=invalid,
                             valid_ranges=valid_ranges, label_method=label_method,
                             fmt_dirs=fmt_dirs)

    @staticmethod
    def rows_from_label(label_file, *, label_contents=None, table_file=None,
                        label_method='strict', fmt_dirs=None):
        """Return the number of rows in a table, as stated by its label.

        Only the label is read, so the table file does not need to exist. The result is
        the label's row count (ROWS for PDS3, records for PDS4), not the number of rows
        a :class:`PdsTable` would load with a `row_range`.

        Parameters:
            label_file (str | Path | FCPath): The path to the PDS3 or PDS4 label of the
                table file.
            label_contents (str | list[str] | dict[str, Any] | Pds3Label, optional):
                The contents of a PDS3 label, to use instead of reading `label_file`; see
                :class:`PdsTable`. It is ignored for PDS4.
            table_file (str | int | None, optional): For a PDS4 label, the table to
                count: a regular expression matching its file name, or its 1-based
                position in the label. Required if the label describes more than one
                table. Not supported for PDS3 labels.
            label_method (str, optional): The method used to parse a PDS3 label, 'strict'
                (default) or 'fast'. Only relevant for PDS3 labels.
            fmt_dirs (str | Path | FCPath | list[str | Path | FCPath] | None, optional):
                Directories to search for the ".FMT" files named by ^STRUCTURE keywords
                in a PDS3 label, after the directory containing the label. Only relevant
                for PDS3 labels.

        Returns:
            int: The number of rows in the table.

        Raises:
            FileNotFoundError: If the label, or a ".FMT" file it names, cannot be found.
            ValueError: If `table_file` is given for a PDS3 label, does not identify a
                table in a PDS4 label, or is omitted for a PDS4 label with more than one
                table; or if the label does not describe a table that :class:`PdsTable`
                can read.

        Warns:
            UserWarning: Under the same conditions as the :class:`PdsTable` constructor.
        """

        info = PdsTable._table_info(label_file, label_contents=label_contents,
                                    invalid={}, valid_ranges={}, table_file=table_file,
                                    label_method=label_method, fmt_dirs=fmt_dirs)
        return info.rows

    @property
    def pdslabel(self) -> Pds3Label | dict[str, Any]:
        """The label of the table as a Pds3Label for PDS3 or dict for PDS4."""
        return self._info.label

    @property
    def label_file_name(self) -> str:
        """The name of the label file (without the path)."""
        return self._info.label_file_name

    @property
    def label_file_path(self) -> Path:
        """The local path to the label file."""
        return self._info.label_file_path

    @property
    def table_file_name(self) -> str:
        """The name of the table file (without the path)."""
        return self._info.table_file_name

    @property
    def table_file_path(self) -> Path:
        """The local path to the table file."""
        return self._info.table_file_path

    @property
    def is_pds4(self) -> bool:
        """True if the read label was a PDS4 label, False otherwise."""
        return self._is_pds4_lbl

    @property
    def rows(self) -> int:
        """The number of rows that were read."""
        return self._rows

    @property
    def first(self) -> int:
        """The index of the first row that was read (0-based)."""
        return self._first

    @property
    def columns(self) -> int:
        """The number of columns in the table (possibly as restricted by the columns
        parameter)."""
        return len(self._keys)

    @property
    def all_columns(self) -> int:
        """The number of columns in the table (possibly as restricted by the columns
        parameter)."""
        return self._info.columns

    @property
    def column_values(self) -> dict[str, np.ndarray | list[tuple]]:
        """The values of the columns that were read as a dict indexed by column name."""
        self._load()
        return self._column_values

    @property
    def column_masks(self) -> dict[str, np.ndarray]:
        """The masks of the columns that were read as a dict indexed by column name."""
        self._load()
        return self._column_masks

    @property
    def column_info_list(self) -> list[PdsColumnInfo]:
        """The list of PdsColumnInfo objects for the columns in the table.

        This list includes ALL of the columns, not just the ones restricted by the columns
        parameter.
        """
        return self._info.column_info_list

    @property
    def column_info_dict(self) -> dict[str, PdsColumnInfo]:
        """The dict of PdsColumnInfo objects for the columns in the table, keyed by the
        column name.

        This dict includes ALL of the columns, not just the ones restricted by the columns
        parameter.
        """
        return self._info.column_info_dict

    @property
    def header_bytes(self) -> int:
        """The number of bytes in the header of the table."""
        return self._info.header_bytes

    @property
    def encoding(self) -> str:
        """The encoding of the table file (e.g., 'utf-8' or 'latin-1')."""
        return self._encoding['encoding']

    @property
    def fixed_length_row(self) -> bool:
        """True if the table has fixed-length rows."""
        return self._info.fixed_length_row

    @property
    def field_delimiter(self) -> bytes | None:
        """The field delimiter for the table."""
        return self._info.field_delimiter

    @property
    def row_bytes(self) -> int | None:
        """The number of bytes per row (the maximum for a delimited table), if known."""
        return self._info.row_bytes

    @property
    def dtype0(self) -> dict[str, tuple[str, int]]:
        """The dtype dictionary for the table, keyed by the column name.

        Each value is a tuple of (dtype_string, start_byte) where dtype_string is the
        string representation of the dtype used to isolate the column (e.g., 'S10' for a
        10-character string) and start_byte is the starting byte position of the column in
        a row.
        """
        return self._info.dtype0

    @property
    def info(self) -> PdsTableInfo:
        """The Pds3/4TableInfo object that holds the attributes of the table.

        DEPRECATED.
        """
        return self._info

    ######################################################################################
    # Support for extracting rows and columns
    ######################################################################################

    def dicts_by_row(self, lowercase=(False, False)):
        """Returns a list of dictionaries, one for each row in the table.

        Each dictionary contains all of the column values in that particular row. The
        dictionary keys are the column names; append "_mask" to the key to get the mask
        value, which is True if the column value is invalid; False otherwise.

        Parameters:
            lowercase (bool | tuple[bool, bool], optional): A tuple of two booleans. If
                the first is True, then the dictionary is also keyed by column names
                converted to lower case. If the second is True, then keys with "_lower"
                appended return values converted to lower case. If a single boolean is
                provided, it will be duplicated for both parameters.

        Returns:
            list[dict[str, Any]]: A list of dictionaries, one for each row in the table.
        """

        # Duplicate the lowercase value if only one is provided
        if isinstance(lowercase, bool):
            lowercase = (lowercase, lowercase)

        # If we already have the needed list of dictionary, return it
        try:
            return self._dicts_by_row[lowercase]
        except KeyError:
            pass

        self._load()
        row_dicts = [self._row_dict(self._column_values, self._column_masks, row,
                                    lowercase)
                     for row in range(self.rows)]

        # Cache results for later re-use
        self._dicts_by_row[lowercase] = row_dicts

        return row_dicts

    def _row_dict(self, values, masks, row, lowercase):
        """Build the dictionary for one row, as returned by :meth:`dicts_by_row`.

        Parameters:
            values (dict[str, Any]): The column values, keyed by column name.
            masks (dict[str, numpy.ndarray]): The column masks, keyed by column name.
            row (int): The index of the row within `values` and `masks`.
            lowercase (tuple[bool, bool]): As for :meth:`dicts_by_row`.

        Returns:
            dict[str, Any]: The row's dictionary.
        """

        row_dict = {}
        for (column_name, items) in values.items():

            key_set = {column_name}
            if not self.is_pds4:
                key_set = {column_name, column_name.replace(' ', '_')}

            for key in key_set:
                value = items[row]
                mask  = masks[key][row]

                # Key and value unchanged
                row_dict[key] = value
                row_dict[key + '_mask'] = mask

                # Key in lower case; value unchanged
                if lowercase[0]:
                    key_lc = key.lower()
                    row_dict[key_lc] = value
                    row_dict[key_lc + '_mask'] = mask

                # Value in lower case
                if lowercase[1]:
                    value_lc = lowercase_value(value)

                    row_dict[key + '_lower'] = value_lc
                    if lowercase[0]:
                        row_dict[key_lc + '_lower'] = value_lc

        return row_dict

    def get_column(self, name):
        """Return the values in the specified column as a list.

        Parameters:
            name (str): The name of the column to retrieve.

        Returns:
            numpy.ndarray | list[tuple]: The values in the specified column. A column with
            multiple items that are not all arrays is returned as a list of tuples.
        """

        self._load()
        return self._column_values[name]

    def get_column_mask(self, name):
        """Return the masks for the specified column as a list.

        Parameters:
            name (str): The name of the column to retrieve masks for.

        Returns:
            numpy.ndarray: The masks for the specified column.
        """

        self._load()
        return self._column_masks[name]

    def get_keys(self):
        """Get the list of column names that were actually loaded.

        Returns:
            list[str]: A list of column names.
        """

        return list(self._keys)

    ######################################################################################
    # Support for finding rows by specified column values
    ######################################################################################

    def find_row_indices(self, lowercase=(False, False), *, limit=None, substrings=None,
                         **params):
        """Find indices of rows where each named parameter equals the specified value.

        Parameters:
            lowercase (bool | tuple[bool, bool], optional): Whether to enable testing of
                the column name and value converted to lower case. This is a tuple of two
                booleans. If the first is True, then we also allow testing of an entry in
                `params` with a ``_lower`` suffix. If the second boolean is True, then
                such a column also converts the value to match lower case. If a single
                boolean is provided, it will be duplicated for both parameters.
            limit (int | None, optional): If not zero or None, this is the maximum number
                of matching rows that are returned.
            substrings (list[str] | None, optional): A list of column names for which a
                match occurs if the given parameter value is embedded within the string;
                an exact match is not required.
            **params (Any): Named parameters where each parameter name corresponds to a
                column name and the value is what to search for in that column.

        Returns:
            list[int]: A list of row indices that match the search criteria.
        """

        if substrings is None:
            substrings = []

        dicts_by_row = self.dicts_by_row(lowercase=lowercase)

        # Make a list (key, value, test_substring, mask_key)
        test_info = []
        for (key, match_value) in params.items():
            if key.endswith('_lower'):
                mask_key = key[:-6] + '_mask'
                match_value = lowercase_value(match_value)
                test_substring = (key in substrings or key[:-6] in substrings)
            else:
                mask_key = key + '_mask'
                test_substring = (key in substrings)

            test_info.append((key, match_value, test_substring, mask_key))

        matches = []

        # For each row in the table...
        for k, row_dict in enumerate(dicts_by_row):

            # Assume it's a match
            match = True

            # Apply each test...
            for (key, match_value, test_substring, mask_key) in test_info:

                # Reject all masked values
                if np.any(row_dict[mask_key]):
                    match = False
                    break

                # Test column value(s)
                column_values = row_dict[key]
                if test_substring:
                    if isinstance(column_values, str):
                        failures = [match_value not in column_values]
                    else:
                        failures = [match_value not in c for c in column_values]
                elif isinstance(column_values, (str, int, float)):
                    failures = [match_value != column_values]
                else:
                    failures = [match_value != c for c in column_values]

                if np.any(failures):
                    match = False
                    break

            # If there were no failures, we have a match
            if match:
                matches.append(k)
                if limit and len(matches) >= limit:
                    return matches

        return matches

    def find_row_index(self, lowercase=(False, False), *, substrings=None, **params):
        """Find the first row where each named parameter equals the specified value.

        Parameters:
            lowercase (bool | tuple[bool, bool], optional): Whether to enable testing of
                the column name and value converted to lower case. This is a tuple of two
                booleans. If the first is True, then we also allow testing of an entry in
                `params` with a ``_lower`` suffix. If the second boolean is True, then
                such a column also converts the value to match lower case. If a single
                boolean is provided, it will be duplicated for both parameters.
            substrings (list[str] | None, optional): A list of column names for which a
                match occurs if the given parameter value is embedded within the string;
                an exact match is not required.
            **params (Any): Named parameters where each parameter name corresponds to a
                column name and the value is what to search for in that column.

        Returns:
            int: The index of the first matching row.

        Raises:
            ValueError: If no matching row is found.
        """

        if substrings is None:
            substrings = []

        matches = self.find_row_indices(lowercase=lowercase, limit=1,
                                        substrings=substrings, **params)

        if matches:
            return matches[0]

        raise ValueError(f'row not found: {params}')

    def find_rows(self, lowercase=(False, False), **params):
        """Return a list of dicts representing rows where each named parameter equals
        the specified value.

        Parameters:
            lowercase (bool | tuple[bool, bool], optional): Whether to enable testing of
                the column name and value converted to lower case. This is a tuple of two
                booleans. If the first is True, then we also allow testing of an entry in
                `params` with a ``_lower`` suffix. If the second boolean is True, then
                such a column also converts the value to match lower case. If a single
                boolean is provided, it will be duplicated for both parameters.
            **params (Any): Named parameters where each parameter name corresponds to a
                column name and the value is what to search for in that column.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the matching rows.
            Each dictionary is keyed by column name.
        """

        indices = self.find_row_indices(lowercase=lowercase, **params)
        dicts_by_row = self.dicts_by_row()
        return [dicts_by_row[k] for k in indices]

    def find_row(self, lowercase=(False, False), **params):
        """Return a dict representing the first row where each named parameter
        equals the specified value.

        Parameters:
            lowercase (bool | tuple[bool, bool], optional): Whether to enable testing of
                the column name and value converted to lower case. This is a tuple of two
                booleans. If the first is True, then we also allow testing of an entry in
                `params` with a ``_lower`` suffix. If the second boolean is True, then
                such a column also converts the value to match lower case. If a single
                boolean is provided, it will be duplicated for both parameters.
            **params (Any): Named parameters where each parameter name corresponds to a
                column name and the value is what to search for in that column.

        Returns:
            dict[str, Any]: A dictionary representing the first matching row. The
            dictionary is keyed by column name.

        Raises:
            ValueError: If no matching row is found.
        """

        k = self.find_row_index(lowercase=lowercase, **params)
        dicts_by_row = self.dicts_by_row()
        return dicts_by_row[k]

    ######################################################################################
    # Support for finding rows by filename
    ######################################################################################

    def filename_key(self, filename):
        """Convert a filename to a key for indexing the rows.

        The key is the basename with the extension removed.

        Parameters:
            filename (str): The filename to convert to a key.

        Returns:
            str: The filename key for indexing.
        """

        basename = os.path.basename(filename)
        key = os.path.splitext(basename)[0]
        if self._filename_keylen and len(key) > self._filename_keylen:
            key = key[:self._filename_keylen]

        return key

    def bundle_column_index(self):
        """Get the index of the column containing volume IDs or bundle names.

        This is an alias for :meth:`~volume_column_index`.

        Returns:
            int: The index of the column containing volume IDs or bundle names, or -1 if
            none.
        """

        return self.volume_column_index()

    def volume_column_index(self):
        """Get the index of the column containing volume IDs or bundle names.

        Returns:
            int: The index of the column containing volume IDs or bundle names,
            or -1 if none.
        """

        if self.is_pds4:
            colnames = PDS4_BUNDLE_COLNAMES_lc
        else:
            colnames = PDS3_VOLUME_COLNAMES_lc

        if self._volume_colname_index is None:
            self._volume_colname_index = -1
            self._volume_colname = ''
            self._volume_colname_lc = ''

            for guess in colnames:
                if guess in self._keys_lc:
                    k = self._keys_lc.index(guess)
                    self._volume_colname_index = k
                    self._volume_colname_lc = guess
                    self._volume_colname = self._keys[k]
                    return k

        return self._volume_colname_index

    def filespec_column_index(self):
        """Get the index of the column containing the file specification name.

        For PDS3 tables, this is a column with a name like "file_specification_name".
        PDS4 tables do not have a standard name, so we look for some possible names.

        Returns:
            int: The index of the column containing the file specification name, or -1 if
            none.
        """

        if self._filespec_colname_index is None:
            self._filespec_colname_index = -1
            self._filespec_colname = ''
            self._filespec_colname_lc = ''

            for guess in self._filespec_column_guesses():
                if guess in self._keys_lc:
                    k = self._keys_lc.index(guess)
                    self._filespec_colname_index = k
                    self._filespec_colname_lc = guess
                    self._filespec_colname = self._keys[k]
                    return k

        return self._filespec_colname_index

    def _filespec_column_guesses(self):
        """Return the lower-case names that identify a file specification column.

        Returns:
            tuple[str, ...]: The names, in order of preference.
        """

        if self.is_pds4:
            return PDS4_FILE_SPECIFICATION_COLUMN_NAMES_lc
        return PDS3_FILE_SPECIFICATION_COLUMN_NAMES_lc

    def _require_filespec_column(self):
        """Raise ValueError unless the table has a file specification column.

        Raises:
            ValueError: If no loaded column has one of the names in
                :meth:`_filespec_column_guesses`.
        """

        if self.filespec_column_index() < 0:
            raise ValueError(f'Table "{self.table_file_name}" has no file specification '
                             'column; the names searched for are: '
                             f'{", ".join(self._filespec_column_guesses())}')

    def find_row_indices_by_bundle_filespec(self, bundle_name, filespec=None, *,
                                            limit=None, substring=False):
        """Find the row indices of the table with the specified bundle name and file
        specification name.

        This is an alias for :meth:`~find_row_indices_by_volume_filespec`.

        The search is case-insensitive.

        If the table does not contain the bundle name or if the given value of
        `bundle_name` is blank or not supplied, the search is performed on the `filespec`
        alone, ignoring the bundle name. Also, if only one argument is specified, it is
        treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            bundle_name (str): The bundle name to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `bundle_name` is treated as the `filespec`.
            limit (int | None, optional): Maximum number of matching rows to return.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            list[int]: A list of row indices that match the search criteria.

        Raises:
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        return self.find_row_indices_by_volume_filespec(bundle_name, filespec,
                                                        limit=limit, substring=substring)

    def find_row_indices_by_volume_filespec(self, volume_id, filespec=None, *, limit=None,
                                            substring=False):
        """Find the row indices of the table with the specified volume ID and file
        specification name.

        The search is case-insensitive.

        If the table does not contain the `volume_id` or if the given value of `volume_id`
        is blank or not supplied, the search is performed on the `filespec` alone. Also,
        if only one argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            volume_id (str): The volume ID to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `volume_id` is treated as the `filespec`.
            limit (int | None, optional): Maximum number of matching rows to return.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            list[int]: A list of row indices that match the search criteria.

        Raises:
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        self._require_filespec_column()
        dicts_by_row = self.dicts_by_row(lowercase=(True, True))

        if filespec is None:
            filespec = volume_id
            volume_id = ''

        # Without a volume ID or bundle name column, the search uses the filespec alone
        if self.volume_column_index() < 0:
            volume_colname = ''
        else:
            volume_colname = self._volume_colname_lc + '_lower'

        filespec_colname = self._filespec_colname_lc + '_lower'

        example = dicts_by_row[0][self._filespec_colname_lc]

        # Convert to VMS format for really old indices
        if not self.is_pds4 and '[' in example:
            parts = filespec.split('/')
            filespec = '[' + '.'.join(parts[:-1]) + ']' + parts[-1]

        # Copy the extension of the example
        filespec = os.path.splitext(filespec)[0]
        if not substring:
            ext = os.path.splitext(example)[1]
            filespec += ext

        # OK now search
        volume_id = volume_id.lower()
        filespec = filespec.lower()
        if substring:
            substrings = [filespec_colname]
        else:
            substrings = []
        if volume_colname and volume_id:
            return self.find_row_indices(lowercase=(True, True),
                                         substrings=substrings, limit=limit,
                                         **{filespec_colname: filespec,
                                            volume_colname: volume_id})
        else:
            return self.find_row_indices(lowercase=(True, True),
                                         substrings=substrings, limit=limit,
                                         **{filespec_colname: filespec})

    def find_row_index_by_bundle_filespec(self, bundle_name, filespec=None, *,
                                          substring=False):
        """Find the first row index with the specified bundle name and file specification
        name.

        This is an alias for :meth:`~find_row_index_by_volume_filespec`.

        The search is case-insensitive.

        If the table does not contain the `bundle_name` or if the given value of
        `bundle_name` is blank, the search is performed on the `filespec` alone. Also, if
        only one argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            bundle_name (str): The bundle name to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `bundle_name` is treated as the `filespec`.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            int: The index of the first matching row.

        Raises:
            ValueError: If no matching row is found, or if the table has no file
                specification column (see :meth:`filespec_column_index`).
        """

        return self.find_row_index_by_volume_filespec(bundle_name, filespec,
                                                      substring=substring)

    def find_row_index_by_volume_filespec(self, volume_id, filespec=None,
                                          substring=False):
        """Find the first row index with the specified volume ID and file specification
        name.

        The search is case-insensitive.

        If the table does not contain the `volume_id` or if the given value of `volume_id`
        is blank, the search is performed on the `filespec` alone. Also, if only one
        argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            volume_id (str): The volume ID to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `volume_id` is treated as the `filespec`.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            int: The index of the first matching row.

        Raises:
            ValueError: If no matching row is found, or if the table has no file
                specification column (see :meth:`filespec_column_index`).
        """

        indices = self.find_row_indices_by_volume_filespec(volume_id, filespec, limit=1,
                                                           substring=substring)
        if indices:
            return indices[0]

        if volume_id and not filespec:
            raise ValueError(f'row not found: filespec={volume_id}; ')
        elif volume_id:
            raise ValueError(f'row not found: volume_id={volume_id}; filespec={filespec}')
        else:
            raise ValueError(f'row not found: filespec={filespec}')

    def find_rows_by_bundle_filespec(self, bundle_name, filespec=None, *, limit=None,
                                     substring=False):
        """Find the rows of the table with the specified bundle name and file
        specification name.

        This is an alias for :meth:`~find_rows_by_volume_filespec`.

        The search is case-insensitive.

        If the table does not contain the `bundle_name` or if the given value of
        `bundle_name` is blank or not supplied, the search is performed on the `filespec`
        alone. Also, if only one argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        If input parameter `substring` is True, then a match occurs whenever the given
        `filespec` appears inside what is tabulated in the file, so a complete match is
        not required.

        Parameters:
            bundle_name (str): The bundle name to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `bundle_name` is treated as the `filespec`.
            limit (int | None, optional): Maximum number of matching rows to return.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the matching rows.

        Raises:
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        return self.find_rows_by_volume_filespec(bundle_name, filespec, limit=limit,
                                                 substring=substring)

    def find_rows_by_volume_filespec(self, volume_id, filespec=None, *, limit=None,
                                     substring=False):
        """Find the rows of the table with the specified volume ID and file specification
        name.

        The search is case-insensitive.

        If the table does not contain the `volume_id` or if the given value of `volume_id`
        is blank, the search is performed on the `filespec` alone. Also, if only one
        argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        If input parameter `substring` is True, then a match occurs whenever `filespec`
        appears inside what is tabulated in the file, so a complete match is not required.

        Parameters:
            volume_id (str): The volume ID to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `volume_id` is treated as the `filespec`.
            limit (int | None, optional): Maximum number of matching rows to return.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the matching rows.

        Raises:
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        indices = self.find_row_indices_by_volume_filespec(volume_id, filespec,
                                                           limit=limit,
                                                           substring=substring)
        dicts_by_row = self.dicts_by_row()
        return [dicts_by_row[k] for k in indices]

    def find_row_by_bundle_filespec(self, bundle_name, filespec=None, substring=False):
        """Find the first row of the table with the specified bundle name and file
        specification name.

        This is an alias for :meth:`~find_row_by_volume_filespec`.

        The search is case-insensitive.

        If the table does not contain the `bundle_name` or if the given value of
        `bundle_name` is blank, the search is performed on the `filespec` alone. Also, if
        only one argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            bundle_name (str): The bundle name to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `bundle_name` is treated as the `filespec`.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            dict[str, Any]: A dictionary representing the first matching row.

        Raises:
            ValueError: If no matching row is found, or if the table has no file
                specification column (see :meth:`filespec_column_index`).
        """

        return self.find_row_by_volume_filespec(bundle_name, filespec,
                                                substring=substring)

    def find_row_by_volume_filespec(self, volume_id, filespec=None, *, substring=False):
        """Find the first row of the table with the specified volume ID and file
        specification name.

        The search is case-insensitive.

        If the table does not contain the `volume_id` or if the given value of `volume_id`
        is blank, the search is performed on the `filespec` alone. Also, if only one
        argument is specified, it is treated as the `filespec`.

        The search ignores the extension of `filespec`, so it does not matter whether the
        column contains paths to labels or data files. It also works in tables that
        contain columns of file names without directory paths.

        Parameters:
            volume_id (str): The volume ID to search for.
            filespec (str | None, optional): The file specification name to search for. If
                None, `volume_id` is treated as the `filespec`.
            substring (bool, optional): If True, a match occurs whenever the given
                `filespec` appears inside what is tabulated in the file, so a complete
                match is not required.

        Returns:
            dict[str, Any]: A dictionary representing the first matching row.

        Raises:
            ValueError: If no matching row is found, or if the table has no file
                specification column (see :meth:`filespec_column_index`).
        """

        k = self.find_row_index_by_volume_filespec(volume_id, filespec=filespec,
                                                   substring=substring)
        dicts_by_row = self.dicts_by_row()
        return dicts_by_row[k]

    def index_rows_by_filename_key(self):
        """Create a dictionary of row indices keyed by the file basename associated with
        the row.

        The key has the file extension stripped away and is converted to lower case. The
        result is available in the `filename_keys` attribute.

        Raises:
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        if self._rows_by_filename is not None:
            return

        self._require_filespec_column()
        self._load()
        filespecs = self._column_values[self._filespec_colname]
        masks = self._column_masks[self._filespec_colname]

        rows_by_filename = {}
        filename_keys = []
        for row_num in range(len(filespecs)):
            if masks[row_num]:
                continue

            key = self.filename_key(filespecs[row_num])
            key_lc = key.lower()
            if key_lc not in rows_by_filename:
                rows_by_filename[key_lc] = []
                filename_keys.append(key)

            rows_by_filename[key_lc].append(row_num)

        self._rows_by_filename = rows_by_filename
        self._filename_keys = filename_keys

    @property
    def filename_keys(self) -> list[str]:
        """The filename keys of the table; ValueError if it has no filespec column."""

        if self._filename_keys is None:
            self.index_rows_by_filename_key()

        return self._filename_keys

    def row_indices_by_filename_key(self, key):
        """Quick lookup of the row indices associated with a filename key.

        Parameters:
            key (str): The filename key to look up.

        Returns:
            list[int]: A list of row indices associated with the filename key.

        Raises:
            KeyError: If no row has the filename key `key`.
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        # Create the index if necessary
        self.index_rows_by_filename_key()

        return self._rows_by_filename[key.lower()]

    def rows_by_filename_key(self, key):
        """Quick lookup of the rows associated with a filename key.

        Parameters:
            key (str): The filename key to look up.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the rows associated
            with the `key`.

        Raises:
            KeyError: If no row has the filename key `key`.
            ValueError: If the table has no file specification column (see
                :meth:`filespec_column_index`).
        """

        # Create the index if necessary
        self.index_rows_by_filename_key()

        indices = self._rows_by_filename[key.lower()]

        dicts_by_row = self.dicts_by_row()
        rows = [dicts_by_row[k] for k in indices]

        return rows

##########################################################################################
