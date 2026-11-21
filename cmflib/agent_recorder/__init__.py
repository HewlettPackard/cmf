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

"""agent_recorder: tails trace-event spool files and records agent turns
into the user's CMF mlmd as Dataset artifacts under an AgentTurn stage.

Designed to work with opencode-capture (or any producer that emits the
trace-event schema) writing to a spool directory of append-only
<session_id>.jsonl files.
"""

__all__ = ["config", "spool_reader", "trace_writer", "schema"]
