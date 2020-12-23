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
