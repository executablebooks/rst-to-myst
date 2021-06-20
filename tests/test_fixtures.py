from pathlib import Path

import pytest

from rst_to_myst import convert, to_ast
from rst_to_myst.utils import read_fixture_file

FIXTURE_PATH = Path(__file__).parent.joinpath("fixtures")


@pytest.mark.parametrize(
    "line,title,rst,expected",
    read_fixture_file(FIXTURE_PATH / "ast.txt"),
    ids=[f"{i[0]}-{i[1]}" for i in read_fixture_file(FIXTURE_PATH / "ast.txt")],
)
def test_ast(line, title, rst, expected):
    document, warning_stream = to_ast(rst)
    text = document.pformat()
    try:
        assert warning_stream.getvalue() == ""
        assert text.rstrip() == expected.rstrip()
    except AssertionError:
        print(text)
        raise


@pytest.mark.parametrize(
    "line,title,rst,expected",
    read_fixture_file(FIXTURE_PATH / "render.txt"),
    ids=[f"{i[0]}-{i[1]}" for i in read_fixture_file(FIXTURE_PATH / "render.txt")],
)
def test_render(line, title, rst, expected):
    text, warning_stream = convert(rst)
    try:
        assert warning_stream.getvalue() == ""
        assert text.rstrip() == expected.rstrip()
    except AssertionError:
        print(text)
        raise


@pytest.mark.parametrize(
    "line,title,rst,expected",
    read_fixture_file(FIXTURE_PATH / "render_mdit.txt"),
    ids=[f"{i[0]}-{i[1]}" for i in read_fixture_file(FIXTURE_PATH / "render_mdit.txt")],
)
def test_render_mdit(line, title, rst, expected):
    from mdformat.plugins import PARSER_EXTENSIONS
    from mdformat.renderer import MDRenderer

    from rst_to_myst.markdownit import MarkdownItRenderer
    from rst_to_myst.parser import to_ast

    document, warning_stream = to_ast(rst)
    token_renderer = MarkdownItRenderer(document, warning_stream=warning_stream)
    output = token_renderer.to_tokens()
    md_renderer = MDRenderer()
    # TODO option for consecutive numbering consecutive_numbering
    options = {
        "parser_extension": [
            PARSER_EXTENSIONS[name] for name in ["myst", "tables", "frontmatter"]
        ]
    }
    text = md_renderer.render(output.tokens, options, output.env)
    try:
        assert warning_stream.getvalue() == ""
        assert text.rstrip() == expected.rstrip()
    except AssertionError:
        print(text)
        raise
