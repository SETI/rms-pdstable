[![GitHub release; latest by date](https://img.shields.io/github/v/release/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/releases)
[![Test Status](https://img.shields.io/github/actions/workflow/status/SETI/rms-pdstable/run-tests.yml?branch=main)](https://github.com/SETI/rms-pdstable/actions)
[![Documentation Status](https://readthedocs.org/projects/rms-pdstable/badge/?version=latest)](https://rms-pdstable.readthedocs.io/en/latest/?badge=latest)
[![Code coverage](https://img.shields.io/codecov/c/github/SETI/rms-pdstable/main?logo=codecov)](https://codecov.io/gh/SETI/rms-pdstable)
<br />
[![PyPI - Version](https://img.shields.io/pypi/v/rms-pdstable)](https://pypi.org/project/rms-pdstable)
[![PyPI - Format](https://img.shields.io/pypi/format/rms-pdstable)](https://pypi.org/project/rms-pdstable)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rms-pdstable)](https://pypi.org/project/rms-pdstable)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rms-pdstable)](https://pypi.org/project/rms-pdstable)
<br />
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/SETI/rms-pdstable/latest)](https://github.com/SETI/rms-pdstable/commits/main/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/commits/main/)
[![GitHub last commit](https://img.shields.io/github/last-commit/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/commits/main/)
<br />
[![Number of GitHub open issues](https://img.shields.io/github/issues-raw/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/issues)
[![Number of GitHub closed issues](https://img.shields.io/github/issues-closed-raw/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/issues)
[![Number of GitHub open pull requests](https://img.shields.io/github/issues-pr-raw/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/pulls)
[![Number of GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/pulls)
<br />
![GitHub License](https://img.shields.io/github/license/SETI/rms-pdstable)
[![Number of GitHub stars](https://img.shields.io/github/stars/SETI/rms-pdstable)](https://github.com/SETI/rms-pdstable/stargazers)
![GitHub forks](https://img.shields.io/github/forks/SETI/rms-pdstable)

# Introduction

`pdstable` contains a class, `PdsTable`, that can read PDS3 or PDS4 labels and their associated
tables.

`pdstable` is a product of the [PDS Ring-Moon Systems Node](https://pds-rings.seti.org).

# Installation

The `pdstable` module is available via the `rms-pdstable` package on PyPI and can be installed with:

```sh
pip install rms-pdstable
```

# Getting Started

The `pdstable` module provides the `PdsTable` class, which can be used to read both
PDS3 (`.lbl`) and PDS4 (`.lblx` or `.xml`) labels and their associated tables. A `PdsTable`
object can be created easily:

```python
from pdstable import PdsTable
p3 = PdsTable('label_filename.lbl')  # PDS3 label and table
p4 = PdsTable('label_filename.xml')  # PDS4 label and table
```

Once created, the `PdsTable` object has properties that can be used to access the
contents of the table. Columns of values are represented by NumPy arrays.

```python
rows = p3.rows  # The number of rows
columns = p3.columns # The number of columns
col_vals = p3.get_column("FILE_SPEC")  # All values in the FILE_SPEC column
col_mask = p3.get_column_mask("FILE_SPEC")  # The mask of invalid values
```

The entire table can be returned as a series of dictionaries, one per row. The
dictionary keys are the names of the columns:

```python
as_dicts = p3.dicts_by_row()
```

PDS3 labels can only point to a single table. However, PDS4 labels can point to
multiple tables. If multiple tables are present in the label, you must specify
which table you want to read. This can be done using an integer index or specifying
a filename or regular expression:

```python
p4 = PdsTable('multi_table_label.xml', table_file=3)  # Load the 3rd table
p4 = PdsTable('multi_table_label.xml', table_file='.*summary_index.*')
```

A wide variety of other features are available, many of which are designed to
increase performance. These include:

- Specifying a subset of columns to parse.
- Reading only a subset of rows.
- Using a faster but less rigorous label parser for PDS3 labels.
- Searching for rows with a specific volume or bundle name and/or file specification.

Full details can be found in the [module documentation](https://rms-pdstable.readthedocs.io/en/latest/module.html).

# Contributing

Information on contributing to this package can be found in the
[Contributing Guide](https://github.com/SETI/rms-pdstable/blob/main/CONTRIBUTING.md).

# Links

- [Documentation](https://rms-pdstable.readthedocs.io)
- [Repository](https://github.com/SETI/rms-pdstable)
- [Issue tracker](https://github.com/SETI/rms-pdstable/issues)
- [PyPi](https://pypi.org/project/rms-pdstable)

# Licensing

This code is licensed under the [Apache License v2.0](https://github.com/SETI/rms-pdstable/blob/main/LICENSE).
