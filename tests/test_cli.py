from pathlib import Path

from click.testing import CliRunner

from rst_to_myst import cli


def test_directives_list():
    runner = CliRunner()
    result = runner.invoke(cli.directives_list, [])
    assert result.exit_code == 0, result.output
    assert "admonition" in result.output


def test_roles_list():
    runner = CliRunner()
    result = runner.invoke(cli.roles_list, [])
    assert result.exit_code == 0
    assert "acronym" in result.output


def test_directives_show():
    runner = CliRunner()
    result = runner.invoke(cli.directives_show, ["admonition"])
    assert result.exit_code == 0
    assert "directives.admonitions.Admonition" in result.output


def test_directives_show_translate():
    runner = CliRunner()
    result = runner.invoke(cli.directives_show, ["-l", "fr", "astuce"])
    assert result.exit_code == 0
    assert "directives.admonitions.Tip" in result.output


def test_roles_show():
    runner = CliRunner()
    result = runner.invoke(cli.roles_show, ["acronym"])
    assert result.exit_code == 0
    assert "rst.roles" in result.output


def test_ast():
    runner = CliRunner()
    result = runner.invoke(cli.ast, ["-"], input=":name:`content`")
    assert result.exit_code == 0, result.output
    assert '<RoleNode role="name" text="content">' in result.output


def test_tokens():
    runner = CliRunner()
    result = runner.invoke(cli.tokens, ["-"], input=":name:`content`")
    assert result.exit_code == 0, result.output
    assert "paragraph_open" in result.output


def test_stream():
    runner = CliRunner()
    result = runner.invoke(cli.stream, ["-"], input=":name:`content`")
    assert result.exit_code == 0, result.output
    assert "{name}`content`" in result.output


def test_convert(tmp_path: Path, file_regression):
    tmp_path.joinpath("test.rst").write_text(
        "head\n====\n\ncontent `a`\n", encoding="utf8"
    )
    tmp_path.joinpath("config.yaml").write_text("default_role: math\n", encoding="utf8")
    runner = CliRunner()
    result = runner.invoke(
        cli.convert,
        [
            "--config",
            str(tmp_path.joinpath("config.yaml")),
            str(tmp_path.joinpath("test.rst")),
        ],
    )
    assert result.exit_code == 0, result.output
    assert tmp_path.joinpath("test.md").exists()
    file_regression.check(
        tmp_path.joinpath("test.md").read_text(encoding="utf8"),
        encoding="utf8",
        extension=".md",
    )


def test_convert_code_to_code_cell(tmp_path: Path, file_regression):
    tmp_path.joinpath("test-code-cell.rst").write_text(
        "head\n====\n\n.. code::\n\n\timport numpy as np", encoding="utf8"
    )
    tmp_path.joinpath("config-code-cell.yaml").write_text(
        "code_to_code_cell: true\n", encoding="utf8"
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.convert,
        [
            "--config",
            str(tmp_path.joinpath("config-code-cell.yaml")),
            str(tmp_path.joinpath("test-code-cell.rst")),
        ],
    )
    assert result.exit_code == 0, result.output
    assert tmp_path.joinpath("test-code-cell.md").exists()
    file_regression.check(
        tmp_path.joinpath("test-code-cell.md").read_text(encoding="utf8"),
        encoding="utf8",
        extension=".md",
    )
