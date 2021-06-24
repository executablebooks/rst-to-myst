from pathlib import Path

import pytest

from rst_to_myst import rst_to_myst

TEXTS_PATH = Path(__file__).parent.joinpath("texts")


@pytest.mark.parametrize(
    "path",
    list(TEXTS_PATH.glob("*.rst")),
    ids=[path.name[:-4] for path in TEXTS_PATH.glob("*.rst")],
)
def test_texts(path: Path, file_regression):
    text = path.read_text()
    output = rst_to_myst(text)
    warnings = output.warning_stream.getvalue().splitlines()
    # ignore known inline target warnings
    assert not [
        line for line in warnings if "inline targets not implemented" not in line
    ], warnings
    file_regression.check(output.text, extension=".md")
