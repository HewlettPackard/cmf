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

"""Tails the spool directory: one append-only JSONL file per session.

The reader is deliberately dumb -- no filesystem watch API, just a poll loop
that re-lists the directory and reads any new bytes since the last offset.
That keeps it portable (works identically on any OS/filesystem) and robust
to the recorder process restarting: offsets are persisted to
``<spool_dir>/.offsets.json`` so a restart resumes instead of re-processing
events that were already recorded.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterator, Tuple

logger = logging.getLogger(__name__)

OFFSETS_FILENAME = ".offsets.json"


class SpoolReader:
    def __init__(self, spool_dir: str):
        self.spool_dir = Path(spool_dir)
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        self._offsets_path = self.spool_dir / OFFSETS_FILENAME
        self._offsets: Dict[str, int] = self._load_offsets()

    def _load_offsets(self) -> Dict[str, int]:
        if self._offsets_path.exists():
            try:
                return json.loads(self._offsets_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("could not read %s, starting from scratch", self._offsets_path)
        return {}

    def _save_offsets(self) -> None:
        self._offsets_path.write_text(json.dumps(self._offsets))

    def poll(self) -> Iterator[Tuple[str, dict]]:
        """Yield ``(session_id, event_dict)`` for every new complete line
        appended to any ``<session_id>.jsonl`` file since the last ``poll()``.

        A trailing line with no final newline (the adapter is mid-write) is
        left for the next poll rather than parsed -- this is what keeps the
        reader safe against tailing a file another process is actively
        appending to.
        """
        for path in sorted(self.spool_dir.glob("*.jsonl")):
            session_id = path.stem
            start_offset = self._offsets.get(session_id, 0)

            with path.open("r", encoding="utf-8") as f:
                f.seek(start_offset)
                chunk = f.read()

            if not chunk:
                continue

            complete_part, _, incomplete_tail = chunk.rpartition("\n")
            if not complete_part:
                # No full line yet; wait for more data.
                continue

            consumed_bytes = len(complete_part.encode("utf-8")) + 1  # + the newline
            for line in complete_part.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("skipping malformed line in %s: %r", path, line)
                    continue
                yield session_id, event

            self._offsets[session_id] = start_offset + consumed_bytes

        self._save_offsets()
