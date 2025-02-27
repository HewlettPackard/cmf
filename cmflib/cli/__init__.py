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
from cmflib.cmf_exception_handling import CmfResponse
from cmflib.cli.progress_bar import ProgressBar    

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
    pbar = ProgressBar()
    pbar.start_progress_bar()
    try:
        args = parse_args(argv)
        cmd = args.func(args)
        msg = cmd.do_run(pbar)
        pbar.stop_progress_bar()
        print(msg.handle())
    except CmfResponse as e:
        pbar.stop_progress_bar()
        print(e.handle())
    except CmfParserError:
        pbar.stop_progress_bar()
        pass    
    except KeyboardInterrupt:
        pbar.stop_progress_bar()
        print("Interrupted by the user")
    except Exception as e:
        pbar.stop_progress_bar()
        print(e)
   