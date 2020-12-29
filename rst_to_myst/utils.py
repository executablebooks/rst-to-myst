from pathlib import Path


def read_fixture_file(path):
    text = Path(path).read_text(encoding="utf-8")
    tests = []
    section = 0
    last_pos = 0
    lines = text.splitlines(keepends=True)
    for i in range(len(lines)):
        if lines[i].rstrip() == ".":
            if section == 0:
                tests.append([i, lines[i - 1].strip()])
                section = 1
            elif section == 1:
                tests[-1].append("".join(lines[last_pos + 1 : i]))
                section = 2
            elif section == 2:
                tests[-1].append("".join(lines[last_pos + 1 : i]))
                section = 0

            last_pos = i
    return tests


def list_directives_docutils():
    # see also https://docutils.sourceforge.io/docs/ref/rst/directives.html
    from docutils.parsers.rst.directives import _directive_registry

    return [
        f"docutils.parsers.rst.directives.{mod}.{klass}"
        for mod, klass in _directive_registry.values()
    ]


if __name__ == "__main__":
    print("\n".join(sorted(f"{t}: eval_rst" for t in list_directives_docutils())))
