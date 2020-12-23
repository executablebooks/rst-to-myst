# rst-to-myst [UNDER-DEVELOPMENT]

[![Build Status][ci-badge]][ci-link]
[![codecov.io][cov-badge]][cov-link]
[![PyPI version][pypi-badge]][pypi-link]

Convert [ReStructuredText](https://docutils.sourceforge.io/) to [MyST Markdown](https://myst-parser.readthedocs.io/).

## Install

```bash
pip install rst-to-myst
```

## Usage

CLI:

```bash
echo "some rst" | rst2myst
rst2myst -f path/to/file.rst
```

Warnings are written to `stderr` and converted text to `stdout`.

For all options see:

```bash
rst2myst --help
```

API:

```python
from rst_to_myst import convert

text, stderr_stream = convert("""
Some RST
========

To **convert**
""")
```

## Conversion Notes

The conversion is designed to be fault tolerant,
i.e. it will not check if referenced targets, roles, directives, etc exist nor fail if they do not.

The only syntax where some checks are required is matching anonymous references and auto-number/symbol footnotes with their definitions; these definitions must be available.

- enumerated lists with roman numerals or alphabetic prefixes will be converted to numbers
- only one kind of footnote (i.e. no symbol prefixes)
- citation are turned into footnotes, with label prepended by `cite_prefix`
- inline targets are not convertible (and so ignored)

## TODO

(see <https://docutils.sourceforge.io/docs/user/rst/quickref.htm>)

- nested conversion of directives (currently all wrapped in `eval-rst`)
- quote_block
- substitution definitions
- tables
- definition lists
- line block
- literal block
- field list

## Development

This package utilises [flit](https://flit.readthedocs.io) as the build engine, and [tox](https://tox.readthedocs.io) for test automation.

To install these development dependencies:

```bash
pip install flit tox
```

To run the tests:

```bash
tox
```

To run the code formatting and style checks:

```bash
pip install pre-commit
pre-commit run --all
```

## Publish to PyPi

Either use flit directly:

```bash
flit publish
```

or trigger the GitHub Action job, by creating a release with a tag equal to the version, e.g. `v0.0.1`.

Note, this requires generating an API key on PyPi and adding it to the repository `Settings/Secrets`, under the name `PYPI_KEY`.

[ci-badge]: https://github.com/executablebooks/rst-to-myst/workflows/CI/badge.svg?branch=main
[ci-link]: https://github.com/executablebooks/rst-to-myst/actions?query=workflow%3ACI+branch%3Amain+event%3Apush
[cov-badge]: https://codecov.io/gh/executablebooks/rst-to-myst/branch/main/graph/badge.svg
[cov-link]: https://codecov.io/gh/executablebooks/rst-to-myst
[pypi-badge]: https://img.shields.io/pypi/v/rst-to-myst.svg
[pypi-link]: https://pypi.org/project/rst-to-myst
