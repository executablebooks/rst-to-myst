# rst-to-myst

[![Build Status][ci-badge]][ci-link]
[![codecov.io][cov-badge]][cov-link]
[![PyPI version][pypi-badge]][pypi-link]

Convert [ReStructuredText](https://docutils.sourceforge.io/) to [MyST Markdown](https://myst-parser.readthedocs.io/),
and also explore available roles/directives.

See [tests/fixtures/render.txt](tests/fixtures/render.txt) for examples of inputs -> outputs.

## Install

```bash
pip install rst-to-myst
```

or with sphinx:

```bash
pip install rst-to-myst[sphinx]
```

To then run a basic conversion of a whole project:

```console
$ rst2myst convert docs/**/*.rst
```

For greater control, you can pass configuration with CLI options, or via a YAML configuration file:

```console
$ rst2myst convert --config config.yaml docs/**/*.rst
```

`config.yaml`:

```yaml
language: en
sphinx: true
extensions:
- sphinx_panels
default_domain: py
consecutive_numbering: true
colon_fences: true
dollar_math: true
conversions:
    sphinx_panels.dropdpwn.DropdownDirective: parse_all
```

See the documentation for more information: <https://rst-to-myst.readthedocs.io/>

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

## TODO

The conversion covers almost all syntaxes (see <https://docutils.sourceforge.io/docs/user/rst/quickref.htm>) except:

- line blocks
- option lists

Also custom functions for directive parsing would be desirable.

[ci-badge]: https://github.com/executablebooks/rst-to-myst/workflows/CI/badge.svg?branch=main
[ci-link]: https://github.com/executablebooks/rst-to-myst/actions?query=workflow%3ACI+branch%3Amain+event%3Apush
[cov-badge]: https://codecov.io/gh/executablebooks/rst-to-myst/branch/main/graph/badge.svg
[cov-link]: https://codecov.io/gh/executablebooks/rst-to-myst
[pypi-badge]: https://img.shields.io/pypi/v/rst-to-myst.svg
[pypi-link]: https://pypi.org/project/rst-to-myst
