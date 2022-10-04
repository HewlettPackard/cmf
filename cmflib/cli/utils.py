import yaml


def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"


def read_cmf_config():
    with open("../../cmfconfig/config.yaml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        print("Read Successful")
    return data
