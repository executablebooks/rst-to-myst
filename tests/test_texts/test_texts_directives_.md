---
Author: David Goodger
Contact: <mailto:docutils-develop@lists.sourceforge.net>
Copyright: This document has been placed in the public domain.
Date: \$Date\$
Revision: \$Revision\$
substitutions:
  '---': |-
    ```{eval-rst}
    .. unicode:: U+02014 .. em dash
       :trim:
    ```
  BogusMegaCorp (TM): |-
    ```{eval-rst}
    .. unicode:: BogusMegaCorp U+2122
       .. with trademark sign
    ```
  copy: |-
    ```{eval-rst}
    .. unicode:: 0xA9 .. copyright sign
    ```
---

# reStructuredText Directives

```{contents}
```

This document describes the directives implemented in the reference
reStructuredText parser.

Directives have the following syntax:

```
+-------+-------------------------------+
| ".. " | directive type "::" directive |
+-------+ block                         |
        |                               |
        +-------------------------------+
```

Directives begin with an explicit markup start (two periods and a
space), followed by the directive type and two colons (collectively,
the "directive marker").  The directive block begins immediately after
the directive marker, and includes all subsequent indented lines.  The
directive block is divided into arguments, options (a field list), and
content (in that order), any of which may appear.  See the [Directives]
section in the [reStructuredText Markup Specification] for syntax
details.

Descriptions below list "doctree elements" (document tree element
names; XML DTD generic identifiers) corresponding to individual
directives.  For details on the hierarchy of elements, please see [The
Docutils Document Tree][the docutils document tree] and the [Docutils Generic DTD] XML document
type definition.  For directive implementation details, see [Creating
reStructuredText Directives][creating restructuredtext directives].

## Admonitions

(attention)=

(caution)=

(danger)=

(error)=

(hint)=

(important)=

(note)=

(tip)=

(warning)=

### Specific Admonitions

```{eval-rst}

"important", "note", "tip", "warning", "admonition"
:Doctree Elements: attention, caution, danger, error, hint, important,
                   note, tip, warning, admonition_, title
:Directive Arguments: None.
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Interpreted as body elements.
```

Admonitions are specially marked "topics" that can appear anywhere an
ordinary body element can.  They contain arbitrary body elements.
Typically, an admonition is rendered as an offset block in a document,
sometimes outlined or shaded, with a title matching the admonition
type.  For example:

```
.. DANGER::
   Beware killer rabbits!
```

This directive might be rendered something like this:

```
+------------------------+
|        !DANGER!        |
|                        |
| Beware killer rabbits! |
+------------------------+
```

The following admonition directives have been implemented:

- attention
- caution
- danger
- error
- hint
- important
- note
- tip
- warning

Any text immediately following the directive indicator (on the same
line and/or indented on following lines) is interpreted as a directive
block and is parsed for normal body elements.  For example, the
following "note" admonition directive contains one paragraph and a
bullet list consisting of two list items:

```
.. note:: This is a note admonition.
   This is the second line of the first paragraph.

   - The note contains all indented body elements
     following.
   - It includes this bullet list.
```

### Generic Admonition

```{eval-rst}

:Directive Type: "admonition"
:Doctree Elements: admonition_, title
:Directive Arguments: One, required (admonition title)
:Directive Options: Possible, see below.
:Directive Content: Interpreted as body elements.
```

This is a generic, titled admonition.  The title may be anything the
author desires.

The author-supplied title is also used as a ["classes"] attribute value
after being converted into a valid identifier form (down-cased;
non-alphanumeric characters converted to single hyphens; "admonition-"
prefixed).  For example, this admonition:

```
.. admonition:: And, by the way...

   You can make up your own admonition too.
```

becomes the following document tree (pseudo-XML):

```
<document source="test data">
    <admonition classes="admonition-and-by-the-way">
        <title>
            And, by the way...
        <paragraph>
            You can make up your own admonition too.
```

The [common options] are recognized:

`class`

: Overrides the computed ["classes"] attribute value.

`name`

: Add `text` to the ["names"] attribute of the admonition element.

## Images

There are two image directives: "image" and "figure".

### Image

```{eval-rst}

:Directive Type: "image"
:Doctree Element: image_
:Directive Arguments: One, required (image URI).
:Directive Options: Possible.
:Directive Content: None.
```

An "image" is a simple picture:

```
.. image:: picture.png
```

Inline images can be defined with an "image" directive in a [substitution
definition][substitution definition]

The URI for the image source file is specified in the directive
argument.  As with hyperlink targets, the image URI may begin on the
same line as the explicit markup start and target name, or it may
begin in an indented text block immediately following, with no
intervening blank lines.  If there are multiple lines in the link
block, they are stripped of leading and trailing whitespace and joined
together.

Optionally, the image link block may contain a flat field list, the
`` _`image options` ``.  For example:

```
.. image:: picture.jpeg
   :height: 100px
   :width: 200 px
   :scale: 50 %
   :alt: alternate text
   :align: right
```

The following options are recognized:

`alt`

: Alternate text: a short description of the image, displayed by
  applications that cannot display images, or spoken by applications
  for visually impaired users.

`height`

: The desired height of the image.
  Used to reserve space or scale the image vertically.  When the "scale"
  option is also specified, they are combined.  For example, a height of
  200px and a scale of 50 is equivalent to a height of 100px with no scale.

`width`

: The width of the image.
  Used to reserve space or scale the image horizontally.  As with "height"
  above, when the "scale" option is also specified, they are combined.

`scale`

: The uniform scaling factor of the image.  The default is "100 %", i.e.
  no scaling.

  If no "height" or "width" options are specified, the [Python Imaging
  Library][python imaging library] (PIL) may be used to determine them, if it is installed and
  the image file is available.

`align`

: The alignment of the image, equivalent to the HTML `<img>` tag's
  "align" attribute.  The values "top", "middle", and "bottom"
  control an image's vertical alignment (relative to the text
  baseline); they are only useful for inline images (substitutions).
  The values "left", "center", and "right" control an image's
  horizontal alignment, allowing the image to float and have the
  text flow around it.  The specific behavior depends upon the
  browser or rendering software used.

`target`

: Makes the image into a hyperlink reference ("clickable").  The
  option argument may be a URI (relative or absolute), or a
  [reference name] with underscore suffix (e.g. `` `a name`_ ``).

and the common options [:class:] and [:name:].

