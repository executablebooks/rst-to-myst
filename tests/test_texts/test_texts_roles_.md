---
Author: David Goodger
Contact: <mailto:docutils-develop@lists.sourceforge.net>
Copyright: This document has been placed in the public domain.
Date: \$Date\$
Revision: \$Revision\$
---

# reStructuredText Interpreted Text Roles

This document describes the interpreted text roles implemented in the
reference reStructuredText parser.

Interpreted text uses backquotes (\`) around the text. An explicit
role marker may optionally appear before or after the text, delimited
with colons. For example:

```
This is `interpreted text` using the default role.

This is :title:`interpreted text` using an explicit role.
```

A default role may be defined by applications of reStructuredText; it
is used if no explicit `:role:` prefix or suffix is given. The
"default default role" is [:title-reference:]. It can be changed
using the [default-role] directive.

See the [Interpreted Text] section in the [reStructuredText Markup
Specification][restructuredtext markup specification] for syntax details. For details on the hierarchy of
elements, please see [The Docutils Document Tree] and the [Docutils
Generic DTD][docutils generic dtd] XML document type definition. For interpreted text role
implementation details, see [Creating reStructuredText Interpreted
Text Roles][creating restructuredtext interpreted text roles].

```{contents}
```

## Customization

Custom interpreted text roles may be defined in a document with the
["role" directive]. Customization details are listed with each role.

(class)=

A `class` option is recognized by the "role" directive for most
interpreted text roles. A [description](directives.html#role-class) is provided in the ["role"
directive]["role" directive] documentation.

## Standard Roles

### `:emphasis:`

```{eval-rst}

:Aliases: None
:DTD Element: emphasis
:Customization:
    :Options: class_.
    :Content: None.
```

Implements emphasis. These are equivalent:

```
*text*
:emphasis:`text`
```

### `:literal:`

```{eval-rst}

:Aliases: None
:DTD Element: literal
:Customization:
    :Options: class_.
    :Content: None.
```

Implements inline literal text. These are equivalent:

```
``text``
:literal:`text`
```

Care must be taken with backslash-escapes though. These are *not*
equivalent:

```
``text \ and \ backslashes``
:literal:`text \ and \ backslashes`
```

The backslashes in the first line are preserved (and do nothing),
whereas the backslashes in the second line escape the following
spaces.

### `:code:`

```{eval-rst}

:Aliases: None
:DTD Element: literal
:Customization:
    :Options: class_, language
    :Content: None.
```

(New in Docutils 0.9.)

The `code` role marks its content as code in a formal language.

For syntax highlight of inline code, the ["role" directive] can be used to
build custom roles with the code language specified in the "language"
option.

For example, the following creates a LaTeX-specific "latex" role:

```
.. role:: latex(code)
   :language: latex
```

Content of the new role is parsed and tagged by the [Pygments] syntax
highlighter. See the [code directive] for more info on parsing and display
of code in reStructuredText.

In addition to "[class]", the following option is recognized:

`language`

: Name of the code's language.
  See [supported languages and markup formats] for recognized values.

### `:math:`

```{eval-rst}

:Aliases: None
:DTD Element: math
:Customization:
    :Options: class_
    :Content: None.
```

(New in Docutils 0.8.)

The `math` role marks its content as mathematical notation (inline
formula).

The input format is LaTeX math syntax without the “math delimiters“
(`$ $`), for example:

```
The area of a circle is :math:`A_\text{c} = (\pi/4) d^2`.
```

See the [math directive] (producing display formulas) for more info
on mathematical notation in reStructuredText.

### `:pep-reference:`

```{eval-rst}

:Aliases: ``:PEP:``
:DTD Element: reference
:Customization:
    :Options: class_.
    :Content: None.
```

The `:pep-reference:` role is used to create an HTTP reference to a
PEP (Python Enhancement Proposal). The `:PEP:` alias is usually
used. For example:

```
See :PEP:`287` for more information about reStructuredText.
```

This is equivalent to:

```
See `PEP 287`__ for more information about reStructuredText.

__ http://www.python.org/peps/pep-0287.html
```

### `:rfc-reference:`

```{eval-rst}

:Aliases: ``:RFC:``
:DTD Element: reference
:Customization:
    :Options: class_.
    :Content: None.
```

The `:rfc-reference:` role is used to create an HTTP reference to an
RFC (Internet Request for Comments). The `:RFC:` alias is usually
used. For example:

```
See :RFC:`2822` for information about email headers.
```

This is equivalent to:

```
See `RFC 2822`__ for information about email headers.

__ http://www.faqs.org/rfcs/rfc2822.html
```

### `:strong:`

```{eval-rst}

:Aliases: None
:DTD Element: strong
:Customization:
    :Options: class_.
    :Content: None.
```

Implements strong emphasis. These are equivalent:

```
**text**
:strong:`text`
```

### `:subscript:`

```{eval-rst}

:Aliases: ``:sub:``
:DTD Element: subscript
:Customization:
    :Options: class_.
    :Content: None.
```

Implements subscripts.

:::{Tip}
Whitespace or punctuation is required around interpreted text, but
often not desired with subscripts & superscripts.
Backslash-escaped whitespace can be used; the whitespace will be
removed from the processed document:

```
H\ :sub:`2`\ O
E = mc\ :sup:`2`
```

In such cases, readability of the plain text can be greatly
improved with substitutions:

```
The chemical formula for pure water is |H2O|.

.. |H2O| replace:: H\ :sub:`2`\ O
```

See [the reStructuredText spec](restructuredtext.html) for further information on
[character-level markup](restructuredtext.html#character-level-inline-markup) and [the substitution mechanism](restructuredtext.html#substitution-references).
:::

### `:superscript:`

```{eval-rst}

:Aliases: ``:sup:``
:DTD Element: superscript
:Customization:
    :Options: class_.
    :Content: None.
```

Implements superscripts. See the tip in [:subscript:] above.

### `:title-reference:`

```{eval-rst}

:Aliases: ``:title:``, ``:t:``.
:DTD Element: title_reference
:Customization:
    :Options: class_.
    :Content: None.
```

The `:title-reference:` role is used to describe the titles of
books, periodicals, and other materials. It is the equivalent of the
HTML "cite" element, and it is expected that HTML writers will
typically render "title_reference" elements using "cite".

Since title references are typically rendered with italics, they are
often marked up using `*emphasis*`, which is misleading and vague.
The "title_reference" element provides accurate and unambiguous
descriptive markup.

Let's assume `:title-reference:` is the default interpreted text
role (see below) for this example:

```
`Design Patterns` [GoF95]_ is an excellent read.
```

The following document fragment ([pseudo-XML]) will result from
processing:

```
<paragraph>
    <title_reference>
        Design Patterns

    <citation_reference refname="gof95">
        GoF95
     is an excellent read.
```

`:title-reference:` is the default interpreted text role in the
standard reStructuredText parser. This means that no explicit role is
required. Applications of reStructuredText may designate a different
default role, in which case the explicit `:title-reference:` role
must be used to obtain a `title_reference` element.

## Specialized Roles

### `raw`

```{eval-rst}

:Aliases: None
:DTD Element: raw
:Customization:
    :Options: class_, format
    :Content: None
```

:::{WARNING}
The "raw" role is a stop-gap measure allowing the author to bypass
reStructuredText's markup. It is a "power-user" feature that
should not be overused or abused. The use of "raw" ties documents
to specific output formats and makes them less portable.

If you often need to use "raw"-derived interpreted text roles or
the "raw" directive, that is a sign either of overuse/abuse or that
functionality may be missing from reStructuredText. Please
describe your situation in a message to the [Docutils-users] mailing
list.
:::

The "raw" role indicates non-reStructuredText data that is to be
passed untouched to the Writer. It is the inline equivalent of the
["raw" directive]; see its documentation for details on the
semantics.

The "raw" role cannot be used directly. The ["role" directive] must
first be used to build custom roles based on the "raw" role. One or
more formats (Writer names) must be provided in a "format" option.

For example, the following creates an HTML-specific "raw-html" role:

```
.. role:: raw-html(raw)
   :format: html
```

This role can now be used directly to pass data untouched to the HTML
Writer. For example:

```
If there just *has* to be a line break here,
:raw-html:`<br />`
it can be accomplished with a "raw"-derived role.
But the line block syntax should be considered first.
```

:::{Tip}
Roles based on "raw" should clearly indicate their origin, so
they are not mistaken for reStructuredText markup. Using a "raw-"
prefix for role names is recommended.
:::

In addition to "[class]", the following option is recognized:

`format`

: One or more space-separated output format names (Writer names).

["raw" directive]: directives.html#raw-directive
["role" directive]: directives.html#role
[code directive]: directives.html#code
[creating restructuredtext interpreted text roles]: ../../howto/rst-roles.html
[default-role]: directives.html#default-role
[docutils generic dtd]: ../docutils.dtd
[docutils-users]: ../../user/mailing-lists.html#docutils-user
[interpreted text]: restructuredtext.html#interpreted-text
[math directive]: directives.html#math
[pseudo-xml]: ../doctree.html#pseudo-xml
[pygments]: http://pygments.org/
[restructuredtext markup specification]: restructuredtext.html
[supported languages and markup formats]: http://pygments.org/languages/
[the docutils document tree]: ../doctree.html
