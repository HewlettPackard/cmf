import sys


class CmfParserError(Exception):
    """Base class for CLI parser errors."""

    def __init__(self):
        super().__init__("parser error")


def parse_args(argv=None):
    from .parser import get_main_parser

    parser = get_main_parser()
    args = parser.parse_args(argv)
    args.parser = parser
    return args


def main(argv=None):
    args = None
    args = parse_args(argv)
    cmd = args.func(args)
    msg = cmd.do_run()
    print(msg)
