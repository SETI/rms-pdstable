##########################################################################################
# tests/test_pdstable_rows_from_label.py
##########################################################################################

from pathlib import Path
import shutil

from filecache import FCPath
import pytest

from pdstable import PdsTable

PDS3_PATH = 'test_files/cassini_iss_index.lbl'
PDS3_EDITED_PATH = 'test_files/cassini_iss_index_edited.lbl'
PDS3_STRUCTURE_PATH = 'test_files/cassini_iss_index_edited_structure.lbl'
PDS4_PATH = 'test_files/uranus_occultations_index.xml'
PDS4_MULTI_PATH = 'test_files/uranus_occultation_ring_fit_rfrench_20201201.xml'


@pytest.mark.parametrize(('label_file', 'expected'),
                         [(PDS3_PATH, 4575),
                          (PDS3_EDITED_PATH, 100),
                          (Path(PDS3_EDITED_PATH), 100),
                          (FCPath(PDS3_EDITED_PATH), 100),
                          (PDS3_STRUCTURE_PATH, 100),
                          (PDS4_PATH, 2244)],
                         ids=['pds3', 'pds3_edited', 'Path', 'FCPath', 'structure',
                              'pds4'])
def test_rows_from_label(label_file: str | Path | FCPath, expected: int) -> None:
    assert PdsTable.rows_from_label(label_file) == expected


@pytest.mark.parametrize(('table_file', 'expected'),
                         [('.*input_events', 29), ('.*input_stars', 28), (1, 12)],
                         ids=['events', 'stars', 'index'])
def test_rows_from_label_pds4_table_file(table_file: str | int, expected: int) -> None:
    assert PdsTable.rows_from_label(PDS4_MULTI_PATH, table_file=table_file) == expected


def test_rows_from_label_pds4_multiple_tables_requires_table_file() -> None:
    with pytest.raises(ValueError, match='table_file parameter was not specified'):
        PdsTable.rows_from_label(PDS4_MULTI_PATH)


def test_rows_from_label_pds3_table_file_raises() -> None:
    with pytest.raises(ValueError, match='table_file is not supported for PDS3'):
        PdsTable.rows_from_label(PDS3_EDITED_PATH, table_file=1)


def test_rows_from_label_label_contents() -> None:
    text = Path(PDS3_EDITED_PATH).read_text(encoding='latin-1')
    text = text.replace('ROWS                   = 100', 'ROWS                   = 7')
    assert PdsTable.rows_from_label(PDS3_EDITED_PATH, label_contents=text) == 7


@pytest.mark.parametrize('label_file', [PDS3_EDITED_PATH, PDS4_PATH],
                         ids=['pds3', 'pds4'])
def test_rows_from_label_does_not_need_table_file(tmp_path: Path,
                                                  label_file: str) -> None:
    # Only the label is copied, so the table file it points to does not exist
    label_copy = tmp_path / Path(label_file).name
    shutil.copy(label_file, label_copy)
    expected = 100 if label_file == PDS3_EDITED_PATH else 2244
    assert PdsTable.rows_from_label(label_copy) == expected
    with pytest.raises(FileNotFoundError):
        PdsTable(label_copy)
