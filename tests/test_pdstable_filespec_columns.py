##########################################################################################
# tests/test_pdstable_filespec_columns.py
##########################################################################################

from collections.abc import Callable
from typing import Any

import pytest

from pdstable import PdsTable

PDS3_EDITED_PATH = 'test_files/cassini_iss_index_edited.lbl'
PDS4_MULTI_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'

# Row 3 of the edited Cassini index
ROW = 3
VOLUME_ID = 'COISS_2039'
FILESPEC = 'data/1573186009_1573197826/W1573186041_1.IMG'
FILE_NAME = 'W1573186041_1.IMG'

NO_FILESPEC = (r'^Table "uranus_occultation_ring_fit_rfrench_20201201\.tab" has no file '
               r'specification column; the names searched for are: file_specification, ')

# Every public member that needs a file specification column, called on a table
FILESPEC_CALLS: dict[str, Callable[[PdsTable], Any]] = {
    'filename_keys': lambda t: t.filename_keys,
    'index_rows_by_filename_key': lambda t: t.index_rows_by_filename_key(),
    'row_indices_by_filename_key': lambda t: t.row_indices_by_filename_key('x'),
    'rows_by_filename_key': lambda t: t.rows_by_filename_key('x'),
    'find_row_indices_by_volume_filespec':
        lambda t: t.find_row_indices_by_volume_filespec('x.tab'),
    'find_row_indices_by_bundle_filespec':
        lambda t: t.find_row_indices_by_bundle_filespec('b', 'x.tab'),
    'find_row_index_by_volume_filespec':
        lambda t: t.find_row_index_by_volume_filespec('x.tab'),
    'find_row_index_by_bundle_filespec':
        lambda t: t.find_row_index_by_bundle_filespec('b', 'x.tab'),
    'find_rows_by_volume_filespec': lambda t: t.find_rows_by_volume_filespec('x.tab'),
    'find_rows_by_bundle_filespec':
        lambda t: t.find_rows_by_bundle_filespec('b', 'x.tab'),
    'find_row_by_volume_filespec': lambda t: t.find_row_by_volume_filespec('x.tab'),
    'find_row_by_bundle_filespec': lambda t: t.find_row_by_bundle_filespec('b', 'x.tab'),
}


@pytest.fixture(scope='module')
def no_filespec_table() -> PdsTable:
    """A PDS4 table with neither a file specification nor a bundle column."""
    return PdsTable(PDS4_MULTI_PATH, table_file=1)


@pytest.fixture(scope='module')
def no_volume_table() -> PdsTable:
    """The edited Cassini index without its VOLUME_ID column."""
    with pytest.warns(UserWarning, match='illegally formatted'):
        table = PdsTable(PDS3_EDITED_PATH,
                         columns=['FILE_NAME', 'FILE_SPECIFICATION_NAME',
                                  'BIAS_STRIP_MEAN'])
    return table


@pytest.fixture(scope='module')
def full_table() -> PdsTable:
    """The edited Cassini index with every column."""
    with pytest.warns(UserWarning, match='illegally formatted'):
        table = PdsTable(PDS3_EDITED_PATH)
    return table


@pytest.mark.parametrize('call', FILESPEC_CALLS.values(), ids=FILESPEC_CALLS.keys())
def test_no_filespec_column_raises(no_filespec_table: PdsTable,
                                   call: Callable[[PdsTable], Any]) -> None:
    assert no_filespec_table.filespec_column_index() == -1
    with pytest.raises(ValueError, match=NO_FILESPEC):
        call(no_filespec_table)


def test_no_volume_column_searches_filespec_alone(no_volume_table: PdsTable) -> None:
    assert no_volume_table.volume_column_index() == -1
    assert no_volume_table.find_row_indices_by_volume_filespec(VOLUME_ID, FILESPEC) == [ROW]
    assert no_volume_table.find_row_indices_by_bundle_filespec(VOLUME_ID, FILESPEC) == [ROW]
    assert no_volume_table.find_row_index_by_volume_filespec(VOLUME_ID, FILESPEC) == ROW
    assert no_volume_table.find_row_by_volume_filespec(VOLUME_ID,
                                                       FILESPEC)['FILE_NAME'] == FILE_NAME
    rows = no_volume_table.find_rows_by_volume_filespec('WRONG_VOLUME', FILESPEC)
    assert [row['FILE_NAME'] for row in rows] == [FILE_NAME]


def test_volume_column_still_filters(full_table: PdsTable) -> None:
    assert full_table.find_row_indices_by_volume_filespec(VOLUME_ID, FILESPEC) == [ROW]
    assert full_table.find_row_indices_by_volume_filespec('WRONG_VOLUME', FILESPEC) == []
    assert full_table.find_row_indices_by_volume_filespec(FILESPEC) == [ROW]
