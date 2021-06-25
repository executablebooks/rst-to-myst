from pathlib import Path

import yaml


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


def represent_str(dumper, data):
    # borrowed from http://stackoverflow.com/a/33300001
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


class YamlDumper(yaml.SafeDumper):
    pass


YamlDumper.add_representer(str, represent_str)


def yaml_dump(data, sort_keys: bool = True):
    return yaml.dump(data, Dumper=YamlDumper, sort_keys=sort_keys)
