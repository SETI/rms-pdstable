##########################################################################################
# tests/test_pdstable_iter_dicts.py
##########################################################################################

import builtins
from collections.abc import Callable
from io import BufferedReader
from pathlib import Path
import shutil
from typing import Any
import warnings

import numpy as np
import pytest

from pdstable import PdsTable

PDS3_PATH = 'test_files/cassini_iss_index.lbl'
PDS3_EDITED_PATH = 'test_files/cassini_iss_index_edited.lbl'
PDS4_INDEX_PATH = 'test_files/uranus_occultations_index.xml'
PDS4_MULTI_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'

# The float column whose "UNK" entries trigger the illegally-formatted-value warning
UNK_COLUMN = 'BIAS_STRIP_MEAN'


def _replace_unk(value: str) -> str:
    """Replace the "UNK" entries that would otherwise make the float column warn."""
    return value.replace('UNK', '-999')


CALLBACKS: dict[str, Callable[..., str | bytes]] = {UNK_COLUMN: _replace_unk}

# Each case is a label and the PdsTable options to load it with
TABLE_CASES: list[tuple[str, dict[str, Any]]] = [
    (PDS3_EDITED_PATH, {'callbacks': CALLBACKS}),
    (PDS3_EDITED_PATH, {'callbacks': CALLBACKS, 'merge_masks': True,
                        'invalid': {'default': [-1.e32, -2147483648]},
                        'replacements': {'INSTRUMENT_DATA_RATE': {182.783997: 1.}},
                        'valid_ranges': {'FILTER_TEMPERATURE': [0., 1.e99]}}),
    (PDS3_EDITED_PATH, {'callbacks': CALLBACKS,
                        'columns': ['FILE_NAME', 'EXPOSURE_DURATION', UNK_COLUMN]}),
    (PDS3_PATH, {'row_range': (10, 60), 'times': ['START_TIME']}),
    (PDS4_MULTI_PATH, {'table_file': 1}),
    (PDS4_MULTI_PATH, {'table_file': '.*input_stars'}),
    (PDS4_INDEX_PATH, {'row_range': (100, 150)}),
]
TABLE_IDS = ['pds3', 'pds3_options', 'pds3_columns', 'pds3_row_range_times',
             'pds4_fixed', 'pds4_csv', 'pds4_row_range']


def _assert_same_dicts(actual: list[dict[str, Any]],
                       expected: list[dict[str, Any]]) -> None:
    """Assert that two lists of row dicts have the same keys and values in order."""
    assert len(actual) == len(expected)
    for actual_row, expected_row in zip(actual, expected, strict=True):
        assert list(actual_row) == list(expected_row)
        for key, value in expected_row.items():
            np.testing.assert_equal(actual_row[key], value)


def _copy_label(tmp_path: Path, label_file: str, *,
                table_lines: Callable[[list[bytes]], list[bytes]] | None = None) -> Path:
    """Copy a PDS3 label into tmp_path; also copy its table, edited by table_lines."""
    label_copy = tmp_path / Path(label_file).name
    shutil.copy(label_file, label_copy)
    if table_lines is not None:
        table_file = Path(label_file).with_suffix('.tab')
        lines = table_file.read_bytes().splitlines(keepends=True)
        (tmp_path / table_file.name).write_bytes(b''.join(table_lines(lines)))
    return label_copy


@pytest.mark.parametrize(('label_file', 'options'), TABLE_CASES, ids=TABLE_IDS)
@pytest.mark.parametrize('chunk_rows', [1, 7, 50, 1000])
@pytest.mark.parametrize('lowercase', [(False, False), (True, True)],
                         ids=['plain', 'lowercase'])
