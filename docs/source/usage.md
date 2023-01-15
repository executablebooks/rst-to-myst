# Extended Guide

## How it works

1. The RST text is converted to a modified version of docutils AST, which preserves lossless information about the source text.
2. The docutils AST is converted to [Markdown-It](https://markdown-it-py.readthedocs.io) syntax tokens.
3. The tokens are converted to Markdown text with [mdformat](https://mdformat.readthedocs.io).

The conversion is designed to be fault tolerant, i.e. it will not check if referenced targets, roles, directives, etc exist nor fail if they do not.

The only syntax where some checks are required is matching anonymous references and auto-number/symbol footnotes with their definitions; these definitions must be available.

Conversion notes:

- enumerated lists with roman numerals or alphabetic prefixes will be converted to numbers
- only one kind of footnote (i.e. no symbol prefixes)
- citation are turned into footnotes, with label prepended by `cite_prefix`
- inline targets are not convertible (and so ignored)
- If tables are not compatible with Markdown (single header row, no merged cells, etc), then they will be wrapped in an `eval-rst` directive
- Markdown blockquotes do not have an attribution syntax, so it is converted instead to `<p class="attribution">—text</p>` (the standard HTML render)

## Converting text snippets

Either use the `stream` CLI command, parsing in `stdin`:

```console
$ echo ":role:`content`" | rst2myst stream -
{role}`content`
```

or use the API:

```python
from rst_to_myst import rst_to_myst
output = rst_to_myst(":role:`content`")
print(output.text)
```

## Converting multiple files

Use the `convert` CLI command, with standard file globbing.
The `--dry-run` option will run without actually writing any files:

```console
$ rst2myst convert --dry-run docs/**/*.rst
docs/source/api.rst -> docs/source/api.md
CONVERTED (extensions: [])
docs/source/cli.rst -> docs/source/cli.md
CONVERTED (extensions: ['deflist'])

FINISHED ALL! (extensions: ['deflist'])
```

Extensions specify which MyST optional extensions are required to reparse the Markdown text.

## Configuring the conversion

The [CLI](./cli.rst) and [API](./api.rst) documentation list all the available configurations.

For the CLI, you can directly use the option flags, or you can provide all the options in a YAML configuration file, with the `--config` option:

```console
$ rst2myst convert --config config.yaml docs/**/*.rst
```

YAML config options mirror the CLI options, except using `_` instead of `-`, e.g.

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

### Directive conversion

Directives are converted according to a mapping of the directive module path to a conversion type:

- "eval_rst" (the default): no conversion, wrap in MyST `eval-rst` directive

  ````
  ```{eval-rst}
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

- "parse_argument": convert to MyST directive and convert the argument to Markdown

  ````
  ```{name} argument [link](link)
  :option: value

  content `link`_
  ```
  ````

- "parse_content": convert to MyST directive and convert the content to Markdown

  ````
  ```{name} argument `link`_
  :option: value

  content [link](link)
  ```
  ````

- "parse_all": convert to MyST directive and convert the content to Markdown

  ````
  ```{name} argument [link](link)
  :option: value

  content [link](link)
  ```
  ````

The default conversions are listed below, or you can use the `conversions` options to update these conversions.
Also use the `colon_fence` option to control whether directives with Markdown content are delimited by `:::`.

````{dropdown} **Directive conversion defaults**

```{literalinclude} ../../rst_to_myst/data/directives.yml
:language: yaml
```

````

## Additional Functionality

### Listing available directives/roles

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
