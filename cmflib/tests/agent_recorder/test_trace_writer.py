"""Unit tests for TraceWriter -- uses a mock Cmf to verify the event
dispatch, turn-to-turn lineage, and per-turn artifact logging without
requiring a real mlmd/DVC/git environment.

Run with: python3 -m pytest cmflib/tests/agent_recorder/test_trace_writer.py
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# cmflib.cmf has heavy dependencies (pandas, ml_metadata, etc.) that may not
# be installed in the test environment. Insert a stub so the lazy import in
# trace_writer._on_session_start can be controlled.
_cmf_stub = MagicMock()
if "cmflib.cmf" not in sys.modules:
    sys.modules["cmflib.cmf"] = _cmf_stub

from cmflib.agent_recorder.config import RecorderConfig, CmfConfig
from cmflib.agent_recorder.trace_writer import TraceWriter, TurnBuffer, AGENT_TURN_STAGE


def load_fixture(name: str) -> list:
    """Load a fixture JSONL file and return a list of event dicts."""
    fixture_path = Path(__file__).parent / "fixtures" / f"{name}.jsonl"
    events = []
    with fixture_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


class TurnBufferTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.tmp.name) / "turn_1"

    def tearDown(self):
        self.tmp.cleanup()

    def test_apply_and_flush_writes_three_files(self):
        buf = TurnBuffer(self.run_dir)
        buf.apply({
            "type": "part", "session_id": "s1", "turn_id": "t1",
            "part_id": "p1", "part_type": "reasoning", "status": "completed",
            "seq": 0, "content": {"text": "thinking"}, "ts": "2026-01-01T00:00:00Z",
        })
        buf.apply({
            "type": "part", "session_id": "s1", "turn_id": "t1",
            "part_id": "p2", "part_type": "tool", "status": "completed",
            "seq": 1, "content": {"tool": "bash", "input": {}, "output": "ok"},
            "ts": "2026-01-01T00:00:01Z",
        })
        buf.apply({
            "type": "part", "session_id": "s1", "turn_id": "t1",
            "part_id": "p3", "part_type": "text", "status": "completed",
            "seq": 2, "content": {"text": "done"}, "ts": "2026-01-01T00:00:02Z",
        })

        self.assertTrue((self.run_dir / "transcript.jsonl").exists())
        self.assertTrue((self.run_dir / "reasoning.jsonl").exists())
        self.assertTrue((self.run_dir / "tool-calls.jsonl").exists())

        transcript = (self.run_dir / "transcript.jsonl").read_text().strip().split("\n")
        self.assertEqual(len(transcript), 3)

        reasoning = (self.run_dir / "reasoning.jsonl").read_text().strip().split("\n")
        self.assertEqual(len(reasoning), 1)
        self.assertEqual(json.loads(reasoning[0])["part_type"], "reasoning")

        tool_calls = (self.run_dir / "tool-calls.jsonl").read_text().strip().split("\n")
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(json.loads(tool_calls[0])["part_type"], "tool")

    def test_latest_status_overwrites_previous(self):
        buf = TurnBuffer(self.run_dir)
        # Same part_id, status transitions pending -> running -> error
        for status in ("pending", "running", "error"):
            buf.apply({
                "type": "part", "session_id": "s1", "turn_id": "t1",
                "part_id": "p1", "part_type": "tool", "status": status,
                "seq": 0, "content": {"tool": "bash", "input": {}}, "ts": "2026-01-01T00:00:00Z",
            })
        self.assertEqual(len(buf.parts), 1)
        self.assertEqual(buf.parts["p1"]["status"], "error")

        transcript = (self.run_dir / "transcript.jsonl").read_text().strip().split("\n")
        self.assertEqual(len(transcript), 1)
        self.assertEqual(json.loads(transcript[0])["status"], "error")

    def test_metrics(self):
        buf = TurnBuffer(self.run_dir)
        buf.apply({
            "type": "part", "part_id": "p1", "part_type": "reasoning", "status": "completed",
            "seq": 0, "content": {}, "session_id": "s", "turn_id": "t", "ts": "",
        })
        buf.apply({
            "type": "part", "part_id": "p2", "part_type": "tool", "status": "error",
            "seq": 1, "content": {}, "session_id": "s", "turn_id": "t", "ts": "",
        })
        m = buf.metrics()
        self.assertEqual(m["part_count"], 2)
        self.assertEqual(m["reasoning_count"], 1)
        self.assertEqual(m["tool_count"], 1)
        self.assertEqual(m["status_completed_count"], 1)
        self.assertEqual(m["status_error_count"], 1)


class TraceWriterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.tmp.name) / "runs"
        self.config = RecorderConfig(
            spool_dir=str(Path(self.tmp.name) / "spool"),
            cmf=CmfConfig(
                runs_dir=str(self.runs_dir),
                mlmd_path=str(Path(self.tmp.name) / "mlmd"),
            ),
        )
        # Set up a fresh mock Cmf on the stub module for each test.
        self.mock_cmf = MagicMock()
        _cmf_stub.Cmf = MagicMock(return_value=self.mock_cmf)

    def tearDown(self):
        self.tmp.cleanup()

    def test_session_start_creates_cmf_and_context(self):
        writer = TraceWriter(self.config)

        writer.handle("ses_1", {
            "type": "session_start", "session_id": "ses_1",
            "source": "opencode", "pipeline_name": "test_pipeline",
            "parent_session_id": None, "fork_point_message_id": None,
            "ts": "2026-01-01T00:00:00Z",
        })

        _cmf_stub.Cmf.assert_called_once_with(
            filepath=self.config.cmf.mlmd_path, pipeline_name="test_pipeline"
        )
        self.mock_cmf.create_context.assert_called_once()
        args, kwargs = self.mock_cmf.create_context.call_args
        stage_name = args[0] if args else kwargs.get("pipeline_stage")
        self.assertEqual(stage_name, AGENT_TURN_STAGE)
        self.assertIn("ses_1", writer.sessions)

    def test_full_turn_logs_artifacts_and_lineage(self):
        """Feed a complete turn from the basic fixture and verify:
        - create_execution called with AgentTurn type
        - log_dataset called for transcript/reasoning/tool-calls as outputs
        - finalize called
        """
        writer = TraceWriter(self.config)
        events = load_fixture("session-basic")

        for event in events:
            writer.handle(events[0]["session_id"], event)

        # First event is session_start -> creates Cmf + context
        self.mock_cmf.create_context.assert_called_once()

        # Two turns -> two create_execution calls
        self.assertEqual(self.mock_cmf.create_execution.call_count, 2)

        # Check the first execution call
        first_call = self.mock_cmf.create_execution.call_args_list[0]
        self.assertEqual(first_call.kwargs["execution_type"], "AgentTurn")
        self.assertEqual(first_call.kwargs["custom_properties"]["turn_id"], "msg_001")
        self.assertEqual(first_call.kwargs["custom_properties"]["turn_index"], 0)
        self.assertEqual(first_call.kwargs["custom_properties"]["session_id"], "ses_basic01")

        # First turn: no prev transcript -> no input log_dataset.
        # Second turn: prev transcript -> 1 input log_dataset + 3 output log_datasets = 4 total.
        # First turn: 3 output log_datasets.
        # Total log_dataset calls: 3 + 4 = 7
        self.assertEqual(self.mock_cmf.log_dataset.call_count, 7)

        # Two finalize calls (one per turn)
        self.assertEqual(self.mock_cmf.finalize.call_count, 2)

        # Two log_execution_metrics calls
        self.assertEqual(self.mock_cmf.log_execution_metrics.call_count, 2)

    def test_turn_to_turn_lineage_edge(self):
        """Verify turn 2 logs turn 1's transcript as an input."""
        writer = TraceWriter(self.config)
        events = load_fixture("session-basic")

        for event in events:
            writer.handle(events[0]["session_id"], event)

        # Find the input log_dataset call (should be in turn 2's processing)
        input_calls = [
            call for call in self.mock_cmf.log_dataset.call_args_list
            if call.kwargs.get("event") == "input"
        ]
        self.assertEqual(len(input_calls), 1)
        self.assertTrue(input_calls[0].kwargs["url"].endswith("transcript.jsonl"))

    def test_abandoned_tool_preserves_error_status(self):
        """The abandoned-tool fixture has a tool that goes running -> error.
        Verify the error status is preserved in the trace files."""
        writer = TraceWriter(self.config)
        events = load_fixture("session-abandoned-tool")

        for event in events:
            writer.handle(events[0]["session_id"], event)

        # The tool-calls.jsonl should exist and contain the error-status part
        turn_dir = self.runs_dir / "autoresearch" / "ses_abandoned01" / "msg_101"
        tool_calls_path = turn_dir / "tool-calls.jsonl"
        self.assertTrue(tool_calls_path.exists())

        tool_lines = tool_calls_path.read_text().strip().split("\n")
        tool_events = [json.loads(line) for line in tool_lines]

        # Find the error-status bash part
        error_parts = [e for e in tool_events if e["status"] == "error"]
        self.assertEqual(len(error_parts), 1)
        self.assertEqual(error_parts[0]["part_id"], "prt_103")
        self.assertIn("CUDA", error_parts[0]["content"]["output"])

    def test_unknown_event_type_logged_and_skipped(self):
        writer = TraceWriter(self.config)

        writer.handle("ses_1", {
            "type": "session_start", "session_id": "ses_1",
            "source": "opencode", "pipeline_name": "test",
            "parent_session_id": None, "fork_point_message_id": None,
            "ts": "2026-01-01T00:00:00Z",
        })
        # Feed an unknown event type
        writer.handle("ses_1", {"type": "unknown_event", "session_id": "ses_1"})

        # No crash, no extra cmf calls beyond session_start's context
        self.mock_cmf.create_context.assert_called_once()
        self.mock_cmf.create_execution.assert_not_called()

    def test_part_with_no_open_turn_is_dropped(self):
        writer = TraceWriter(self.config)

        writer.handle("ses_1", {
            "type": "session_start", "session_id": "ses_1",
            "source": "opencode", "pipeline_name": "test",
            "parent_session_id": None, "fork_point_message_id": None,
            "ts": "2026-01-01T00:00:00Z",
        })
        # Part before turn_start -> should be dropped, not crash
        writer.handle("ses_1", {
            "type": "part", "session_id": "ses_1", "turn_id": "t1",
            "part_id": "p1", "part_type": "text", "status": "completed",
            "seq": 0, "content": {"text": "hello"}, "ts": "2026-01-01T00:00:01Z",
        })
        self.mock_cmf.create_execution.assert_not_called()

    def test_orphaned_turn_is_auto_closed_on_next_turn_start(self):
        """When turn_start arrives while a turn is still open (no turn_end
        was emitted), the previous turn should be auto-closed with status
        'aborted' so its artifacts aren't lost."""
        writer = TraceWriter(self.config)

        writer.handle("ses_1", {
            "type": "session_start", "session_id": "ses_1",
            "source": "opencode", "pipeline_name": "test",
            "parent_session_id": None, "fork_point_message_id": None,
            "ts": "2026-01-01T00:00:00Z",
        })
        # Open turn 0
        writer.handle("ses_1", {
            "type": "turn_start", "session_id": "ses_1", "turn_id": "t0",
            "turn_index": 0, "role": "user", "ts": "2026-01-01T00:00:01Z",
        })
        # Add a part to turn 0
        writer.handle("ses_1", {
            "type": "part", "session_id": "ses_1", "turn_id": "t0",
            "part_id": "p1", "part_type": "text", "status": "completed",
            "seq": 0, "content": {"text": "hello"}, "ts": "2026-01-01T00:00:02Z",
        })
        # Open turn 1 WITHOUT a turn_end for turn 0
        writer.handle("ses_1", {
            "type": "turn_start", "session_id": "ses_1", "turn_id": "t1",
            "turn_index": 1, "role": "user", "ts": "2026-01-01T00:00:03Z",
        })

        # Turn 0 should have been auto-closed: 2 create_execution calls
        # (turn 0 + turn 1), and turn 0's 3 output log_dataset calls
        self.assertEqual(self.mock_cmf.create_execution.call_count, 2)
        # turn 0: 3 outputs (transcript, reasoning, tool-calls) + finalize
        # turn 1: 1 input (turn 0's transcript)
        output_calls = [
            call for call in self.mock_cmf.log_dataset.call_args_list
            if call.kwargs.get("event") == "output"
        ]
        self.assertEqual(len(output_calls), 3)
        self.assertEqual(self.mock_cmf.finalize.call_count, 1)


if __name__ == "__main__":
    unittest.main()
