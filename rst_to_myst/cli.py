from io import TextIOWrapper

import click

from . import convert, to_ast


@click.command()
@click.option(
    "--file",
    "-f",
    type=click.File("r"),
    default="-",
    help="Input file (defaults to stdin)",
)
@click.option(
    "--ast", "-a", is_flag=True, help="Output the AST instead of rendered text"
)
def main(file: TextIOWrapper, ast: bool):
    """Convert ReStructuredText to MyST Markdown"""
    text = file.read()
    if ast:
        document, _ = to_ast(text, warning_stream=click.get_text_stream("stderr"))
        output = document.pformat()
    else:
        output, _ = convert(text, click.get_text_stream("stderr"))
    click.echo(output)


if __name__ == "__main__":
    main()
