from pathlib import Path

import pytest
from pytest_param_files import ParamTestData

from rst_to_myst import rst_to_myst, to_docutils_ast

FIXTURE_PATH = Path(__file__).parent.joinpath("fixtures")


@pytest.mark.param_file(FIXTURE_PATH / "ast.txt")
def test_ast(file_params: ParamTestData):
    document, warning_stream = to_docutils_ast(file_params.content)
    assert warning_stream.getvalue() == ""
    file_params.assert_expected(document.pformat(), rstrip=True)


@pytest.mark.param_file(FIXTURE_PATH / "render.txt")
def test_render(file_params: ParamTestData):
    output = rst_to_myst(file_params.content)
    if "EXPECT_WARNING" not in file_params.title:
        assert output.warning_stream.getvalue() == ""
    else:
        assert output.warning_stream.getvalue() != ""
    file_params.assert_expected(output.text, rstrip=True)


@pytest.mark.param_file(FIXTURE_PATH / "render_extra.txt")
def test_render_extra(file_params: ParamTestData):
    output = rst_to_myst(file_params.content)
    assert output.warning_stream.getvalue() == ""
    file_params.assert_expected(output.text, rstrip=True)
