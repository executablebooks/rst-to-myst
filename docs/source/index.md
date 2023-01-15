# RST-to-MyST

A tool for converting [ReStructuredText](https://docutils.sourceforge.io/) to [MyST Markdown](https://myst-parser.readthedocs.io/).

## Getting Started

To install from PyPI:

```shell
pip install "rst-to-myst[sphinx]"
```

It is recommended to install into an isolated environment.
One way to do this is using [pipx](https://pypa.github.io/pipx/):

```console
$ pipx install "rst-to-myst[sphinx]"
$ pipx list
venvs are in /Users/username/.local/pipx/venvs
apps are exposed on your $PATH at /Users/username/.local/bin
   package rst-to-myst 0.1.2, Python 3.7.3
    - rst2myst
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
    sphinx_panels.dropdown.DropdownDirective: parse_all
```

```{toctree}
:hidden:

usage
cli
api
```