### Figure

```{eval-rst}

:Directive Type: "figure"
:Doctree Elements: figure_, image_, caption_, legend_
:Directive Arguments: One, required (image URI).
:Directive Options: Possible.
:Directive Content: Interpreted as the figure caption and an optional
                    legend.
```

A "figure" consists of [image] data (including [image options]), an optional
caption (a single paragraph), and an optional legend (arbitrary body
elements). For page-based output media, figures might float to a different
position if this helps the page layout.

```
.. figure:: picture.png
   :scale: 50 %
   :alt: map to buried treasure

   This is the caption of the figure (a simple paragraph).

   The legend consists of all elements after the caption.  In this
   case, the legend consists of this paragraph and the following
   table:

   +-----------------------+-----------------------+
   | Symbol                | Meaning               |
   +=======================+=======================+
   | .. image:: tent.png   | Campground            |
   +-----------------------+-----------------------+
   | .. image:: waves.png  | Lake                  |
   +-----------------------+-----------------------+
   | .. image:: peak.png   | Mountain              |
   +-----------------------+-----------------------+
```

There must be blank lines before the caption paragraph and before the
legend.  To specify a legend without a caption, use an empty comment
("..") in place of the caption.

The "figure" directive supports all of the options of the "image"
directive (see [image options] above). These options (except
"align") are passed on to the contained image.

`align`

: The horizontal alignment of the figure, allowing the image to
  float and have the text flow around it.  The specific behavior
  depends upon the browser or rendering software used.

In addition, the following options are recognized:

`figwidth`

: The width of the figure.
  Limits the horizontal space used by the figure.
  A special value of "image" is allowed, in which case the
  included image's actual width is used (requires the [Python Imaging
  Library][python imaging library]). If the image file is not found or the required software is
  unavailable, this option is ignored.

  Sets the "width" attribute of the "figure" doctree element.

  This option does not scale the included image; use the "width"
  [image] option for that.

  ```
  +---------------------------+
  |        figure             |
  |                           |
  |<------ figwidth --------->|
  |                           |
  |  +---------------------+  |
  |  |     image           |  |
  |  |                     |  |
  |  |<--- width --------->|  |
  |  +---------------------+  |
  |                           |
  |The figure's caption should|
  |wrap at this width.        |
  +---------------------------+
  ```

`figclass`

: Set a ["classes"] attribute value on the figure element.  See the
  [class] directive below.

## Body Elements

### Topic

```{eval-rst}

:Directive Type: "topic"
:Doctree Element: topic_
:Directive Arguments: 1, required (topic title).
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Interpreted as the topic body.
```

A topic is like a block quote with a title, or a self-contained
section with no subsections.  Use the "topic" directive to indicate a
self-contained idea that is separate from the flow of the document.
Topics may occur anywhere a section or transition may occur.  Body
elements and topics may not contain nested topics.

The directive's sole argument is interpreted as the topic title; the
next line must be blank.  All subsequent lines make up the topic body,
interpreted as body elements.  For example:

```
.. topic:: Topic Title

    Subsequent indented lines comprise
    the body of the topic, and are
    interpreted as body elements.
```

### Sidebar

```{eval-rst}

:Directive Type: "sidebar"
:Doctree Element: sidebar_
:Directive Arguments: One, required (sidebar title).
:Directive Options: Possible (see below).
:Directive Content: Interpreted as the sidebar body.
```

Sidebars are like miniature, parallel documents that occur inside
other documents, providing related or reference material.  A sidebar
is typically offset by a border and "floats" to the side of the page;
the document's main text may flow around it.  Sidebars can also be
likened to super-footnotes; their content is outside of the flow of
the document's main text.

Sidebars may occur anywhere a section or transition may occur.  Body
elements (including sidebars) may not contain nested sidebars.

The directive's sole argument is interpreted as the sidebar title,
which may be followed by a subtitle option (see below); the next line
must be blank.  All subsequent lines make up the sidebar body,
interpreted as body elements.  For example:

```
.. sidebar:: Sidebar Title
   :subtitle: Optional Sidebar Subtitle

   Subsequent indented lines comprise
   the body of the sidebar, and are
   interpreted as body elements.
```

The following options are recognized:

`subtitle`

: The sidebar's subtitle.

and the common options [:class:] and [:name:].

### Line Block

:::{admonition} Deprecated
The "line-block" directive is deprecated.  Use the [line block
syntax][line block syntax] instead.
:::

```{eval-rst}

:Directive Type: "line-block"
:Doctree Element: line_block_
:Directive Arguments: None.
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Becomes the body of the line block.
```

The "line-block" directive constructs an element where line breaks and
initial indentation is significant and inline markup is supported.  It
is equivalent to a [parsed literal block] with different rendering:
typically in an ordinary serif typeface instead of a
typewriter/monospaced face, and not automatically indented.  (Have the
line-block directive begin a block quote to get an indented line
block.)  Line blocks are useful for address blocks and verse (poetry,
song lyrics), where the structure of lines is significant.  For
example, here's a classic:

```
"To Ma Own Beloved Lassie: A Poem on her 17th Birthday", by
Ewan McTeagle (for Lassie O'Shea):

    .. line-block::

        Lend us a couple of bob till Thursday.
        I'm absolutely skint.
        But I'm expecting a postal order and I can pay you back
            as soon as it comes.
        Love, Ewan.
```

(parsed-literal)=

### Parsed Literal Block

```{eval-rst}

:Directive Type: "parsed-literal"
:Doctree Element: literal_block_
:Directive Arguments: None.
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Becomes the body of the literal block.
```

Unlike an ordinary literal block, the "parsed-literal" directive
constructs a literal block where the text is parsed for inline markup.
It is equivalent to a [line block] with different rendering:
typically in a typewriter/monospaced typeface, like an ordinary
literal block.  Parsed literal blocks are useful for adding hyperlinks
to code examples.

However, care must be taken with the text, because inline markup is
recognized and there is no protection from parsing.  Backslash-escapes
may be necessary to prevent unintended parsing.  And because the
markup characters are removed by the parser, care must also be taken
with vertical alignment.  Parsed "ASCII art" is tricky, and extra
whitespace may be necessary.

For example, all the element names in this content model are links:

```
.. parsed-literal::

   ( (title_, subtitle_?)?,
     decoration_?,
     (docinfo_, transition_?)?,
     `%structure.model;`_ )
```

