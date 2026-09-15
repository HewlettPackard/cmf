"""Unit tests for SpoolReader -- pure stdlib, no cmflib required.

Run with: python3 -m pytest cmflib/tests/agent_recorder/test_spool_reader.py
"""

import json
import tempfile
import unittest
from pathlib import Path

from cmflib.agent_recorder.spool_reader import SpoolReader


def write_line(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


class SpoolReaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spool_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_lines_appended_before_first_poll(self):
        session_file = self.spool_dir / "ses_1.jsonl"
        write_line(session_file, {"type": "session_start", "session_id": "ses_1", "n": 1})
        write_line(session_file, {"type": "session_end", "session_id": "ses_1", "n": 2})

        reader = SpoolReader(str(self.spool_dir))
        events = list(reader.poll())

        self.assertEqual(len(events), 2)
        self.assertEqual([sid for sid, _ in events], ["ses_1", "ses_1"])
        self.assertEqual(events[0][1]["n"], 1)
        self.assertEqual(events[1][1]["n"], 2)

    def test_does_not_reread_already_consumed_lines(self):
        session_file = self.spool_dir / "ses_1.jsonl"
        write_line(session_file, {"type": "session_start", "session_id": "ses_1"})

        reader = SpoolReader(str(self.spool_dir))
        first_pass = list(reader.poll())
        second_pass = list(reader.poll())

        self.assertEqual(len(first_pass), 1)
        self.assertEqual(len(second_pass), 0)

    def test_leaves_incomplete_trailing_line_for_next_poll(self):
        session_file = self.spool_dir / "ses_1.jsonl"
        with session_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "session_start", "session_id": "ses_1"}) + "\n")
            f.write('{"type": "turn_start", "session_id": "ses_1"')  # no closing brace/newline

        reader = SpoolReader(str(self.spool_dir))
        events = list(reader.poll())
        self.assertEqual(len(events), 1)

        with session_file.open("a", encoding="utf-8") as f:
            f.write('}\n')  # finish the line
        events = list(reader.poll())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1]["type"], "turn_start")

    def test_offsets_survive_a_new_reader_instance(self):
        session_file = self.spool_dir / "ses_1.jsonl"
        write_line(session_file, {"type": "session_start", "session_id": "ses_1"})
        list(SpoolReader(str(self.spool_dir)).poll())

        write_line(session_file, {"type": "session_end", "session_id": "ses_1"})
        events = list(SpoolReader(str(self.spool_dir)).poll())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1]["type"], "session_end")

    def test_multiple_sessions_do_not_cross_talk(self):
        write_line(self.spool_dir / "ses_a.jsonl", {"type": "session_start", "session_id": "ses_a"})
        write_line(self.spool_dir / "ses_b.jsonl", {"type": "session_start", "session_id": "ses_b"})

        events = list(SpoolReader(str(self.spool_dir)).poll())
        session_ids = sorted(sid for sid, _ in events)
        self.assertEqual(session_ids, ["ses_a", "ses_b"])

    def test_skips_malformed_lines_without_crashing(self):
        session_file = self.spool_dir / "ses_1.jsonl"
        with session_file.open("w", encoding="utf-8") as f:
            f.write("not json\n")
            f.write(json.dumps({"type": "session_start", "session_id": "ses_1"}) + "\n")

        events = list(SpoolReader(str(self.spool_dir)).poll())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1]["type"], "session_start")


if __name__ == "__main__":
    unittest.main()
