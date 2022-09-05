from io import TextIOWrapper
from pathlib import Path
from typing import List, Mapping, Optional

import click
import yaml

from . import compile_namespace, rst_to_myst, to_docutils_ast
from .utils import yaml_dump


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option()
def main():
    """CLI for converting ReStructuredText to MyST Markdown."""


def read_config(ctx, param, value):
    if not value:
        return
    try:
        with open(value, encoding="utf8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        raise click.BadOptionUsage(
            "--config", f"Error reading configuration file: {exc}", ctx
        )

    ctx.default_map = ctx.default_map or {}
    ctx.default_map.update(data or {})

    return value


OPT_CONFIG = click.option(
    "--config",
    help="YAML file to read default configuration from",
    is_eager=True,
    expose_value=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    callback=read_config,
)


OPT_LANGUAGE = click.option(
    "--language",
    "-l",
    type=str,
    default="en",
    show_default=True,
    help="Language code for directive names",
)


ARG_STREAM = click.argument("stream", type=click.File("r"), metavar="PATH_OR_STDIN")


ARG_PATHS = click.argument(
    "paths",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    nargs=-1,
)

OPT_ENCODING = click.option(
    "--encoding", default="utf8", show_default=True, help="Encoding for read/write"
)


def read_conversions(ctx, param, value):
    if not value:
        return {}
    if isinstance(value, Mapping):
        # read from config file
        data = value
    else:
        path = Path(str(value))
        if not path.exists():
            raise click.BadOptionUsage(
                "--conversions", f"Path does not exist: {value}", ctx
            )
        try:
            with path.open("r") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:
            raise click.BadOptionUsage(
                "--conversions", f"Error reading conversions file: {exc}", ctx
            )
    if not isinstance(value, Mapping):
        raise click.BadOptionUsage("--conversions", f"Not a mapping: {value!r}", ctx)
    return data


OPT_CONVERSIONS = click.option(
    "--conversions",
    "-c",
    default=None,
    callback=read_conversions,
    metavar="PATH",
    help="YAML file mapping directives -> conversions",
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
    is_flag=True,
    default=True,
    show_default=True,
    callback=check_sphinx,
    help="Load sphinx.",
)


def split_extension(ctx, param, value):
    if isinstance(value, list):
        # if reading from config
        return value
    return tuple(ext.strip() for ext in value.split(",")) if value else ()


OPT_EXTENSIONS = click.option(
    "--extensions",
    "-e",
    callback=split_extension,
    help="A comma-separated list of sphinx extensions to load.",
)

OPT_DEFAULT_DOMAIN = click.option(
    "--default-domain",
    "-dd",
    default="py",
    show_default=True,
    help="Default sphinx domain",
)
OPT_DEFAULT_ROLE = click.option(
    "--default-role",
    "-dr",
    default=None,
    help="Default sphinx role [default: convert to literal]",
)
OPT_CITE_PREFIX = click.option(
    "--cite-prefix",
    "-cp",
    default="cite",
    show_default=True,
    help="Prefix to add to citation references",
)
OPT_RAISE_ON_WARNING = click.option(
    "--raise-on-warning", "-W", is_flag=True, help="Raise exception on parsing warning"
)
OPT_CONSECUTIVE_NUMBERING = click.option(
    "--consecutive-numbering/--no-consecutive-numbering",
    default=True,
    show_default=True,
    help="Apply consecutive numbering to ordered lists",
)
OPT_COLON_FENCES = click.option(
    "--colon-fences/--no-colon-fences",
    default=True,
    show_default=True,
    help="Use colon fences for directives with parsed content",
)
OPT_DOLLAR_MATH = click.option(
    "--dollar-math/--no-dollar-math",
    default=True,
    show_default=True,
    help="Convert math (where possible) to dollar-delimited math",
)


@main.command("ast")
@ARG_STREAM
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_CONVERSIONS
@OPT_CONFIG
def ast(stream: TextIOWrapper, language: str, sphinx: bool, extensions, conversions):
    """Parse file / stdin (-) and print RST Abstract Syntax Tree."""
    text = stream.read()
    document, _ = to_docutils_ast(
        text,
        warning_stream=click.get_text_stream("stderr"),
        language_code=language,
        use_sphinx=sphinx,
        extensions=extensions,
        conversions=conversions,
    )
    output = document.pformat()
    click.echo(output)