### Code

```{eval-rst}

:Directive Type: "code"
:Doctree Element: literal_block_, `inline elements`_
:Directive Arguments: One, optional (formal language).
:Directive Options: name, class, number-lines.
:Directive Content: Becomes the body of the literal block.
:Configuration Setting: syntax_highlight_.
```

(New in Docutils 0.9)

The "code" directive constructs a literal block. If the code language is
specified, the content is parsed by the [Pygments] syntax highlighter and
tokens are stored in nested [inline elements] with class arguments
according to their syntactic category. The actual highlighting requires
a style-sheet (e.g. one [generated by Pygments](http://pygments.org/docs/cmdline/#generating-styles), see the
[sandbox/stylesheets](http://docutils.sourceforge.net/sandbox/stylesheets/) for examples).

The parsing can be turned off with the [syntax_highlight] configuration
setting and command line option or by specifying the language as [:class:]
option instead of directive argument. This also avoids warnings
when [Pygments] is not installed or the language is not in the
[supported languages and markup formats].

For inline code, use the ["code" role].

The following options are recognized:

`number-lines`

: Precede every line with a line number.
  The optional argument is the number of the first line (defaut 1).

and the common options [:class:] and [:name:].

Example::

: The content of the following directive

  ```
  .. code:: python

    def my_function():
        "just a test"
        print 8/2
  ```

  is parsed and marked up as Python source code.

### Math

```{eval-rst}

:Directive Type: "math"
:Doctree Element: math_block_
:Directive Arguments: One, optional: prepended to content.
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Interpreted as math block(s).
                    Content blocks separated by a blank line are put in
                    separate math-block doctree elements.
:Configuration Setting: math_output_
```

(New in Docutils 0.8)

The "math" directive inserts blocks with mathematical content
(display formulas, equations) into the document. The input format is
*LaTeX math syntax*[^math-syntax] with support for Unicode
symbols, for example:

```
.. math::

  α_t(i) = P(O_1, O_2, … O_t, q_t = S_i λ)
```

Support is limited to a subset of *LaTeX math* by the conversion
required for many output formats.  For HTML, the the [math_output]
configuration setting (or the corresponding `--math-output`
command line option) select between alternative output formats with
different subsets of supported elements. If a writer does not
support math typesetting at all, the content is inserted verbatim.

[^math-syntax]: The supported LaTeX commands include AMS extensions
    (see, e.g., the [Short Math Guide]).

For inline math, use the ["math" role].

### Rubric

```{eval-rst}

:Directive Type: "rubric"
:Doctree Element: rubric_
:Directive Arguments: 1, required (rubric text).
:Directive Options: `:class:`_, `:name:`_
:Directive Content: None.
```

%

> rubric n. 1. a title, heading, or the like, in a manuscript,
> book, statute, etc., written or printed in red or otherwise
> distinguished from the rest of the text. ...
>
> <p class="attribution">-Random House Webster's College Dictionary, 1991</p>

The "rubric" directive inserts a "rubric" element into the document
tree.  A rubric is like an informal heading that doesn't correspond to
the document's structure.

### Epigraph

```{eval-rst}

:Directive Type: "epigraph"
:Doctree Element: block_quote_
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Interpreted as the body of the block quote.
```

An epigraph is an apposite (suitable, apt, or pertinent) short
inscription, often a quotation or poem, at the beginning of a document
or section.

The "epigraph" directive produces an "epigraph"-class block quote.
For example, this input:

```
.. epigraph::

   No matter where you go, there you are.

   -- Buckaroo Banzai
```

becomes this document tree fragment:

```
<block_quote classes="epigraph">
    <paragraph>
        No matter where you go, there you are.
    <attribution>
        Buckaroo Banzai
```

### Highlights

```{eval-rst}

:Directive Type: "highlights"
:Doctree Element: block_quote_
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Interpreted as the body of the block quote.
```

Highlights summarize the main points of a document or section, often
consisting of a list.

The "highlights" directive produces a "highlights"-class block quote.
See [Epigraph] above for an analogous example.

### Pull-Quote

```{eval-rst}

:Directive Type: "pull-quote"
:Doctree Element: block_quote_
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Interpreted as the body of the block quote.
```

A pull-quote is a small selection of text "pulled out and quoted",
typically in a larger typeface.  Pull-quotes are used to attract
attention, especially in long articles.

The "pull-quote" directive produces a "pull-quote"-class block quote.
See [Epigraph] above for an analogous example.

### Compound Paragraph

```{eval-rst}

:Directive Type: "compound"
:Doctree Element: compound_
:Directive Arguments: None.
:Directive Options: `:class:`_, `:name:`_
:Directive Content: Interpreted as body elements.
```

(New in Docutils 0.3.6)

The "compound" directive is used to create a compound paragraph, which
is a single logical paragraph containing multiple physical body
elements such as simple paragraphs, literal blocks, tables, lists,
etc., instead of directly containing text and inline elements.  For
example:

```
.. compound::

   The 'rm' command is very dangerous.  If you are logged
   in as root and enter ::

       cd /
       rm -rf *

   you will erase the entire contents of your file system.
```

In the example above, a literal block is "embedded" within a sentence
that begins in one physical paragraph and ends in another.

:::{note}
The "compound" directive is *not* a generic block-level container
like HTML's `<div>` element.  Do not use it only to group a
sequence of elements, or you may get unexpected results.

If you need a generic block-level container, please use the
[container] directive, described below.
:::

Compound paragraphs are typically rendered as multiple distinct text
blocks, with the possibility of variations to emphasize their logical
unity:

- If paragraphs are rendered with a first-line indent, only the first
  physical paragraph of a compound paragraph should have that indent
  -- second and further physical paragraphs should omit the indents;
- vertical spacing between physical elements may be reduced;
- and so on.

### Container

```{eval-rst}

:Directive Type: "container"
:Doctree Element: container_
:Directive Arguments: One or more, optional (class names).
:Directive Options: `:name:`_
:Directive Content: Interpreted as body elements.
```

(New in Docutils 0.3.10)

The "container" directive surrounds its contents (arbitrary body
elements) with a generic block-level "container" element.  Combined
with the optional "[classes]" attribute argument(s), this is an
extension mechanism for users & applications.  For example:

```
.. container:: custom

   This paragraph might be rendered in a custom way.
```

Parsing the above results in the following pseudo-XML:

```
<container classes="custom">
    <paragraph>
        This paragraph might be rendered in a custom way.
```

The "container" directive is the equivalent of HTML's `<div>`
element.  It may be used to group a sequence of elements for user- or
application-specific purposes.

## Tables

Formal tables need more structure than the reStructuredText syntax
supplies.  Tables may be given titles with the [table] directive.
Sometimes reStructuredText tables are inconvenient to write, or table
data in a standard format is readily available.  The [csv-table]
directive supports CSV data.

### Table

```{eval-rst}

:Directive Type: "table"
:Doctree Element: table_
:Directive Arguments: 1, optional (table title).
:Directive Options: `:class:`_, `:name:`_
:Directive Content: A normal reStructuredText table.
```

(New in Docutils 0.3.1)

The "table" directive is used to create a titled table, to associate a
title with a table:

```
.. table:: Truth table for "not"

   =====  =====
     A    not A
   =====  =====
   False  True
   True   False
   =====  =====
```

(csv-table)=

### CSV Table

```{eval-rst}

:Directive Type: "csv-table"
:Doctree Element: table_
:Directive Arguments: 1, optional (table title).
:Directive Options: Possible (see below).
:Directive Content: A CSV (comma-separated values) table.
```

:::{WARNING}
The "csv-table" directive's ":file:" and ":url:" options represent
a potential security holes.  They can be disabled with the
"[file_insertion_enabled]" runtime setting.
:::

(New in Docutils 0.3.4)

The "csv-table" directive is used to create a table from CSV
(comma-separated values) data.  CSV is a common data format generated
by spreadsheet applications and commercial databases.  The data may be
internal (an integral part of the document) or external (a separate
file).

Example:

```
.. csv-table:: Frozen Delights!
   :header: "Treat", "Quantity", "Description"
   :widths: 15, 10, 30

   "Albatross", 2.99, "On a stick!"
   "Crunchy Frog", 1.49, "If we took the bones out, it wouldn't be
   crunchy, now would it?"
   "Gannet Ripple", 1.99, "On a stick!"
```

Block markup and inline markup within cells is supported.  Line ends
are recognized within cells.

Working limitations:

- There is no support for checking that the number of columns in each
  row is the same.  However, this directive supports CSV generators
  that do not insert "empty" entries at the end of short rows, by
  automatically adding empty entries.

  % Add "strict" option to verify input?

[^whitespace-delim]: Whitespace delimiters are supported only for external
    CSV files.

[^ascii-char]: With Python 2, the valuess for the `delimiter`,
    `quote`, and `escape` options must be ASCII characters. (The csv
    module does not support Unicode and all non-ASCII characters are
    encoded as multi-byte utf-8 string). This limitation does not exist
    under Python 3.

The following options are recognized:

`widths`

: A comma- or space-separated list of relative column widths.  The
  default is equal-width columns (100%/#columns).

`header-rows`

: The number of rows of CSV data to use in the table header.
  Defaults to 0.

`stub-columns`

: The number of table columns to use as stubs (row titles, on the
  left).  Defaults to 0.

`header`

: Supplemental data for the table header, added independently of and
  before any `header-rows` from the main CSV data.  Must use the
  same CSV format as the main CSV data.

`file`

: The local filesystem path to a CSV data file.

`url`

: An Internet URL reference to a CSV data file.

`encoding`

: The text encoding of the external CSV data (file or URL).
  Defaults to the document's encoding (if specified).

`delim`

: A one-character string[^ascii-char] used to separate fields.
  Defaults to `,` (comma).  May be specified as a Unicode code
  point; see the [unicode] directive for syntax details.

`quote`

: A one-character string[^ascii-char] used to quote elements
  containing the delimiter or which start with the quote
  character.  Defaults to `"` (quote).  May be specified as a
  Unicode code point; see the [unicode] directive for syntax
  details.

`keepspace`

: Treat whitespace immediately following the delimiter as
  significant.  The default is to ignore such whitespace.

`escape`

: A one-character[^ascii-char] string used to escape the
  delimiter or quote characters.  May be specified as a Unicode
  code point; see the [unicode] directive for syntax details.  Used
  when the delimiter is used in an unquoted field, or when quote
  characters are used within a field.  The default is to double-up
  the character, e.g. "He said, ""Hi!"""

  % Add another possible value, "double", to explicitly indicate
  % the default case?

and the common options [:class:] and [:name:].

### List Table

```{eval-rst}

:Directive Type: "list-table"
:Doctree Element: table_
:Directive Arguments: 1, optional (table title).
:Directive Options: Possible (see below).
:Directive Content: A uniform two-level bullet list.
```

(New in Docutils 0.3.8.  This is an initial implementation; [further
ideas](../../dev/rst/alternatives.html#list-driven-tables) may be implemented in the future.)

The "list-table" directive is used to create a table from data in a
uniform two-level bullet list.  "Uniform" means that each sublist
(second-level list) must contain the same number of list items.

Example:

```
.. list-table:: Frozen Delights!
   :widths: 15 10 30
   :header-rows: 1

   * - Treat
     - Quantity
     - Description
   * - Albatross
     - 2.99
     - On a stick!
   * - Crunchy Frog
     - 1.49
     - If we took the bones out, it wouldn't be
       crunchy, now would it?
   * - Gannet Ripple
     - 1.99
     - On a stick!
```

The following options are recognized:

`widths`

: A comma- or space-separated list of relative column widths.  The
  default is equal-width columns (100%/#columns).

`header-rows`

: The number of rows of list data to use in the table header.
  Defaults to 0.

`stub-columns`

: The number of table columns to use as stubs (row titles, on the
  left).  Defaults to 0.

and the common options [:class:] and [:name:].

## Document Parts

(contents)=

### Table of Contents

```{eval-rst}

:Directive Type: "contents"
:Doctree Elements: pending_, topic_
:Directive Arguments: One, optional: title.
:Directive Options: Possible.
:Directive Content: None.
```

The "contents" directive generates a table of contents (TOC) in a
[topic].  Topics, and therefore tables of contents, may occur anywhere
a section or transition may occur.  Body elements and topics may not
contain tables of contents.

Here's the directive in its simplest form:

```
.. contents::
```

Language-dependent boilerplate text will be used for the title.  The
English default title text is "Contents".

An explicit title may be specified:

```
.. contents:: Table of Contents
```

The title may span lines, although it is not recommended:

```
.. contents:: Here's a very long Table of
   Contents title
```

Options may be specified for the directive, using a field list:

```
.. contents:: Table of Contents
   :depth: 2
```

If the default title is to be used, the options field list may begin
on the same line as the directive marker:

```
.. contents:: :depth: 2
```

The following options are recognized:

`depth`

: The number of section levels that are collected in the table of
  contents.  The default is unlimited depth.

`local`

: Generate a local table of contents.  Entries will only include
  subsections of the section in which the directive is given.  If no
  explicit title is given, the table of contents will not be titled.

`backlinks`

: Generate links from section headers back to the table of contents
  entries, the table of contents itself, or generate no backlinks.

`class`

: Set a ["classes"] attribute value on the topic element.  See the
  [class] directive below.

(sectnum)=

(section-numbering)=

### Automatic Section Numbering

```{eval-rst}

:Directive Type: "sectnum" or "section-numbering" (synonyms)
:Doctree Elements: pending_, generated_
:Directive Arguments: None.
:Directive Options: Possible.
:Directive Content: None.
:Configuration Setting: sectnum_xform_
```

The "sectnum" (or "section-numbering") directive automatically numbers
sections and subsections in a document (if not disabled by the
`--no-section-numbering` command line option or the [sectnum_xform]
configuration setting).

Section numbers are of the "multiple enumeration" form, where each
level has a number, separated by periods.  For example, the title of section
1, subsection 2, subsubsection 3 would have "1.2.3" prefixed.

The "sectnum" directive does its work in two passes: the initial parse
and a transform.  During the initial parse, a "pending" element is
generated which acts as a placeholder, storing any options internally.
At a later stage in the processing, the "pending" element triggers a
transform, which adds section numbers to titles.  Section numbers are
enclosed in a "generated" element, and titles have their "auto"
attribute set to "1".

The following options are recognized:

`depth`

: The number of section levels that are numbered by this directive.
  The default is unlimited depth.

`prefix`

: An arbitrary string that is prefixed to the automatically
  generated section numbers.  It may be something like "3.2.", which
  will produce "3.2.1", "3.2.2", "3.2.2.1", and so on.  Note that
  any separating punctuation (in the example, a period, ".") must be
  explicitly provided.  The default is no prefix.

`suffix`

: An arbitrary string that is appended to the automatically
  generated section numbers.  The default is no suffix.

`start`

: The value that will be used for the first section number.
  Combined with `prefix`, this may be used to force the right
  numbering for a document split over several source files.  The
  default is 1.

(header)=

(footer)=

### Document Header & Footer

```{eval-rst}

:Directive Types: "header" and "footer"
:Doctree Elements: decoration_, header, footer
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Interpreted as body elements.
```

(New in Docutils 0.3.8)

The "header" and "footer" directives create document decorations,
useful for page navigation, notes, time/datestamp, etc.  For example:

```
.. header:: This space for rent.
```

This will add a paragraph to the document header, which will appear at
the top of the generated web page or at the top of every printed page.

These directives may be used multiple times, cumulatively.  There is
currently support for only one header and footer.

:::{note}
While it is possible to use the "header" and "footer" directives to
create navigational elements for web pages, you should be aware
that Docutils is meant to be used for *document* processing, and
that a navigation bar is not typically part of a document.

Thus, you may soon find Docutils' abilities to be insufficient for
these purposes.  At that time, you should consider using a
documentation generator like [Sphinx] rather than the "header" and
"footer" directives.
:::

In addition to the use of these directives to populate header and
footer content, content may also be added automatically by the
processing system.  For example, if certain runtime settings are
enabled, the document footer is populated with processing information
such as a datestamp, a link to [the Docutils website], etc.

## References

(target-notes)=

### Target Footnotes

```{eval-rst}

:Directive Type: "target-notes"
:Doctree Elements: pending_, footnote_, footnote_reference_
:Directive Arguments: None.
:Directive Options: `:class:`_, `:name:`_
:Directive Options: Possible.
:Directive Content: None.
```

The "target-notes" directive creates a footnote for each external
target in the text, and corresponding footnote references after each
reference.  For every explicit target (of the form, `.. _target name:
URL`) in the text, a footnote will be generated containing the
visible URL as content.

### Footnotes

**NOT IMPLEMENTED YET**

```{eval-rst}

:Directive Type: "footnotes"
:Doctree Elements: pending_, topic_
:Directive Arguments: None?
:Directive Options: Possible?
:Directive Content: None.
```

@@@

### Citations

**NOT IMPLEMENTED YET**

```{eval-rst}

:Directive Type: "citations"
:Doctree Elements: pending_, topic_
:Directive Arguments: None?
:Directive Options: Possible?
:Directive Content: None.
```

@@@

## HTML-Specific

### Meta

```{eval-rst}

:Directive Type: "meta"
:Doctree Element: meta (non-standard)
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Must contain a flat field list.
```

The "meta" directive is used to specify HTML metadata stored in HTML
META tags.  "Metadata" is data about data, in this case data about web
pages.  Metadata is used to describe and classify web pages in the
World Wide Web, in a form that is easy for search engines to extract
and collate.

Within the directive block, a flat field list provides the syntax for
metadata.  The field name becomes the contents of the "name" attribute
of the META tag, and the field body (interpreted as a single string
without inline markup) becomes the contents of the "content"
attribute.  For example:

```
.. meta::
   :description: The reStructuredText plaintext markup language
   :keywords: plaintext, markup language
```

This would be converted to the following HTML:

```
<meta name="description"
    content="The reStructuredText plaintext markup language">
<meta name="keywords" content="plaintext, markup language">
```

Support for other META attributes ("http-equiv", "scheme", "lang",
"dir") are provided through field arguments, which must be of the form
"attr=value":

```
.. meta::
   :description lang=en: An amusing story
   :description lang=fr: Une histoire amusante
```

And their HTML equivalents:

```
<meta name="description" lang="en" content="An amusing story">
<meta name="description" lang="fr" content="Une histoire amusante">
```

Some META tags use an "http-equiv" attribute instead of the "name"
attribute.  To specify "http-equiv" META tags, simply omit the name:

```
.. meta::
   :http-equiv=Content-Type: text/html; charset=ISO-8859-1
```

HTML equivalent:

```
<meta http-equiv="Content-Type"
     content="text/html; charset=ISO-8859-1">
```

### Imagemap

**NOT IMPLEMENTED YET**

Non-standard element: imagemap.

## Directives for Substitution Definitions

The directives in this section may only be used in substitution
definitions.  They may not be used directly, in standalone context.
The [image] directive may be used both in substitution definitions
and in the standalone context.

(replace)=

### Replacement Text

```{eval-rst}

:Directive Type: "replace"
:Doctree Element: Text & `inline elements`_
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: A single paragraph; may contain inline markup.
```

The "replace" directive is used to indicate replacement text for a
substitution reference.  It may be used within substitution
definitions only.  For example, this directive can be used to expand
abbreviations:

```
.. |reST| replace:: reStructuredText

Yes, |reST| is a long word, so I can't blame anyone for wanting to
abbreviate it.
```

As reStructuredText doesn't support nested inline markup, the only way
to create a reference with styled text is to use substitutions with
the "replace" directive:

```
I recommend you try |Python|_.

.. |Python| replace:: Python, *the* best language around
.. _Python: http://www.python.org/
```

(unicode)=

### Unicode Character Codes

```{eval-rst}

:Directive Type: "unicode"
:Doctree Element: Text
:Directive Arguments: One or more, required (Unicode character codes,
                      optional text, and comments).
:Directive Options: Possible.
:Directive Content: None.
```

The "unicode" directive converts Unicode character codes (numerical
values) to characters, and may be used in substitution definitions
only.

The arguments, separated by spaces, can be:

- **character codes** as

  - decimal numbers or
  - hexadecimal numbers, prefixed by `0x`, `x`, `\x`, `U+`,
    `u`, or `\u` or as XML-style hexadecimal character entities,
    e.g. `&#x1a2b;`

- **text**, which is used as-is.

Text following " .. " is a comment and is ignored.  The spaces between
the arguments are ignored and thus do not appear in the output.
Hexadecimal codes are case-insensitive.

For example, the following text:

```
Copyright |copy| 2003, |BogusMegaCorp (TM)| |---|
all rights reserved.

.. |copy| unicode:: 0xA9 .. copyright sign
.. |BogusMegaCorp (TM)| unicode:: BogusMegaCorp U+2122
   .. with trademark sign
.. |---| unicode:: U+02014 .. em dash
   :trim:
```

results in:

> Copyright {{ copy }} 2003, {{ BogusMegaCorp (TM) }} {{ --- }}
> all rights reserved.

The following options are recognized:

`ltrim`

: Whitespace to the left of the substitution reference is removed.

`rtrim`

: Whitespace to the right of the substitution reference is removed.

`trim`

: Equivalent to `ltrim` plus `rtrim`; whitespace on both sides
  of the substitution reference is removed.

### Date

```{eval-rst}

:Directive Type: "date"
:Doctree Element: Text
:Directive Arguments: One, optional (date format).
:Directive Options: None.
:Directive Content: None.
```

The "date" directive generates the current local date and inserts it
into the document as text.  This directive may be used in substitution
definitions only.

The optional directive content is interpreted as the desired date
format, using the same codes as Python's time.strftime function.  The
default format is "%Y-%m-%d" (ISO 8601 date), but time fields can also
be used.  Examples:

```
.. |date| date::
.. |time| date:: %H:%M

Today's date is |date|.

This document was generated on |date| at |time|.
```

## Miscellaneous

(include)=

### Including an External Document Fragment

```{eval-rst}

:Directive Type: "include"
:Doctree Elements: Depend on data being included
                   (literal_block_ with ``code`` or ``literal`` option).
:Directive Arguments: One, required (path to the file to include).
:Directive Options: Possible.
:Directive Content: None.
:Configuration Setting: file_insertion_enabled_
```

:::{WARNING}
The "include" directive represents a potential security hole.  It
can be disabled with the "[file_insertion_enabled]" runtime setting.
:::

The "include" directive reads a text file. The directive argument is
the path to the file to be included, relative to the document
containing the directive. Unless the options `literal` or `code`
are given, the file is parsed in the current document's context at the
point of the directive. For example:

```
This first example will be parsed at the document level, and can
thus contain any construct, including section headers.

.. include:: inclusion.txt

Back in the main document.

    This second example will be parsed in a block quote context.
    Therefore it may only contain body elements.  It may not
    contain section headers.

    .. include:: inclusion.txt
```

If an included document fragment contains section structure, the title
adornments must match those of the master document.

Standard data files intended for inclusion in reStructuredText
documents are distributed with the Docutils source code, located in
the "docutils" package in the `docutils/parsers/rst/include`
directory.  To access these files, use the special syntax for standard
"include" data files, angle brackets around the file name:

```
.. include:: <isonum.txt>
```

The current set of standard "include" data files consists of sets of
substitution definitions.  See [reStructuredText Standard Definition
Files](definitions.html) for details.

The following options are recognized:

`start-line`

: Only the content starting from this line will be included.
  (As usual in Python, the first line has index 0 and negative values
  count from the end.)

`end-line`

: Only the content up to (but excluding) this line will be included.

`start-after`

: Only the content after the first occurrence of the specified text
  will be included.

`end-before`

: Only the content before the first occurrence of the specified text
  (but after any `after` text) will be included.

`literal`

: The entire included text is inserted into the document as a single
  literal block.

`code`

: The argument and the content of the included file are passed to
  the [code] directive (useful for program listings).
  (New in Docutils 0.9)

`number-lines`

: Precede every code line with a line number.
  The optional argument is the number of the first line (defaut 1).
  Works only with `code` or `literal`.
  (New in Docutils 0.9)

`encoding`

: The text encoding of the external data file.  Defaults to the
  document's [input_encoding].

`tab-width`

: Number of spaces for hard tab expansion.
  A negative value prevents expansion of hard tabs. Defaults to the
  [tab_width] configuration setting.

With `code` or `literal` the common options [:class:] and
[:name:] are recognized as well.

Combining `start/end-line` and `start-after/end-before` is possible. The
text markers will be searched in the specified lines (further limiting the
included content).

(raw-directive)=

### Raw Data Pass-Through

```{eval-rst}

:Directive Type: "raw"
:Doctree Element: raw_
:Directive Arguments: One or more, required (output format types).
:Directive Options: Possible.
:Directive Content: Stored verbatim, uninterpreted.  None (empty) if a
                    "file" or "url" option given.
:Configuration Setting: raw_enabled_
```

:::{WARNING}
The "raw" directive represents a potential security hole.  It can
be disabled with the "[raw_enabled]" or "[file_insertion_enabled]"
runtime settings.
:::

:::{Caution}
The "raw" directive is a stop-gap measure allowing the author to
bypass reStructuredText's markup.  It is a "power-user" feature
that should not be overused or abused.  The use of "raw" ties
documents to specific output formats and makes them less portable.

If you often need to use the "raw" directive or a "raw"-derived
interpreted text role, that is a sign either of overuse/abuse or
that functionality may be missing from reStructuredText.  Please
describe your situation in a message to the [Docutils-users] mailing
list.
:::

The "raw" directive indicates non-reStructuredText data that is to be
passed untouched to the Writer.  The names of the output formats are
given in the directive arguments.  The interpretation of the raw data
is up to the Writer.  A Writer may ignore any raw output not matching
its format.

For example, the following input would be passed untouched by an HTML
Writer:

```
.. raw:: html

   <hr width=50 size=10>
```

A LaTeX Writer could insert the following raw content into its
output stream:

```
.. raw:: latex

   \setlength{\parindent}{0pt}
```

Raw data can also be read from an external file, specified in a
directive option.  In this case, the content block must be empty.  For
example:

```
.. raw:: html
   :file: inclusion.html
```

Inline equivalents of the "raw" directive can be defined via
[custom interpreted text roles] derived from the ["raw" role].

The following options are recognized:

`file`

: The local filesystem path of a raw data file to be included.

`url`

: An Internet URL reference to a raw data file to be included.

`encoding`

: The text encoding of the external raw data (file or URL).
  Defaults to the document's encoding (if specified).

(classes)=

### Class

```{eval-rst}

:Directive Type: "class"
:Doctree Element: pending_
:Directive Arguments: One or more, required (class names / attribute
                      values).
:Directive Options: None.
:Directive Content: Optional.  If present, it is interpreted as body
                    elements.
```

The "class" directive sets the ["classes"] attribute value on its content
or on the first immediately following non-comment element [^id13].  For
details of the "classes" attribute, see [its entry](../doctree.html#classes) in [The Docutils
Document Tree][the docutils document tree].

The directive argument consists of one or more space-separated class
names. The names are transformed to conform to the regular expression
`[a-z](-?[a-z0-9]+)*` by converting

- alphabetic characters to lowercase,
- accented characters to the base character,
- non-alphanumeric characters to hyphens,
- consecutive hyphens into one hyphen.

For example "Rot-Gelb.Blau Grün:+2008" becomes "rot-gelb-blau grun-2008".
(For the [rationale], see below.)

Examples:

```
.. class:: special

This is a "special" paragraph.

.. class:: exceptional remarkable

An Exceptional Section
======================

This is an ordinary paragraph.

.. class:: multiple

   First paragraph.

   Second paragraph.
```

The text above is parsed and transformed into this doctree fragment:

```
<paragraph classes="special">
    This is a "special" paragraph.
<section classes="exceptional remarkable">
    <title>
        An Exceptional Section
    <paragraph>
        This is an ordinary paragraph.
    <paragraph classes="multiple">
        First paragraph.
    <paragraph classes="multiple">
        Second paragraph.
```

[^id13]: To set a "classes" attribute value on a block quote, the
    "class" directive must be followed by an empty comment:

    ```
    .. class:: highlights
    ..

        Block quote text.
    ```

    Without the empty comment, the indented text would be interpreted as the
    "class" directive's content, and the classes would be applied to each
    element (paragraph, in this case) individually, instead of to the block
    quote as a whole.

(rationale)=

:::{topic} Rationale for "classes" Attribute Value Conversion
Docutils identifiers are converted to conform to the regular
expression `[a-z](-?[a-z0-9]+)*`.  For HTML + CSS compatibility,
identifiers (the "classes" and "id" attributes) should have no
underscores, colons, or periods.  Hyphens may be used.

- The [HTML 4.01 spec] defines identifiers based on SGML tokens:

  > ID and NAME tokens must begin with a letter (\[A-Za-z\]) and
  > may be followed by any number of letters, digits (\[0-9\]),
  > hyphens ("-"), underscores ("\_"), colons (":"), and periods
  > (".").

- The [CSS1 spec] defines identifiers based on the "name" token
  ("flex" tokenizer notation below; "latin1" and "escape" 8-bit
  characters have been replaced with XML entities):

  ```
  unicode     \\[0-9a-f]{1,4}
  latin1      [&iexcl;-&yuml;]
  escape      {unicode}|\\[ -~&iexcl;-&yuml;]
  nmchar      [-A-Za-z0-9]|{latin1}|{escape}
  name        {nmchar}+
  ```

The CSS rule does not include underscores ("\_"), colons (":"), or
periods ("."), therefore "classes" and "id" attributes should not
contain these characters.  Combined with HTML's requirements (the
first character must be a letter; no "unicode", "latin1", or
"escape" characters), this results in the regular expression
`[A-Za-z][-A-Za-z0-9]*`. Docutils adds a normalisation by
downcasing and merge of consecutive hyphens.
:::

(role)=

### Custom Interpreted Text Roles

```{eval-rst}

:Directive Type: "role"
:Doctree Element: None; affects subsequent parsing.
:Directive Arguments: Two; one required (new role name), one optional
                      (base role name, in parentheses).
:Directive Options: Possible (depends on base role).
:Directive Content: depends on base role.
```

(New in Docutils 0.3.2)

The "role" directive dynamically creates a custom interpreted text
role and registers it with the parser.  This means that after
declaring a role like this:

```
.. role:: custom
```

the document may use the new "custom" role:

```
An example of using :custom:`interpreted text`
```

This will be parsed into the following document tree fragment:

```
<paragraph>
    An example of using
    <inline classes="custom">
        interpreted text
```

The role must be declared in a document before it can be used.

The new role may be based on an existing role, specified as a second
argument in parentheses (whitespace optional):

```
.. role:: custom(emphasis)

:custom:`text`
```

The parsed result is as follows:

```
<paragraph>
    <emphasis classes="custom">
        text
```

A special case is the ["raw" role]: derived roles enable
inline [raw data pass-through], e.g.:

```
.. role:: raw-role(raw)
   :format: html latex

:raw-role:`raw text`
```

If no base role is explicitly specified, a generic custom role is
automatically used.  Subsequent interpreted text will produce an
"inline" element with a ["classes"] attribute, as in the first example
above.

With most roles, the ":class:" option can be used to set a "classes"
attribute that is different from the role name.  For example:

```
.. role:: custom
   :class: special

:custom:`interpreted text`
```

This is the parsed result:

```
<paragraph>
    <inline classes="special">
        interpreted text
```

(role-class)=

The following option is recognized by the "role" directive for most
base roles:

`class`

: Set the ["classes"] attribute value on the element produced
  (`inline`, or element associated with a base class) when the
  custom interpreted text role is used.  If no directive options are
  specified, a "class" option with the directive argument (role
  name) as the value is implied.  See the [class] directive above.

Specific base roles may support other options and/or directive
content.  See the [reStructuredText Interpreted Text Roles] document
for details.

(default-role)=

### Setting the Default Interpreted Text Role

```{eval-rst}

:Directive Type: "default-role"
:Doctree Element: None; affects subsequent parsing.
:Directive Arguments: One, optional (new default role name).
:Directive Options: None.
:Directive Content: None.
```

(New in Docutils 0.3.10)

The "default-role" directive sets the default interpreted text role,
the role that is used for interpreted text without an explicit role.
For example, after setting the default role like this:

```
.. default-role:: subscript
```

any subsequent use of implicit-role interpreted text in the document
will use the "subscript" role:

```
An example of a `default` role.
```

This will be parsed into the following document tree fragment:

```
<paragraph>
    An example of a
    <subscript>
        default
     role.
```

Custom roles may be used (see the "[role]" directive above), but it
must have been declared in a document before it can be set as the
default role.  See the [reStructuredText Interpreted Text Roles]
document for details of built-in roles.

The directive may be used without an argument to restore the initial
default interpreted text role, which is application-dependent.  The
initial default interpreted text role of the standard reStructuredText
parser is "title-reference".

### Metadata Document Title

```{eval-rst}

:Directive Type: "title"
:Doctree Element: None.
:Directive Arguments: 1, required (the title text).
:Directive Options: None.
:Directive Content: None.
```

The "title" directive specifies the document title as metadata, which
does not become part of the document body.  It overrides a
document-supplied title.  For example, in HTML output the metadata
document title appears in the title bar of the browser window.

### Restructuredtext-Test-Directive

```{eval-rst}

:Directive Type: "restructuredtext-test-directive"
:Doctree Element: system_warning
:Directive Arguments: None.
:Directive Options: None.
:Directive Content: Interpreted as a literal block.
```

This directive is provided for test purposes only.  (Nobody is
expected to type in a name *that* long!)  It is converted into a
level-1 (info) system message showing the directive data, possibly
followed by a literal block containing the rest of the directive
block.

## Common Options

Most of the directives that generate doctree elements support the following
options:

`` _`:class:` ``

: Set a ["classes"] attribute value on the doctree element generated by
  the directive. See also the [class] directive.

`` _`:name:` ``

: Add `text` to the ["names"] attribute of the doctree element generated
  by the directive. This allows [hyperlink references] to the element
  using `text` as [reference name].

  Specifying the `name` option of a directive, e.g.,

  ```
  .. image:: bild.png
     :name: my picture
  ```

  is a concise syntax alternative to preceding it with a [hyperlink
  target][hyperlink target]

  ```
  .. _my picture:

  .. image:: bild.png
  ```

  New in Docutils 0.8.

% Local Variables:
% mode: indented-text
% indent-tabs-mode: nil
% sentence-end-double-space: t
% fill-column: 70
% End:

["classes"]: ../doctree.html#classes
["code" role]: roles.html#code
["math" role]: roles.html#math
["names"]: ../doctree.html#names
["raw" role]: roles.html#raw
[admonition]: ../doctree.html#admonition
[block_quote]: ../doctree.html#block-quote
[caption]: ../doctree.html#caption
[compound]: ../doctree.html#compound
[container]: ../doctree.html#container
[creating restructuredtext directives]: ../../howto/rst-directives.html
[css1 spec]: http://www.w3.org/TR/REC-CSS1
[decoration]: ../doctree.html#decoration
[directives]: restructuredtext.html#directives
[docutils generic dtd]: ../docutils.dtd
[docutils-users]: ../../user/mailing-lists.html#docutils-users
[figure]: ../doctree.html#figure
[file_insertion_enabled]: ../../user/config.html#file-insertion-enabled
[footnote]: ../doctree.html#footnote
[footnote_reference]: ../doctree.html#footnote-reference
[generated]: ../doctree.html#generated
[html 4.01 spec]: http://www.w3.org/TR/html401/
[hyperlink references]: restructuredtext.html#hyperlink-references
[hyperlink target]: restructuredtext.html#hyperlink-targets
[image]: ../doctree.html#image
[inline elements]: ../doctree.html#inline-elements
[input_encoding]: ../../user/config.html#input-encoding
[legend]: ../doctree.html#legend
[length]: restructuredtext.html#length-units
[line block syntax]: restructuredtext.html#line-blocks
[line_block]: ../doctree.html#line-block
[literal_block]: ../doctree.html#literal-block
[math_block]: ../doctree.html#math-block
[math_output]: ../../user/config.html#math-output
[pending]: ../doctree.html#pending
[percentage]: restructuredtext.html#percentage-units
[pygments]: http://pygments.org/
[python imaging library]: http://www.pythonware.com/products/pil/
[raw]: ../doctree.html#raw
[raw_enabled]: ../../user/config.html#raw-enabled
[reference name]: restructuredtext.html#reference-names
[restructuredtext interpreted text roles]: roles.html
[restructuredtext markup specification]: restructuredtext.html
[rubric]: ../doctree.html#rubric
[sectnum_xform]: ../../user/config.html#sectnum-xform
[short math guide]: ftp://ftp.ams.org/ams/doc/amsmath/short-math-guide.pdf
[sidebar]: ../doctree.html#sidebar
[sphinx]: http://sphinx-doc.org/
[substitution definition]: restructuredtext.html#substitution-definitions
[supported languages and markup formats]: http://pygments.org/languages/
[syntax_highlight]: ../../user/config.html#syntax-highlight
[tab_width]: ../../user/config.html#tab-width
[table]: ../doctree.html#table
[the docutils document tree]: ../doctree.html
[the docutils website]: http://docutils.sourceforge.net
[title]: ../doctree.html#title
[topic]: ../doctree.html#topic
