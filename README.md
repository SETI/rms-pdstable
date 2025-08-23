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

`pdstable` is a set of classes for reading and searching star catalogs. Currently NAIF SPICE
star catalogs, the Yale Bright Star Catalog (YBSC), and UCAC4 are supported.

`pdstable` is a product of the [PDS Ring-Moon Systems Node](https://pds-rings.seti.org).

# Installation

The `pdstable` module is available via the `rms-pdstable` package on PyPI and can be installed with:

```sh
pip install rms-pdstable
```

# Getting Started

The `pdstable` module provides the `pdstablealog` class, which is the superclass for classes
that handle specific star catalogs. Each star catalog class takes an optional directory
path to point at the root of the star catalog data; if no directory path is provided,
the contents of an environment variable is used instead. Each path can be a full URL
as supported by [`rms-filecache`](https://rms-filecache.readthedocs.io/en/latest/),
allowing the catalog data to be downloaded (and cached locally) at runtime.

- `Spicepdstablealog`
  - The `dir` argument, if specified, must point to a directory containing NAIF SPICE
    kernels.
  - Otherwise, the environment variable `SPICE_PATH`, if defined, must contain a `Stars`
    subdirectory with NAIF SPICE kernels.
  - Otherwise, the environment variable `OOPS_RESOURCES` must contain a `SPICE/Stars`
    subdirectory.
- `YBSCpdstablealog`
  - The `dir` argument, if specified, must point to a directory containing the file
    `catalog`.
  - Otherwise, the environment variable `YBSC_PATH` must point to that directory.
- `UCAC4pdstablealog`
  - The `dir` argument, if specified, must point to a directory containing the directory
    `u4b`.
  - Otherwise, the environment variable `UCAC4_PATH` must point to that directory.

Each star catalog returns stars as a class that is a subclass of `Star`. Each subclass
contains the attributes provided by that star catalog, and none are guaranteed to be
filled in for all stars:

- `SpiceStar`
- `YBSCStar`
- `UCAC4Star`

Details of each class are available in the [module documentation](https://rms-pdstable.readthedocs.io/en/latest/module.html).

Basic operation is as follows:

```python
from pdstable import YBSCpdstablealog
import numpy as np
cat = YBSCpdstablealog()
ra_vega = 279.2333
dec_vega = 38.7836
vega_list = list(cat.find_stars(ra_min=np.radians(ra_vega-0.1),
                                ra_max=np.radians(ra_vega+0.1),
                                dec_min=np.radians(dec_vega-0.1),
                                dec_max=np.radians(dec_vega+0.1)))

assert len(vega_list) == 1
print(vega_list[0])
```

yields:

```
UNIQUE ID 7001 | RA 279.2345833° (18h36m56.300s) | DEC 38.7836111° (+038d47m1.000s)
VMAG  0.030  | PM RA 259.135 mas/yr  | PM DEC 286.000 mas/yr
TEMP 10800 | SCLASS A0Va
Name "3Alp Lyr" | Durch "BD+38 3238" | Draper 172167 | SAO 67174 | FK5 699
IR 1 Ref NASA | Multiple " " | Aitken 11510 None | Variable "Alp Lyr"
SCLASS Code   | Galactic LON 67.44 LAT 19.24
B-V 0.0 | U-B -0.01 | R-I -0.03
Parallax TRIG 0.1230000 arcsec | RadVel -14.0 km/s V  | RotVel (v sin i) 15.0 km/s
Double mag diff 10.40 Sep 62.80 arcsec Components AB # 5
```

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
