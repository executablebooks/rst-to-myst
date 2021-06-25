"""Configuration for Sphinx documentation build.

It is recommended to use tox to run the build (see tox.ini):
`tox -e docs-clean` and `tox -e docs-update`,
or directly: `sphinx-build -n -W --keep-going docs/source docs/_build`
"""
from rst_to_myst import __version__

project = "RST-to-MyST"
copyright = "2021, Executable Book Project"  # noqa: A001
author = "Executable Book Project"
version = __version__

extensions = [
    # read Markdown files
    "myst_parser",
    "sphinx_panels",
    # document CLI
    "sphinx_click",
    # document API
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

html_theme = "sphinx_book_theme"
html_title = f"RST-to-MyST: v{__version__}"
html_theme_options = {
    "home_page_in_toc": True,
    "github_url": "https://github.com/executablebooks/rst-to-myst",
    "repository_url": "https://github.com/executablebooks/rst-to-myst",
    "use_issues_button": True,
    "use_repository_button": True,
    "repository_branch": "main",
    "path_to_docs": "docs",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.8", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "markdown_it": ("https://markdown-it-py.readthedocs.io/en/latest", None),
}

nitpick_ignore = [
    ("py:class", name) for name in ["IO", "_io.StringIO", "docutils.nodes.document"]
]
