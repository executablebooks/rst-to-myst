from io import TextIOWrapper
from pathlib import Path

import click
import yaml

from . import compile_namespace, convert, to_ast
from .utils import yaml_dump


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option()
def main():
    """CLI for rst-to-myst"""


OPT_LANGUAGE = click.option(
    "--language",
    "-l",
    type=str,
    default="en",
    show_default=True,
    help="Language code for directive names",
)

# TODO don't hang when when no stdin provided (test file.isatty()?)
OPT_READ = click.option(
    "--file",
    "-f",
    type=click.File("r"),
    default="-",
    help="Input file [default: stdin]",
)


def read_conversions(ctx, param, value):
    if not value:
        return {}
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Path does not exist: {value}")
    with path.open("r") as handle:
        data = yaml.safe_load(handle)
    return data


OPT_CONVERSIONS = click.option(
    "--conversions",
    "-c",
    default=None,
    callback=read_conversions,
    metavar="PATH",
    help="YAML file containing directive conversions",
)


def check_sphinx(ctx, param, value):
    if not value:
        return value
    try:
        import sphinx  # noqa: F401
    except ImportError:
        raise click.BadParameter(
            "sphinx not installed: install or use '--no-sphinx' option"
        )
    return value


OPT_SPHINX = click.option(
    "--sphinx/--no-sphinx",
    "-s/-ns",
    is_flag=True,
    default=True,
    callback=check_sphinx,
    help="Load sphinx.",
)
OPT_EXTENSIONS = click.option(
    "--extensions", "-e", multiple=True, help="Load sphinx extensions."
)


@main.command("ast")
@OPT_READ
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_CONVERSIONS
def ast(file: TextIOWrapper, language: str, sphinx: bool, extensions, conversions):
    """Convert ReStructuredText to an Abstract Syntax Tree."""
    text = file.read()
    document, _ = to_ast(
        text,
        warning_stream=click.get_text_stream("stderr"),
        language_code=language,
        use_sphinx=sphinx,
        extensions=extensions,
        conversions=conversions,
    )
    output = document.pformat()
    click.echo(output)


@main.command("parse")
@OPT_READ
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_CONVERSIONS
def parse(file: TextIOWrapper, language: str, sphinx: bool, extensions, conversions):
    """Convert ReStructuredText to MyST Markdown."""
    text = file.read()
    output, _ = convert(
        text,
        click.get_text_stream("stderr"),
        language_code=language,
        use_sphinx=sphinx,
        extensions=extensions,
        conversions=conversions,
    )
    click.echo(output)


@main.group("directives")
def directives():
    """Commands for showing available directives."""


@directives.command("list")
@OPT_SPHINX
@OPT_EXTENSIONS
def directives_list(sphinx, extensions):
    """List available directives."""
    namespace = compile_namespace(extensions=extensions, use_sphinx=sphinx)
    click.echo(" ".join(namespace.list_directives()))


@directives.command("show")
@click.argument("name")
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_LANGUAGE
def directives_show(name, sphinx, extensions, language):
    """List available directives."""
    namespace = compile_namespace(
        extensions=extensions, use_sphinx=sphinx, language_code=language
    )
    try:
        data = namespace.get_directive_data(name)
    except KeyError as error:
        raise click.ClickException(str(error))
    click.echo(yaml_dump(data))


@main.group("roles")
def roles():
    """Commands for showing available roles."""


@roles.command("list")
@OPT_SPHINX
@OPT_EXTENSIONS
def roles_list(sphinx, extensions):
    """List available directives."""
    namespace = compile_namespace(extensions=extensions, use_sphinx=sphinx)
    click.echo(" ".join(namespace.list_roles()))


@roles.command("show")
@click.argument("name")
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_LANGUAGE
def roles_show(name, sphinx, extensions, language):
    """List available directives."""
    namespace = compile_namespace(
        extensions=extensions, use_sphinx=sphinx, language_code=language
    )
    try:
        data = namespace.get_role_data(name)
    except KeyError as error:
        raise click.ClickException(str(error))
    click.echo(yaml_dump(data))


if __name__ == "__main__":
    main()
