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

"""Turns trace events into CMF pipelines/contexts/executions/artifacts.

Mapping (see DESIGN.md):

  pipeline_name -> the user's pipeline (e.g. "autoresearch")
  context       -> one ``AgentTurn`` stage within the user's pipeline
  execution     -> one per turn
  artifacts     -> reasoning.jsonl / tool-calls.jsonl / transcript.jsonl
                   per turn, with turn N's transcript logged as an input of
                   turn N+1's execution to thread the lineage DAG across the
                   session.

This module assumes the process's current working directory is a git repo
that has already been through ``cmf init local|...`` (see README.md). CMF's
cmflib does real DVC + git operations under the hood when you log an
artifact, so this is not optional set-up.

The recorder runs as a **separate process** from the user's code. It creates
its own ``Cmf`` instance pointing at the same mlmd file. There is no cursor
clobbering or write contention because:

  1. The user's code (e.g. train.py) runs during the turn and exits before
     ``turn_end`` arrives in the spool.
  2. The recorder processes ``turn_end`` after the user's code has exited,
     so the recorder is the only writer to mlmd at that moment.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from .config import RecorderConfig

logger = logging.getLogger(__name__)

# The stage name used for all agent-turn executions within the user's pipeline.
AGENT_TURN_STAGE = "AgentTurn"

# The four part types we accept, and which derived file each goes into.
# "transcript.jsonl" gets every part regardless of type.
_PART_TYPE_FILES = {
    "reasoning": "reasoning.jsonl",
    "tool": "tool-calls.jsonl",
}


class TurnBuffer:
    """Accumulates ``part`` events for one open turn and keeps the three
    derived trace files on disk up to date after every single part event
    (not just at turn_end) -- this is what preserves a mid-turn crash's
    partial trace, and what keeps an abandoned tool call's last status
    (e.g. "error") visible instead of silently disappearing.
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        # part_id -> latest event for that part. A dict because a part can
        # be reported multiple times (pending -> running -> completed); we
        # only ever keep the most recent status, per the schema doc.
        self.parts: Dict[str, dict] = {}

    def apply(self, event: dict) -> None:
        self.parts[event["part_id"]] = event
        self._flush()

    def _ordered_parts(self):
        return sorted(self.parts.values(), key=lambda p: p["seq"])

    def _flush(self) -> None:
        ordered = self._ordered_parts()
        self._write_jsonl(self.run_dir / "transcript.jsonl", ordered)
        for part_type, filename in _PART_TYPE_FILES.items():
            subset = [p for p in ordered if p["part_type"] == part_type]
            self._write_jsonl(self.run_dir / filename, subset)

    @staticmethod
    def _write_jsonl(path: Path, events: list) -> None:
        with path.open("w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

    def metrics(self) -> dict:
        parts = list(self.parts.values())
        by_status: Dict[str, int] = {}
        for p in parts:
            by_status[p["status"]] = by_status.get(p["status"], 0) + 1
        return {
            "part_count": len(parts),
            "reasoning_count": sum(1 for p in parts if p["part_type"] == "reasoning"),
            "tool_count": sum(1 for p in parts if p["part_type"] == "tool"),
            "text_count": sum(1 for p in parts if p["part_type"] == "text"),
            "file_count": sum(1 for p in parts if p["part_type"] == "file"),
            **{f"status_{status}_count": count for status, count in by_status.items()},
        }


@dataclasses.dataclass
class SessionState:
    session_id: str
    pipeline_name: str
    cmf: Cmf
    run_root: Path
    prev_turn_transcript: Optional[str] = None
    current_turn: Optional[TurnBuffer] = None
    current_turn_meta: Optional[dict] = None


def _parse_iso_ts(ts: str) -> Optional[int]:
    """Parse an ISO-8601 timestamp string to milliseconds since epoch.

    Returns None if parsing fails (correlation will be skipped).
    """
    try:
        # Python 3.11+: datetime.fromisoformat handles 'Z' suffix.
        # For 3.9/3.10, replace trailing 'Z' with '+00:00'.
        ts_clean = ts.rstrip("Z")
        if ts.endswith("Z"):
            ts_clean = ts_clean + "+00:00"
        dt = datetime.fromisoformat(ts_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        logger.debug("could not parse timestamp %r", ts)
        return None


class TraceWriter:
    """Consumes trace events (already split by session by the caller's poll
    loop) and drives cmflib. One instance per recorder process; internally
    keeps one ``SessionState`` per active session_id so it can interleave
    events from multiple concurrent sessions safely (all cmflib calls happen
    on this single thread, so there is no write contention on the local
    mlmd/DVC store even with many sessions in flight).
    """

    def __init__(self, config: RecorderConfig):
        self.config = config
        self.sessions: Dict[str, SessionState] = {}

    def handle(self, session_id: str, event: dict) -> None:
        handler = getattr(self, f"_on_{event['type']}", None)
        if handler is None:
            logger.warning("unknown event type %r for session %s", event.get("type"), session_id)
            return
        handler(session_id, event)

    # -- event handlers ----------------------------------------------------

    def _on_session_start(self, session_id: str, event: dict) -> None:
        from cmflib.cmf import Cmf
        pipeline_name = event["pipeline_name"]
        cmf = Cmf(filepath=self.config.cmf.mlmd_path, pipeline_name=pipeline_name)
        # Create the AgentTurn stage once per session. cmflib's
        # create_context() does a get-or-create keyed on
        # "<pipeline_name>/<pipeline_stage>", so calling this again for a
        # second session in the same pipeline will reuse the same context.
        # That's fine: session_id is a custom property on each execution,
        # not on the context.
        cmf.create_context(
            pipeline_stage=AGENT_TURN_STAGE,
            custom_properties={
                "session_id": session_id,
                "source": event.get("source", "unknown"),
                "parent_session_id": event.get("parent_session_id") or "",
                "fork_point_message_id": event.get("fork_point_message_id") or "",
            },
        )
        run_root = Path(self.config.cmf.runs_dir) / pipeline_name / session_id
        self.sessions[session_id] = SessionState(
            session_id=session_id,
            pipeline_name=pipeline_name,
            cmf=cmf,
            run_root=run_root,
        )
        logger.info("session_start %s (pipeline=%s)", session_id, pipeline_name)

    def _on_turn_start(self, session_id: str, event: dict) -> None:
        session = self.sessions[session_id]
        # If the previous turn was never closed (no turn_end arrived),
        # auto-close it now so its artifacts aren't lost. This happens when
        # the capture adapter opens a new turn before the previous one's
        # assistant message completed.
        if session.current_turn is not None:
            logger.warning(
                "turn_start for %s but previous turn %s still open, auto-closing",
                session_id, session.current_turn_meta.get("turn_id") if session.current_turn_meta else "?",
            )
            self._close_turn(session_id, {
                "type": "turn_end",
                "session_id": session_id,
                "turn_id": session.current_turn_meta.get("turn_id", "") if session.current_turn_meta else "",
                "status": "aborted",
                "ts": event.get("ts", ""),
            })
        turn_id = event["turn_id"]
        session.cmf.create_execution(
            execution_type="AgentTurn",
            custom_properties={
                "turn_id": turn_id,
                "turn_index": event["turn_index"],
                "role": event["role"],
                "session_id": session_id,
                "turn_start_ts": event.get("ts", ""),
            },
            # Without an explicit cmd, cmflib records this *recorder*
            # process's own argv as the execution's "command" -- which
            # describes the wrong thing. Record what actually ran instead.
            cmd=f"session={session_id} turn={turn_id} turn_index={event['turn_index']}",
        )
        if session.prev_turn_transcript:
            session.cmf.log_dataset(url=session.prev_turn_transcript, event="input")
        session.current_turn = TurnBuffer(session.run_root / turn_id)
        session.current_turn_meta = event
        logger.info("turn_start %s / %s (index=%s)", session_id, turn_id, event["turn_index"])

    def _on_part(self, session_id: str, event: dict) -> None:
        session = self.sessions[session_id]
        if session.current_turn is None:
            logger.warning("part event for %s with no open turn, dropping: %r", session_id, event)
            return
        session.current_turn.apply(event)

    def _on_turn_end(self, session_id: str, event: dict) -> None:
        session = self.sessions[session_id]
        if session.current_turn is None:
            logger.warning("turn_end for %s with no open turn, ignoring", session_id)
            return
        self._close_turn(session_id, event)

    def _close_turn(self, session_id: str, event: dict) -> None:
        """Shared turn-closing logic used by _on_turn_end and the auto-close
        path in _on_turn_start. Logs the three trace files as outputs,
        records metrics, finalizes the execution, and threads the transcript
        path to the next turn as an input.
        """
        session = self.sessions[session_id]
        turn = session.current_turn
        if turn is None:
            return

        turn._flush()
        transcript_path = str(turn.run_dir / "transcript.jsonl")
        reasoning_path = str(turn.run_dir / "reasoning.jsonl")
        tool_calls_path = str(turn.run_dir / "tool-calls.jsonl")

        common_props = {
            "turn_id": event["turn_id"],
            "status": event["status"],
            "session_id": session_id,
        }

        # Try to correlate this agent turn with the user's ML execution
        # (e.g. train.py) that ran during this turn. The ML execution was
        # created during the turn and is already in the mlmd by now.
        correlated_exec_id = self._correlate_ml_execution(
            session, session.current_turn_meta, event
        )
        if correlated_exec_id is not None:
            common_props["correlated_ml_exec_id"] = str(correlated_exec_id)

        session.cmf.log_dataset(url=transcript_path, event="output", custom_properties=common_props)
        session.cmf.log_dataset(url=reasoning_path, event="output", custom_properties=common_props)
        session.cmf.log_dataset(url=tool_calls_path, event="output", custom_properties=common_props)
        session.cmf.log_execution_metrics(metrics_name="turn_metrics", custom_properties=turn.metrics())
        session.cmf.finalize()

        session.prev_turn_transcript = transcript_path
        session.current_turn = None
        session.current_turn_meta = None
        logger.info("turn_end %s / %s (status=%s)", session_id, event["turn_id"], event["status"])

        if self.config.cmf.server_url:
            self._push(session.pipeline_name)

    def _on_session_end(self, session_id: str, event: dict) -> None:
        if self.config.cmf.server_url:
            session = self.sessions.get(session_id)
            if session:
                self._push(session.pipeline_name)
        self.sessions.pop(session_id, None)
        logger.info("session_end %s (status=%s)", session_id, event["status"])

    # -- correlation -------------------------------------------------------

    def _correlate_ml_execution(
        self, session: SessionState, turn_start_event: Optional[dict], turn_end_event: dict
    ) -> Optional[int]:
        """Find the user's ML execution whose ``create_time_since_epoch``
        falls within the turn's ``[turn_start_ts, turn_end_ts]`` time window.

        Returns the execution ID, or None if no match is found or the
        pipeline doesn't exist yet (e.g. the recorder started before any
        user code has run).

        This runs at turn_end time, before the recorder has created its own
        AgentTurn execution for this turn, so the query sees only the
        user's executions (e.g. train.py's).
        """
        turn_start_ts = turn_start_event.get("ts") if turn_start_event else None
        turn_end_ts = turn_end_event.get("ts")
        if not turn_end_ts:
            return None

        start_ms = _parse_iso_ts(turn_start_ts) if turn_start_ts else None
        end_ms = _parse_iso_ts(turn_end_ts)
        if end_ms is None:
            return None
        if start_ms is None:
            # If we don't have a start ts, use a generous window (1 hour
            # before the turn end) to avoid missing long-running turns.
            start_ms = end_ms - 3600_000

        try:
            from cmflib.cmfquery import CmfQuery
            query = CmfQuery(self.config.cmf.mlmd_path)
            pipeline_id = query.get_pipeline_id(session.pipeline_name)
            for stage in query._get_stages(pipeline_id):
                # Skip our own AgentTurn stage to avoid correlating with
                # a previous turn's agent execution.
                if AGENT_TURN_STAGE in stage.name:
                    continue
                for execution in query._get_executions(stage.id):
                    exec_ms = execution.create_time_since_epoch
                    if start_ms <= exec_ms <= end_ms:
                        return execution.id
        except Exception:
            logger.debug(
                "correlation query failed for pipeline %s", session.pipeline_name,
                exc_info=True,
            )
        return None

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _push(pipeline_name: str) -> None:
        """Push metadata + artifacts to the configured CMF server. Run right
        after every turn's finalize() so a server, if configured, stays close
        to real time rather than only syncing at session end. cmf only
        transfers deltas, so pushing every turn is cheap.

        ``cmf metadata push`` exits 0 even when the underlying HTTP request
        to the server fails (e.g. connection refused) -- it prints the error
        and moves on rather than surfacing a nonzero exit code. So a clean
        exit code alone doesn't mean the push worked; the combined output is
        also scanned for the failure marker cmf/requests actually emit.
        """
        for args in (["cmf", "artifact", "push", "-p", pipeline_name],
                     ["cmf", "metadata", "push", "-p", pipeline_name]):
            result = subprocess.run(args, capture_output=True, text=True)
            output = result.stdout + result.stderr
            if result.returncode != 0 or "ConnectionError" in output or "Traceback" in output:
                logger.warning("%s did not fully succeed: %s", " ".join(args), output.strip()[-500:])
