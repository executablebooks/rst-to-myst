# rst-to-myst [UNDER-DEVELOPMENT]

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

## Basic Usage

### Command-Line Interface (CLI)

For all commands see:

```bash
rst2myst --help
```

Parse *via* stdin:

```console
$ echo ":role:`content`" | rst2myst parse
{role}`content`
```

Parse *via* file:

```console
$ rst2myst parse -f path/to/file.rst
...
```

Warnings are written to `stderr` and converted text to `stdout`.

List available directives/roles:

```console
$ rst2myst directives list
acks admonition ...

$ rst2myst roles list
abbr abbreviation ...
```

Show details of a specific directive/role:

```console
$ rst2myst directives show admonition
class: docutils.parsers.rst.directives.admonitions.Admonition
description: ''
has_content: true
name: admonition
optional_arguments: 0
options:
  class: class_option
  name: unchanged
required_arguments: 1

$ rst2myst roles show abbreviation
description: |-
  Generic interpreted text role, where the interpreted text is simply
  wrapped with the provided node class.
module: docutils.parsers.rst.roles
name: abbreviation
```

### Python Interface (API)

```python
from rst_to_myst import convert

text, stderr_stream = convert("""
Some RST
========

To **convert**
""")
```

## Advanced Usage

You can select a language to translate directive/role names:

```console
$ rst2myst parse -l fr -f path/to/file.rst
...
```

You can select whether sphinx directives/roles are loaded:

```console
$ rst2myst parse --no-sphinx -f path/to/file.rst
...
```

You can load directives/roles from extensions:

```console
$ rst2myst parse -e sphinx.ext.autodoc -e sphinx_panels -f path/to/file.rst
...
```

Directives are converted according to [rst_to_myst/data/directives.yml](rst_to_myst/data/directives.yml), which can also be updated with an external YAML file, using the `-c/--conversions` option.
This is a mapping of directive import paths to a conversion type:

- "eval_rst" (the default): no conversion, wrap in MyST eval_rst directive
  ````
  ```{eval_rst}
  .. name:: argument `link`_
     :option: value

     content `link`_
  ```
  ````
- "direct": convert directly to MyST directive, keeping original argument/content
  ````
  ```{name} argument `link`_
  :option: value

  content `link`_
  ```
  ````
- "argument_only":  convert to MyST directive and convert the argument to Markdown
  ````
  ```{name} argument [link](link)
  :option: value

  content `link`_
  ```
  ````
- "content_only":  convert to MyST directive and convert the content to Markdown
  ````
  ```{name} argument `link`_
  :option: value

  content [link](link)
  ```
  ````
- "argument_content":  convert to MyST directive and convert the content to Markdown
  ````
  ```{name} argument [link](link)
  :option: value

  content [link](link)
  ```
  ````

If a conversion type is prepended by "_colon", use `:::` delimiters instad of ```` ``` ````,
e.g. "argument_content_colon"

````
:::{name} argument [link](link)
:option: value

content [link](link)
:::
````

## Conversion Notes

The conversion is designed to be fault tolerant,
i.e. it will not check if referenced targets, roles, directives, etc exist nor fail if they do not.

The only syntax where some checks are required is matching anonymous references and auto-number/symbol footnotes with their definitions; these definitions must be available.

- enumerated lists with roman numerals or alphabetic prefixes will be converted to numbers
- only one kind of footnote (i.e. no symbol prefixes)
- citation are turned into footnotes, with label prepended by `cite_prefix`
- inline targets are not convertible (and so ignored)
- If tables are not compatible with Markdown (single header row, no merged cells, etc), then they will be wrapped in an `eval_rst`
- Markdown blockquotes do not have an attribution syntax, so it is converted instead to `<p class="attribution">—text</p>` (the standard HTML render)

## TODO

The conversion covers almost all syntaxes (see <https://docutils.sourceforge.io/docs/user/rst/quickref.htm>) except:

- line blocks
- field lists (except at top of document, which are converted to front matter)
- option lists

Also custom functions for directive parsing would be desirable.

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