def test_iter_dicts_matches_dicts_by_row(label_file: str, options: dict[str, Any],
                                         chunk_rows: int,
                                         lowercase: tuple[bool, bool]) -> None:
    expected = PdsTable(label_file, **options).dicts_by_row(lowercase=lowercase)
    table = PdsTable(label_file, defer_load=True, **options)
    actual = list(table.iter_dicts(chunk_rows, lowercase=lowercase))
    _assert_same_dicts(actual, expected)


def test_iter_dicts_default_chunk_and_lowercase_bool() -> None:
    expected = PdsTable(PDS4_INDEX_PATH).dicts_by_row(lowercase=True)
    table = PdsTable(PDS4_INDEX_PATH, defer_load=True)
    _assert_same_dicts(list(table.iter_dicts(lowercase=True)), expected)


def test_iter_is_iter_dicts() -> None:
    expected = PdsTable(PDS4_MULTI_PATH, table_file=1).dicts_by_row()
    table = PdsTable(PDS4_MULTI_PATH, table_file=1, defer_load=True)
    _assert_same_dicts(list(table), expected)


@pytest.mark.parametrize('chunk_rows', [0, -1])
def test_iter_dicts_bad_chunk_rows_raises_on_call(chunk_rows: int) -> None:
    table = PdsTable(PDS4_INDEX_PATH, defer_load=True)
    with pytest.raises(ValueError, match=f'chunk_rows must be at least 1: {chunk_rows}'):
        table.iter_dicts(chunk_rows)


def test_defer_load_does_not_read_table(tmp_path: Path) -> None:
    # Only the label is copied, so the table file it points to does not exist
    label_copy = _copy_label(tmp_path, PDS3_EDITED_PATH)
    table = PdsTable(label_copy, defer_load=True)
    assert table.rows == 100
    assert table.columns == 44
    assert table.column_info_dict['FILE_NAME'].bytes == 22
    with pytest.raises(FileNotFoundError):
        table.get_column('FILE_NAME')
    with pytest.raises(FileNotFoundError):
        next(table.iter_dicts())


@pytest.mark.parametrize('accessor', ['column_values', 'column_masks', 'get_column',
                                      'get_column_mask', 'dicts_by_row',
                                      'filename_keys'])
def test_defer_load_loads_on_first_use(accessor: str) -> None:
    loaded = PdsTable(PDS3_EDITED_PATH, callbacks=CALLBACKS)
    deferred = PdsTable(PDS3_EDITED_PATH, callbacks=CALLBACKS, defer_load=True)
    if accessor in ('get_column', 'get_column_mask'):
        np.testing.assert_equal(getattr(deferred, accessor)('FILE_NAME'),
                                getattr(loaded, accessor)('FILE_NAME'))
    elif accessor == 'dicts_by_row':
        _assert_same_dicts(deferred.dicts_by_row(), loaded.dicts_by_row())
    else:
        np.testing.assert_equal(getattr(deferred, accessor), getattr(loaded, accessor))


def test_iter_dicts_on_loaded_table_does_not_reread(tmp_path: Path) -> None:
    label_copy = _copy_label(tmp_path, PDS3_EDITED_PATH, table_lines=lambda x: x)
    table = PdsTable(label_copy, callbacks=CALLBACKS)
    expected = table.dicts_by_row()
    (tmp_path / 'cassini_iss_index_edited.tab').unlink()
    _assert_same_dicts(list(table.iter_dicts(7)), expected)


def _collect_until_error(table: PdsTable, chunk_rows: int,
                         ) -> tuple[list[dict[str, Any]], pytest.ExceptionInfo[ValueError]]:
    """Iterate a table until it raises ValueError; return the rows yielded first."""
    rows: list[dict[str, Any]] = []
    iterator = table.iter_dicts(chunk_rows)
    with pytest.raises(ValueError, match='row count mismatch') as excinfo:
        rows.extend(iterator)
    return rows, excinfo


