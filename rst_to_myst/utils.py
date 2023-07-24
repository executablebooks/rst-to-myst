import yaml


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
