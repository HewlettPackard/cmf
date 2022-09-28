import sys


class CmfParserError(Exception):
    """Base class for CLI parser errors."""

    def __init__(self):
        super().__init__("parser error")


def parse_args(argv=None):
    """Parses CLI arguments

    Args:
        argv: optional list of arguments to parse. sys.argv is used by default.

    Raises:
        CmfParserError: raised for argument parsing errors

    """
    from .parser import get_main_parser

    parser = get_main_parser()
    args = parser.parse_args(argv)
    args.parser = parser
    return args


def main(argv=None):
    """Main entry point for cmf CLI.

    Args:
        argv: argv: optional list of arguments to parse. sys.argv is used by default.

    Returns:
        int, string: command's return code and error
    """
    args = None
    try:
        args = parse_args(argv)
        cmd = args.func(args)
        msg = cmd.do_run()
        print(msg)
    except CmfParserError:
        print("Error while parsing arguments")
    except KeyboardInterrupt:
        print("Interrupted by the user")
    except Exception as e:
        print("Unknown Exception")
