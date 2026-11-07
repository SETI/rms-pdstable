##########################################################################################
# tests/test_pds3table_structure.py
##########################################################################################

from collections.abc import Callable
from pathlib import Path

from filecache import FCPath
import numpy as np
from pdsparser import Pds3Label
import pytest

from pdstable import PdsTable

# The same table as EDITED_PATH, with most of its COLUMN objects moved into .fmt files.
EDITED_PATH = 'test_files/cassini_iss_index_edited.lbl'

# Columns 5-20 are in a .fmt file beside the label, which pulls in columns 21-44 from a
# second, nested .fmt file.
STRUCTURE_PATH = 'test_files/cassini_iss_index_edited_structure.lbl'

# Columns 5-44 are in a .fmt file in FMT_DIR rather than beside the label.
FMT_DIR_PATH = 'test_files/cassini_iss_index_edited_structure_fmt_dir.lbl'
FMT_DIR = 'test_files/fmt'
FMT_DIR_FMT_NAME = 'cassini_iss_index_edited_structure_fmt_dir.fmt'



def _replace_unk(value: str) -> str:
    """Replace the "UNK" entries that would otherwise make the float column warn."""
    return value.replace('UNK', '-999')


# Every table in this file loads with these callbacks, so that the only warnings a test
# sees are the ones it is about.
CALLBACKS: dict[str, Callable[..., str | bytes]] = {'BIAS_STRIP_MEAN': _replace_unk}

TABLE_END = 'END_OBJECT               = IMAGE_INDEX_TABLE'

CONTAINER = """\
  OBJECT         = CONTAINER
    NAME         = REPEATED
    START_BYTE   = 1
    BYTES        = 4
    REPETITIONS  = 2
    OBJECT       = COLUMN
      NAME       = ITEM
      DATA_TYPE  = CHARACTER
      START_BYTE = 1
      BYTES      = 2
    END_OBJECT   = COLUMN
  END_OBJECT     = CONTAINER

"""


@pytest.fixture(scope='module')
def reference() -> PdsTable:
    """The table loaded from the label that lists every column inline."""
    return PdsTable(EDITED_PATH, callbacks=CALLBACKS)


def _edited_text() -> str:
    """The text of the inline label, with its original <CR><LF> line terminators."""
    return Path(EDITED_PATH).read_bytes().decode('latin-1')


def _assert_same_table(table: PdsTable, reference: PdsTable) -> None:
    """Assert that two tables have the same columns, values, and masks."""
    assert table.get_keys() == reference.get_keys()
    assert table.columns == 44
    for key in reference.get_keys():
        np.testing.assert_array_equal(table.get_column(key), reference.get_column(key))
        np.testing.assert_array_equal(table.get_column_mask(key),
                                      reference.get_column_mask(key))


def test_structure_beside_label_with_nested_structure(reference: PdsTable) -> None:
    table = PdsTable(STRUCTURE_PATH, callbacks=CALLBACKS)
    _assert_same_table(table, reference)


@pytest.mark.parametrize('fmt_dirs', [FMT_DIR, Path(FMT_DIR), FCPath(FMT_DIR),
                                      [FMT_DIR], [Path('test_files/nowhere'), FMT_DIR]],
                         ids=['str', 'Path', 'FCPath', 'list', 'list_second'])
def test_structure_in_fmt_dirs(reference: PdsTable, fmt_dirs: str | Path | FCPath | list[str | Path | FCPath]) -> None:
    table = PdsTable(FMT_DIR_PATH, fmt_dirs=fmt_dirs, callbacks=CALLBACKS)
    _assert_same_table(table, reference)


def test_structure_not_found_raises() -> None:
    with pytest.raises(FileNotFoundError, match=FMT_DIR_FMT_NAME):
        PdsTable(FMT_DIR_PATH, callbacks=CALLBACKS)


@pytest.mark.parametrize('form', ['crlf', 'lf', 'list'])
def test_structure_in_label_contents(reference: PdsTable, form: str) -> None:
    text = Path(STRUCTURE_PATH).read_bytes().decode('latin-1')
    contents: str | list[str]
    if form == 'crlf':
        contents = text
    elif form == 'lf':
        contents = text.replace('\r\n', '\n')
    else:
        contents = text.splitlines()
    table = PdsTable(STRUCTURE_PATH, label_contents=contents, callbacks=CALLBACKS)
    _assert_same_table(table, reference)


def test_structure_in_label_contents_uses_fmt_dirs(reference: PdsTable) -> None:
    text = Path(FMT_DIR_PATH).read_bytes().decode('latin-1')
    table = PdsTable(FMT_DIR_PATH, label_contents=text, fmt_dirs=FMT_DIR, callbacks=CALLBACKS)
    _assert_same_table(table, reference)


def test_expanded_pds3label_is_accepted(reference: PdsTable) -> None:
    label = Pds3Label(STRUCTURE_PATH, expand=True)
    table = PdsTable(STRUCTURE_PATH, label_contents=label, callbacks=CALLBACKS)
    _assert_same_table(table, reference)


@pytest.mark.parametrize('as_dict', [False, True], ids=['Pds3Label', 'dict'])
def test_unexpanded_label_raises(as_dict: bool) -> None:
    label = Pds3Label(STRUCTURE_PATH)
    contents = label.dict if as_dict else label
    with pytest.raises(ValueError, match=r'\^STRUCTURE.*expand=True'):
        PdsTable(STRUCTURE_PATH, label_contents=contents, callbacks=CALLBACKS)


def test_columns_count_mismatch_warns() -> None:
    text = _edited_text().replace('COLUMNS                = 44',
                                  'COLUMNS                = 45')
    with pytest.warns(UserWarning, match='COLUMNS = 45') as record:
        table = PdsTable(EDITED_PATH, label_contents=text, callbacks=CALLBACKS)
    assert [str(w.message) for w in record] == [
        'Table label says COLUMNS = 45 but describes 44 COLUMN objects']
    assert table.columns == 44


def test_container_warns() -> None:
    text = _edited_text().replace('\r\n', '\n').replace(TABLE_END, CONTAINER + TABLE_END)
    with pytest.warns(UserWarning, match='CONTAINER') as record:
        table = PdsTable(EDITED_PATH, label_contents=text, callbacks=CALLBACKS)
    assert [str(w.message) for w in record] == [
        'Table contains a CONTAINER object, which is not supported; its columns are '
        'not loaded']
    assert table.columns == 44
