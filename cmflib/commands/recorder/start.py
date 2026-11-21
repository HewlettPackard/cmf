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

import argparse
import logging
import os
import signal
import time

from cmflib.cli.command import CmdBase
from cmflib.cmf_exception_handling import MsgSuccess
from cmflib.agent_recorder.config import load_config
from cmflib.agent_recorder.spool_reader import SpoolReader
from cmflib.agent_recorder.trace_writer import TraceWriter

logger = logging.getLogger(__name__)


class CmdRecorderStart(CmdBase):
    """Starts the agent-recorder: a long-running process that tails the
    spool directory for new trace-event lines and feeds each one to the
    TraceWriter in order.

    Run this from inside a git repo that has already had
    ``cmf init local|minioS3|...`` run in it -- cmflib does real DVC + git
    commits when it logs an artifact, so it needs that context to exist first.

    No config file required -- the recorder reads .cmfconfig (written by
    ``cmf init``) to determine whether to push to a CMF server after every
    turn. Use environment variables to override defaults.
    """

    def run(self, live):
        # Suppress DVC/tqdm progress bars that flood the recorder's output.
        os.environ["TQDM_DISABLE"] = "1"
        config = load_config()

        # CLI flags override environment variables.
        if self.args.spool_dir:
            config.spool_dir = self.args.spool_dir
        if self.args.runs_dir:
            config.cmf.runs_dir = self.args.runs_dir
        if self.args.mlmd_path:
            config.cmf.mlmd_path = self.args.mlmd_path
        if self.args.poll_interval is not None:
            config.poll_interval_seconds = self.args.poll_interval

        logging.basicConfig(
            level=logging.DEBUG if self.args.verbose else logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )

        reader = SpoolReader(config.spool_dir)
        writer = TraceWriter(config)

        running = True

        def _stop(signum, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        logger.info("watching %s (mlmd=%s)", config.spool_dir, config.cmf.mlmd_path)

        while running:
            for session_id, event in reader.poll():
                try:
                    writer.handle(session_id, event)
                except Exception:
                    logger.error("error handling event for session %s", session_id, exc_info=True)
            if self.args.once:
                break
            time.sleep(config.poll_interval_seconds)

        return MsgSuccess(msg_str=f"Recorder stopped. Processed spool at {config.spool_dir}")


def add_parser(subparsers, parent_parser):
    HELP = "Start the agent-recorder to tail the spool and record agent turns into CMF."

    parser = subparsers.add_parser(
        "start",
        parents=[parent_parser],
        description=(
            "Starts a long-running process that tails the spool directory for "
            "trace-event JSONL files (produced by opencode-capture or any "
            "compatible producer) and records each agent turn into the user's "
            "mlmd as Dataset artifacts under an AgentTurn stage.\n\n"
            "Run this from inside a git repo that has already had "
            "`cmf init local|minioS3|...` run in it.\n\n"
            "Environment variables:\n"
            "  CMF_AGENT_SPOOL_DIR      Spool directory (default: ./spool)\n"
            "  CMF_AGENT_RUNS_DIR       Per-turn trace file staging (default: ./cmf-runs)\n"
            "  CMF_AGENT_MLMD_PATH      Path to mlmd file (default: mlmd)\n"
            "  CMF_AGENT_POLL_INTERVAL  Poll cadence in seconds (default: 1.0)\n"
            "  CMF_AGENT_SERVER_URL     CMF server URL for push (default: from .cmfconfig)"
        ),
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--spool-dir",
        default=None,
        help="Spool directory containing <session_id>.jsonl files (overrides CMF_AGENT_SPOOL_DIR)",
        metavar="<path>",
    )
    parser.add_argument(
        "--runs-dir",
        default=None,
        help="Directory for staging per-turn trace files (overrides CMF_AGENT_RUNS_DIR)",
        metavar="<path>",
    )
    parser.add_argument(
        "--mlmd-path",
        default=None,
        help="Path to the mlmd metadata file (overrides CMF_AGENT_MLMD_PATH)",
        metavar="<path>",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="Poll interval in seconds (overrides CMF_AGENT_POLL_INTERVAL)",
        metavar="<seconds>",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process everything currently in the spool, then exit (for testing)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.set_defaults(func=CmdRecorderStart)
