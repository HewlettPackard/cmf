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

"""Loads recorder configuration from environment variables and ``.cmfconfig``.

No config file is required -- every field has a sane default, and the CMF
server URL (the one field that matters for push behavior) is read directly
from ``.cmfconfig`` (written by ``cmf init``) if not set via environment.
This avoids requiring the user to keep a second copy of the server URL in
sync.
"""

from __future__ import annotations

import configparser
import dataclasses
import os
from typing import Optional


@dataclasses.dataclass
class CmfConfig:
    # If set, the recorder pushes metadata + artifacts to this CMF server
    # after every turn. If None, CMF stays local-only (cmf init's default).
    # Populated from .cmfconfig if not set via environment -- see load_config().
    server_url: Optional[str] = None
    # Where trace_writer.py stages per-turn trace files (reasoning.jsonl,
    # tool-calls.jsonl, transcript.jsonl) before handing them to cmflib.
    runs_dir: str = "./cmf-runs"
    # Path to the mlmd metadata file, passed straight through to
    # cmflib.cmf.Cmf(filepath=...).
    mlmd_path: str = "mlmd"


@dataclasses.dataclass
class RecorderConfig:
    spool_dir: str = "./spool"
    poll_interval_seconds: float = 1.0
    cmf: CmfConfig = dataclasses.field(default_factory=CmfConfig)


def _read_cmfconfig_server_url(cmfconfig_path: str = ".cmfconfig") -> Optional[str]:
    """Read the server-url field from .cmfconfig (written by ``cmf init``).

    Returns None if .cmfconfig doesn't exist or has no server-url set
    (i.e. local-only CMF).
    """
    parser = configparser.ConfigParser()
    read_files = parser.read(cmfconfig_path)
    if not read_files:
        return None
    return parser.get("cmf", "server-url", fallback=None)


def load_config() -> RecorderConfig:
    """Load a RecorderConfig from environment variables, falling back to
    built-in defaults. After loading, if ``cmf.server_url`` is still None,
    it is read from ``.cmfconfig`` (written by ``cmf init``) so the recorder
    can decide whether to push after every turn without requiring the user
    to duplicate the server URL in an environment variable.
    """
    cmf_config = CmfConfig(
        server_url=os.getenv("CMF_AGENT_SERVER_URL"),
        runs_dir=os.getenv("CMF_AGENT_RUNS_DIR", CmfConfig.runs_dir),
        mlmd_path=os.getenv("CMF_AGENT_MLMD_PATH", CmfConfig.mlmd_path),
    )
    config = RecorderConfig(
        spool_dir=os.getenv("CMF_AGENT_SPOOL_DIR", RecorderConfig.spool_dir),
        poll_interval_seconds=float(
            os.getenv("CMF_AGENT_POLL_INTERVAL", str(RecorderConfig.poll_interval_seconds))
        ),
        cmf=cmf_config,
    )

    # If the environment didn't set cmf.server_url, read it from .cmfconfig
    # (written by `cmf init`). This is the only field that .cmfconfig
    # carries that the recorder cares about -- the push-after-every-turn
    # switch. cmflib's own push commands read the server URL from
    # .cmfconfig at push time regardless, so this just needs to know
    # WHETHER to push, not where.
    if config.cmf.server_url is None:
        config.cmf.server_url = _read_cmfconfig_server_url()

    return config
