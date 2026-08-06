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

"""Trace-event schema constants and validation.

Mirrors the TypeScript types in opencode-capture/src/schema.ts. The recorder
works with raw dicts throughout; this module provides constants for dispatch
and a lightweight validator used by tests.
"""

from __future__ import annotations

from typing import Any, List

# Event types
SESSION_START = "session_start"
SESSION_END = "session_end"
TURN_START = "turn_start"
TURN_END = "turn_end"
PART = "part"

ALL_EVENT_TYPES = frozenset({
    SESSION_START, SESSION_END, TURN_START, TURN_END, PART,
})

# Part types
PART_TYPE_TEXT = "text"
PART_TYPE_REASONING = "reasoning"
PART_TYPE_TOOL = "tool"
PART_TYPE_FILE = "file"

ALL_PART_TYPES = frozenset({
    PART_TYPE_TEXT, PART_TYPE_REASONING, PART_TYPE_TOOL, PART_TYPE_FILE,
})

# Part statuses
PART_STATUS_PENDING = "pending"
PART_STATUS_RUNNING = "running"
PART_STATUS_COMPLETED = "completed"
PART_STATUS_ERROR = "error"

ALL_PART_STATUSES = frozenset({
    PART_STATUS_PENDING, PART_STATUS_RUNNING, PART_STATUS_COMPLETED, PART_STATUS_ERROR,
})

# Turn statuses
TURN_STATUS_COMPLETED = "completed"
TURN_STATUS_ERROR = "error"
TURN_STATUS_ABORTED = "aborted"

ALL_TURN_STATUSES = frozenset({
    TURN_STATUS_COMPLETED, TURN_STATUS_ERROR, TURN_STATUS_ABORTED,
})


def validate_event(event: dict) -> List[str]:
    """Return a list of validation error messages (empty if valid).

    Does not raise; the recorder's SpoolReader already skips malformed JSON
    lines. This function is for tests and debugging.
    """
    errors: List[str] = []
    etype = event.get("type")
    if etype not in ALL_EVENT_TYPES:
        errors.append(f"unknown event type: {etype!r}")
        return errors

    if "session_id" not in event:
        errors.append(f"{etype}: missing session_id")
    if "ts" not in event:
        errors.append(f"{etype}: missing ts")

    if etype == SESSION_START:
        for field in ("source", "pipeline_name"):
            if field not in event:
                errors.append(f"{etype}: missing {field}")
    elif etype == SESSION_END:
        if event.get("status") not in ALL_TURN_STATUSES:
            errors.append(f"{etype}: invalid status {event.get('status')!r}")
    elif etype == TURN_START:
        for field in ("turn_id", "turn_index", "role"):
            if field not in event:
                errors.append(f"{etype}: missing {field}")
    elif etype == TURN_END:
        for field in ("turn_id", "status"):
            if field not in event:
                errors.append(f"{etype}: missing {field}")
        if event.get("status") not in ALL_TURN_STATUSES:
            errors.append(f"{etype}: invalid status {event.get('status')!r}")
    elif etype == PART:
        for field in ("turn_id", "part_id", "part_type", "status", "seq"):
            if field not in event:
                errors.append(f"{etype}: missing {field}")
        if event.get("part_type") not in ALL_PART_TYPES:
            errors.append(f"{etype}: invalid part_type {event.get('part_type')!r}")
        if event.get("status") not in ALL_PART_STATUSES:
            errors.append(f"{etype}: invalid status {event.get('status')!r}")
        if not isinstance(event.get("seq"), int):
            errors.append(f"{etype}: seq must be int, got {type(event.get('seq'))}")

    return errors


def is_valid(event: dict) -> bool:
    return len(validate_event(event)) == 0