@main.command("tokens")
@ARG_STREAM
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_DEFAULT_DOMAIN
@OPT_DEFAULT_ROLE
@OPT_CITE_PREFIX
@OPT_COLON_FENCES
@OPT_DOLLAR_MATH
@OPT_CONVERSIONS
@OPT_CONFIG
def tokens(
    stream: TextIOWrapper,
    language: str,
    sphinx: bool,
    extensions: List[str],
    default_domain: str,
    default_role: Optional[str],
    cite_prefix: str,
    colon_fences: bool,
    dollar_math: bool,
    conversions,
):
    """Parse file / stdin (-) and print Markdown-It tokens."""
    text = stream.read()
    output = rst_to_myst(
        text,
        warning_stream=click.get_text_stream("stderr"),
        language_code=language,
        use_sphinx=sphinx,
        extensions=extensions,
        conversions=conversions,
        default_domain=default_domain,
        default_role=default_role,
        cite_prefix=cite_prefix + "_",
        colon_fences=colon_fences,
        dollar_math=dollar_math,
    )
    click.echo(yaml_dump([token.as_dict() for token in output.tokens]))


@main.command("stream")
@ARG_STREAM
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_DEFAULT_DOMAIN
@OPT_DEFAULT_ROLE
@OPT_CITE_PREFIX
@OPT_CONSECUTIVE_NUMBERING
@OPT_COLON_FENCES
@OPT_DOLLAR_MATH
@OPT_CONVERSIONS
@OPT_CONFIG
def stream(
    stream: TextIOWrapper,
    language: str,
    sphinx: bool,
    extensions: List[str],
    default_domain: str,
    default_role: Optional[str],
    cite_prefix: str,
    consecutive_numbering: bool,
    colon_fences: bool,
    dollar_math: bool,
    conversions,
):
    """Parse file / stdin (-) and print Markdown text."""
    text = stream.read()
    output = rst_to_myst(
        text,
        warning_stream=click.get_text_stream("stderr"),
        language_code=language,
        use_sphinx=sphinx,
        extensions=extensions,
        conversions=conversions,
        default_domain=default_domain,
        default_role=default_role,
        cite_prefix=cite_prefix + "_",
        consecutive_numbering=consecutive_numbering,
        colon_fences=colon_fences,
        dollar_math=dollar_math,
    )
    click.echo(output.text)


@main.command("convert")
@ARG_PATHS
@click.option("--dry-run", "-d", is_flag=True, help="Do not write/remove any files")
@click.option("--replace-files", "-R", is_flag=True, help="Remove parsed files")
@click.option("--stop-on-fail", "-S", is_flag=True, help="Stop on first failure")
@OPT_RAISE_ON_WARNING
@OPT_LANGUAGE
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_DEFAULT_DOMAIN
@OPT_DEFAULT_ROLE
@OPT_CITE_PREFIX
@OPT_CONSECUTIVE_NUMBERING
@OPT_COLON_FENCES
@OPT_DOLLAR_MATH
@OPT_CONVERSIONS
@OPT_ENCODING
@OPT_CONFIG
def convert(
    paths: List[str],
    dry_run: bool,
    replace_files: bool,
    raise_on_warning: bool,
    stop_on_fail: bool,
    language: str,
    sphinx: bool,
    extensions: List[str],
    default_domain: str,
    default_role: Optional[str],
    cite_prefix: str,
    consecutive_numbering: bool,
    colon_fences: bool,
    dollar_math: bool,
    conversions,
    encoding: str,
):
    """Convert one or more files."""
    myst_extensions = set()
    for path in paths:
        path = Path(path)
        output_path = path.parent / (path.stem + ".md")
        click.secho(f"{path} -> {output_path}", fg="blue")
        input_text = path.read_text(encoding)
        try:
            output = rst_to_myst(
                input_text,
                warning_stream=click.get_text_stream("stderr"),
                raise_on_warning=raise_on_warning,
                language_code=language,
                use_sphinx=sphinx,
                extensions=extensions,
                conversions=conversions,
                default_domain=default_domain,
                default_role=default_role,
                cite_prefix=cite_prefix + "_",
                consecutive_numbering=consecutive_numbering,
                colon_fences=colon_fences,
                dollar_math=dollar_math,
            )
        except Exception as exc:
            click.secho(f"FAILED:\n{exc}", fg="red")
            if stop_on_fail:
                raise SystemExit(1)
            continue

        click.secho(f"CONVERTED (extensions: {list(output.extensions)!r})", fg="green")
        myst_extensions.update(output.extensions)
        if dry_run:
            continue
        output_path.write_text(output.text, encoding=encoding)
        if replace_files and output_path != path:
            path.unlink()
    click.echo("")
    click.secho(f"FINISHED ALL! (extensions: {list(myst_extensions)!r})", fg="green")


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
    """Show information about a single role."""
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
    """List available roles."""
    namespace = compile_namespace(extensions=extensions, use_sphinx=sphinx)
    click.echo(" ".join(namespace.list_roles()))


@roles.command("show")
@click.argument("name")
@OPT_SPHINX
@OPT_EXTENSIONS
@OPT_LANGUAGE
def roles_show(name, sphinx, extensions, language):
    """Show information about a single role."""
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
