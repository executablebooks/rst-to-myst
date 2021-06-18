from mdformat.renderer import MDRenderer

from rst_to_myst.markdownit import MarkdownItRenderer
from rst_to_myst.parser import to_ast


def test_basic():
    document, warning_stream = to_ast(
        """
``a
b``
"""
    )
    token_renderer = MarkdownItRenderer(document)
    tokens = token_renderer.to_tokens()
    print([(t.type, [c.type for c in t.children or ()]) for t in tokens])
    md_renderer = MDRenderer()
    text = md_renderer.render(tokens, {}, {})
    print(text)
    # raise