def test_iter_dicts_short_table_raises_after_last_row(tmp_path: Path) -> None:
    label_copy = _copy_label(tmp_path, PDS3_EDITED_PATH, table_lines=lambda x: x[:45])
    table = PdsTable(label_copy, callbacks=CALLBACKS, defer_load=True)
    rows, excinfo = _collect_until_error(table, 20)
    assert len(rows) == 45
    assert str(excinfo.value) == (f'row count mismatch in {label_copy}: 45 rows in file; '
                                  'label says 100 rows')


def test_iter_dicts_long_table_raises_after_all_rows(tmp_path: Path) -> None:
    label_copy = _copy_label(tmp_path, PDS3_EDITED_PATH,
                             table_lines=lambda x: x + x[:3])
    table = PdsTable(label_copy, callbacks=CALLBACKS, defer_load=True)
    rows, excinfo = _collect_until_error(table, 30)
    assert len(rows) == 100
    assert str(excinfo.value) == (f'row count mismatch in {label_copy}: 103 rows in '
                                  'file; label says 100 rows')


def test_iter_dicts_short_row_range_raises(tmp_path: Path) -> None:
    label_copy = _copy_label(tmp_path, PDS3_EDITED_PATH, table_lines=lambda x: x[:45])
    table = PdsTable(label_copy, callbacks=CALLBACKS, row_range=(30, 60),
                     defer_load=True)
    rows, excinfo = _collect_until_error(table, 10)
    assert len(rows) == 15
    assert str(excinfo.value) == 'row count mismatch: 15 row(s) read; 30 row(s) requested'


def test_iter_dicts_closes_file_when_closed_early(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[BufferedReader] = []
    real_open = builtins.open

    def recording_open(*args: Any, **kwargs: Any) -> Any:
        f = real_open(*args, **kwargs)
        opened.append(f)
        return f

    table = PdsTable(PDS4_INDEX_PATH, defer_load=True)
    monkeypatch.setattr(builtins, 'open', recording_open)
    rows = table.iter_dicts(10)
    next(rows)
    assert len(opened) == 1
    assert not opened[0].closed
    rows.close()
    assert opened[0].closed


def _unk_chunk(chunk_rows: int) -> tuple[int, int]:
    """The first row of the first chunk with an "UNK" value, and that chunk's count."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        mask = PdsTable(PDS3_EDITED_PATH).get_column_mask(UNK_COLUMN)
    start = (int(np.argmax(mask)) // chunk_rows) * chunk_rows
    return start, int(np.sum(mask[start:start + chunk_rows]))


def test_iter_dicts_warns_once_per_column() -> None:
    start, count = _unk_chunk(10)
    table = PdsTable(PDS3_EDITED_PATH, defer_load=True)
    with pytest.warns(UserWarning, match=UNK_COLUMN) as record:
        list(table.iter_dicts(10))
    if count == 1:
        expected = (f'Illegally formatted float value in column {UNK_COLUMN} in rows '
                    f'{start}-{start + 9}: UNK')
    else:
        expected = (f'{count} illegally formatted float values in column {UNK_COLUMN} '
                    f'in rows {start}-{start + 9}; first example is "UNK"')
    assert [str(w.message) for w in record] == [expected]


def test_iter_dicts_does_not_repeat_warning_on_second_pass() -> None:
    table = PdsTable(PDS3_EDITED_PATH, defer_load=True)
    with pytest.warns(UserWarning, match=UNK_COLUMN):
        list(table.iter_dicts(10))
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        rows = list(iter(table))
    assert len(rows) == 100


def test_full_load_after_iteration_still_warns() -> None:
    table = PdsTable(PDS3_EDITED_PATH, defer_load=True)
    with pytest.warns(UserWarning, match=UNK_COLUMN):
        list(table.iter_dicts(10))
    with pytest.warns(UserWarning, match=UNK_COLUMN) as record:
        table.get_column(UNK_COLUMN)
    assert [str(w.message) for w in record] == [
        f'25 illegally formatted float values in column {UNK_COLUMN}; first example is '
        '"UNK"']
