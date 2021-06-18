from mdformat.renderer import MDRenderer

from rst_to_myst.markdownit import MarkdownItRenderer
from rst_to_myst.parser import to_ast


def test_basic():
    document, warning_stream = to_ast(
        """
Python_

.. _Python: http://www.python.org/
"""
    )
    token_renderer = MarkdownItRenderer(document, warning_stream=warning_stream)
    output = token_renderer.to_tokens()
    print([(t.type, [c.type for c in t.children or ()]) for t in output.tokens])
    print(output.env)
    md_renderer = MDRenderer()
    text = md_renderer.render(output.tokens, {}, output.env)
    print(text)
    # raise
