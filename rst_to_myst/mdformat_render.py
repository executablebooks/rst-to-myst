from typing import IO, Any, Dict, Iterable, List, NamedTuple, Optional

from markdown_it.token import Token
from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import MDRenderer, RenderContext, RenderTreeNode

from .markdownit import MarkdownItRenderer, RenderOutput
from .parser import to_docutils_ast


def _sub_renderer(node: RenderTreeNode, context: RenderContext) -> str:
    return f"{{{{ {node.content} }}}}"


class AdditionalRenderers:
    RENDERERS = {
        "substitution_block": _sub_renderer,
        "substitution_inline": _sub_renderer,
    }


def from_tokens(output: RenderOutput, *, consecutive_numbering: bool = True) -> str:
    """Convert markdown-it tokens to text."""
    md_renderer = MDRenderer()
    # TODO option for consecutive numbering consecutive_numbering, etc
    options = {
        "parser_extension": [
            PARSER_EXTENSIONS[name] for name in ["myst", "tables", "frontmatter"]
        ]
        + [AdditionalRenderers],
        "mdformat": {"number": consecutive_numbering},
    }
    # TODO redirect logging
    return md_renderer.render(output.tokens, options, output.env)


class ConvertedOutput(NamedTuple):
    """Output from ``rst_to_myst``."""

    text: str
    tokens: List[Token]
    env: Dict[str, Any]
    warning_stream: IO
    # TODO list myst extensions required for parsing


def rst_to_myst(
    text: str,
    *,
    warning_stream: Optional[IO] = None,
    language_code="en",
    use_sphinx: bool = True,
    extensions: Iterable[str] = (),
    conversions: Optional[Dict[str, str]] = None,
    default_domain: str = "py",
    default_role: Optional[str] = None,
    raise_on_error: bool = False,
    cite_prefix: str = "cite_",
    consecutive_numbering: bool = True,
) -> ConvertedOutput:
    """Convert RST text to MyST Markdown text.

    :param text: The input RST text

    :param warning_stream: The warning IO to write to
    :param language_code: the language module to use,
        for directive/role name translation
    :param use_sphinx: Whether to load sphinx roles, directives and extentions
    :param extensions: Sphinx extension to load
    :param conversions: Overrides for mapping of how to convert directives;
        directive module path -> conversion type
    :param default_domain: name of the default sphinx domain
    :param default_role: name of the default role, otherwise convert to a literal

    :param cite_prefix: Prefix to add to citation references
    :param raise_on_error: Raise exception on parsing errors (or only warn)
    :param consecutive_numbering: Apply consecutive numbering to ordered lists

    """
    document, warning_stream = to_docutils_ast(
        text,
        warning_stream=warning_stream,
        language_code=language_code,
        use_sphinx=use_sphinx,
        extensions=extensions,
        default_domain=default_domain,
        conversions=conversions,
    )
    token_renderer = MarkdownItRenderer(
        document,
        warning_stream=warning_stream,
        cite_prefix=cite_prefix,
        raise_on_error=raise_on_error,
        default_role=default_role,
    )
    output = token_renderer.to_tokens()
    output_text = from_tokens(output, consecutive_numbering=consecutive_numbering)
    return ConvertedOutput(output_text, output.tokens, output.env, warning_stream)
