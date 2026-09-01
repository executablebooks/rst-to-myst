"""Sphinx 8.2+ replaces docutils admonition classes; they must still convert."""

from docutils import nodes
from docutils.parsers.rst.directives.admonitions import BaseAdmonition

from rst_to_myst.mdformat_render import from_tokens
from rst_to_myst.markdownit import MarkdownItRenderer
from rst_to_myst.namespace import compile_namespace
from rst_to_myst.parser import to_docutils_ast


class Warning(BaseAdmonition):
    """Stand-in for ``sphinx.directives.admonitions.Warning``."""

    node_class = nodes.warning


Warning.__module__ = "sphinx.directives.admonitions"


def _convert(text: str) -> str:
    namespace = compile_namespace(use_sphinx=False)
    namespace.directives["warning"] = Warning
    document, warning_stream = to_docutils_ast(
        text, use_sphinx=False, namespace=namespace
    )
    assert warning_stream.getvalue() == ""
    tokens = MarkdownItRenderer(
        document,
        warning_stream=warning_stream,
        colon_fences=True,
        dollar_math=True,
    ).to_tokens()
    return from_tokens(tokens, warning_stream=warning_stream)


def test_sphinx_overridden_warning_is_not_eval_rst():
    # Issue #97: ``.. warning:: This is a warning`` became an eval-rst fence
    # after Sphinx started registering its own admonition classes.
    text = _convert(".. warning:: This is a warning\n")
    assert "{eval-rst}" not in text
    assert "This is a warning" in text
    assert "{warning}" in text
