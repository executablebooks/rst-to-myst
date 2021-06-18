from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import MDRenderer

from rst_to_myst.markdownit import MarkdownItRenderer
from rst_to_myst.parser import to_ast


def test_basic():
    document, warning_stream = to_ast(
        r"""
Python_

.. _Python: http://www.python.org/

.. _a:

ab
==

.. comment

:role:`content`

----
"""
    )
    token_renderer = MarkdownItRenderer(document, warning_stream=warning_stream)
    output = token_renderer.to_tokens()
    print([(t.type, [c.type for c in t.children or ()]) for t in output.tokens])
    print(output.env)
    md_renderer = MDRenderer()
    options = {"parser_extension": [PARSER_EXTENSIONS["myst"]]}
    text = md_renderer.render(output.tokens, options, output.env)
    print(text)
    # raise
