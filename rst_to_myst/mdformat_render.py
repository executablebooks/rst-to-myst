from textwrap import indent
from typing import IO, Any, Dict, Iterable, List, NamedTuple, Optional

from markdown_it.token import Token
from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import MDRenderer, RenderContext, RenderTreeNode
from mdformat.renderer._util import longest_consecutive_sequence

from .markdownit import MarkdownItRenderer, RenderOutput
from .parser import to_docutils_ast
from .utils import yaml_dump


def _front_matter_tokens_render(node: RenderTreeNode, context: RenderContext) -> str:
    dct = {}
    for child in node.children:
        path = child.meta["key_path"]
        value = (
            "\n\n".join(subchild.render(context) for subchild in child.children)
            if child.children
            else True
        )
        subdct = dct
        for key in path[:-1]:
            subdct.setdefault(key, {})
            subdct = subdct[key]
        subdct[path[-1]] = value
    text = yaml_dump(dct).rstrip()
    return f"---\n{text}\n---"


def _sub_renderer(node: RenderTreeNode, context: RenderContext) -> str:
    return f"{{{{ {node.content} }}}}"


def _directive_render(node: RenderTreeNode, context: RenderContext) -> str:

    # special directives that should only be used within substitutions
    if node.meta["module"].endswith("misc.Replace") and node.children:
        return "\n\n".join(child.render(context) for child in node.children[-1])
    if node.meta["module"].endswith("misc.Date"):
        return "{sub-ref}`today`"

    name = node.meta["name"]
    info_str = code_block = ""

    if node.children and node.children[0].type == "directive_arg":
        info_str = "".join(child.render(context) for child in node.children[0])
        info_str = " " + " ".join(info_str.splitlines()).strip()

    if node.meta["options_list"]:
        yaml_str = yaml_dump(
            {
                key: (True if val is None else (int(val) if val.isnumeric() else val))
                for key, val in node.meta["options_list"]
            }
        )
        code_block = indent(yaml_str, ":", lambda s: True).strip()

    if node.children and node.children[-1].type == "directive_content":
        if code_block:
            code_block += "\n\n"
        code_block += "\n\n".join(child.render(context) for child in node.children[-1])

    # Info strings of backtick code fences can not contain backticks or tildes.
    # If that is the case, we make a tilde code fence instead.
    if node.markup and ":" in node.markup:
        fence_char = ":"
    elif "`" in info_str or "~" in info_str:
        fence_char = "~"
    else:
        fence_char = "`"

    # The code block must not include as long or longer sequence of `fence_char`s
    # as the fence string itself
    fence_len = max(3, longest_consecutive_sequence(code_block, fence_char) + 1)
    fence_str = fence_char * fence_len
    return f"{fence_str}{{{name}}}{info_str}\n{code_block}\n{fence_str}"


class AdditionalRenderers:
    RENDERERS = {
        "front_matter_tokens": _front_matter_tokens_render,
        "substitution_block": _sub_renderer,
        "substitution_inline": _sub_renderer,
        "directive": _directive_render,
    }


def from_tokens(output: RenderOutput, *, consecutive_numbering: bool = True) -> str:
    """Convert markdown-it tokens to text."""
    md_renderer = MDRenderer()
    # TODO option for consecutive numbering consecutive_numbering, etc
    options = {
        "parser_extension": [
            PARSER_EXTENSIONS[name]
            for name in ["myst", "tables", "frontmatter", "deflist"]
        ]
        + [AdditionalRenderers],
        "mdformat": {"number": consecutive_numbering},
    }
    # TODO redirect logging
    # mdformat outputs only used reference definitions during 'finalize'
    # instead we want to output all parsed reference definitions
    text = md_renderer.render(output.tokens, options, output.env, finalize=False)
    if output.env["references"]:
        if text:
            text += "\n\n"
        output.env["used_refs"] = set(output.env["references"])
        text += md_renderer._write_references(output.env)
    if text:
        text += "\n"
    return text


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
    colon_fences: bool = True,
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
    :param colon_fences: Use colon fences for directives with parsed content

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
        colon_fences=colon_fences,
    )
    output = token_renderer.to_tokens()
    output_text = from_tokens(output, consecutive_numbering=consecutive_numbering)
    return ConvertedOutput(output_text, output.tokens, output.env, warning_stream)
