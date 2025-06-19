###
# Copyright (2025) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###
from rich.live import Live               # To manage live-updating output
from rich.console import Console         # For rendering to the terminal
from rich.spinner import Spinner         # Provides a ready-made spinner widget
from cmflib.cmf_exception_handling import CmfResponse
import sys

# Reconfigure the standard output stream to use UTF-8 encoding.
# This ensures that printing Unicode characters (such as emojis or special symbols)
# will not cause encoding errors, regardless of the system's default encoding.
sys.stdout.reconfigure(encoding='utf-8')

console = Console() # Create a console object
spinner = Spinner("dots", text="Loading...") # Create a spinner object

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
        try:
            # Use the Live context manager to manage the spinner 
            with Live(spinner, refresh_per_second=10, console=console, transient=True) as live:
                msg = cmd.do_run(live)
                print(msg.handle())
        except CmfResponse as e:  
            print(e.handle())
    except CmfParserError:
        pass    
    except KeyboardInterrupt:
        print("Interrupted by the user")
    except Exception as e:
        print(e)
   