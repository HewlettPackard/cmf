# agent_recorder Design

## Overview

The agent-recorder captures the turn-by-turn trace of a coding-agent session
(e.g., OpenCode driving an autoresearch loop) and records it into the **same
mlmd file** the user's pipeline is already using. Each agent turn produces
three trace files (`transcript.jsonl`, `reasoning.jsonl`, `tool-calls.jsonl`)
that are logged as `Dataset` artifacts under a dedicated `AgentTurn` stage
within the user's pipeline. Turn-to-turn lineage is threaded by logging the
previous turn's transcript as an `input` to the next turn's execution.

## Architecture

```
opencode (with opencode-capture plugin)
    --JSONL--> spool/<session_id>.jsonl  --tail--> agent_recorder --> user's mlmd
```

The recorder is a **separate process** (`cmf recorder start`), not an
in-process hook. This is a hard constraint: the complete turn trace only
exists after `turn_end`, which arrives *after* the user's code (e.g.,
`train.py`) has already run and exited. An in-process bolt-on inside the
user's `create_execution()` / `finalize()` calls cannot capture the complete
trace because the turn is still open when those calls fire.

Running as a separate process also means:

- **Zero overhead** to the user's process (no shared `Cmf` object, no
  cursor clobbering, no SQLite write contention during the turn).
- **Crash safety**: the spool is append-only JSONL with persistent offsets;
  a recorder crash loses at most un-drained spool events, never the user's
  data.
- **Simplicity**: the recorder's `Cmf` instance is the only writer to mlmd
  at `turn_end` time (the user's `train.py` has already exited by then).

## Event Schema

The recorder consumes the 5-event trace schema emitted by opencode-capture:

| Event type      | Key fields                                                        |
|-----------------|-------------------------------------------------------------------|
| `session_start` | `session_id`, `source`, `pipeline_name`, `parent_session_id`     |
| `session_end`   | `session_id`, `status`                                            |
| `turn_start`    | `session_id`, `turn_id`, `turn_index`, `role`, `ts`              |
| `turn_end`      | `session_id`, `turn_id`, `status`, `ts`                           |
| `part`          | `session_id`, `turn_id`, `part_id`, `part_type`, `status`, `seq` |

`part_type` ∈ `text|reasoning|tool|file`; `status` ∈ `pending|running|completed|error`.

A part can be reported multiple times (pending → running → completed); the
recorder keeps only the latest status per `part_id` but every line stays on
disk in the spool unmodified.

## CMF Mapping

| CMF entity   | Maps to                                          |
|--------------|--------------------------------------------------|
| Pipeline     | The user's pipeline (e.g., `autoresearch`)       |
| Stage        | `AgentTurn` (dedicated stage for agent turns)    |
| Execution    | One per turn                                     |
| Artifacts    | `transcript.jsonl`, `reasoning.jsonl`, `tool-calls.jsonl` per turn (as `Dataset` type) |
| Lineage edge | Turn N's `transcript.jsonl` → `input` of turn N+1's execution |
| Metrics      | `turn_metrics` with part/status counts            |

### Correlation to user's ML executions

Each agent turn execution stores a `correlated_ml_exec_id` custom property:
the ID of the user's ML execution (e.g., `train.py`'s execution) whose
`create_time_since_epoch` falls within the turn's `[turn_start_ts,
turn_end_ts]` time window. This is a property-based link (not a structural
artifact edge), queryable by property but not traversable via
`cmf_execution_lineage`. This is the v1 approach; a tighter structural link
can be added later if needed.

The correlation query runs at `turn_end` time, before the recorder creates
its own `AgentTurn` execution, so the query sees the user's ML execution
(train.py's) that was created during the turn but not the recorder's
about-to-be-created agent execution.

## Per-turn trace files

Derived from buffered `part` events, staged under
`<runs_dir>/<pipeline_name>/<session_id>/<turn_id>/`:

- `transcript.jsonl` — every part in `seq` order
- `reasoning.jsonl` — reasoning parts only
- `tool-calls.jsonl` — tool parts only

Rewritten (not appended) after every `part` event so a mid-turn crash still
leaves a partial trace reflecting exactly what streamed. This is what
preserves abandoned tool calls' last status (e.g., `error`) in the trace.

## Configuration

Environment variables (consistent with cmflib's `CMF_LOG_FILE`, `CONFIG_FILE`
pattern):

| Var                       | Default                    | Purpose                                  |
|---------------------------|----------------------------|------------------------------------------|
| `CMF_AGENT_SPOOL_DIR`     | `./spool`                  | Where the capture plugin writes JSONL    |
| `CMF_AGENT_RUNS_DIR`      | `./cmf-runs`               | Per-turn trace file staging              |
| `CMF_AGENT_MLMD_PATH`     | `mlmd`                     | Path to the user's mlmd file             |
| `CMF_AGENT_POLL_INTERVAL` | `1.0`                      | Spool poll cadence (seconds)             |
| `CMF_AGENT_SERVER_URL`    | *(from .cmfconfig)*        | If set, push after every turn            |

CLI flags override env vars, which override `.cmfconfig` defaults.

## Limitations (v1)

- **No sub-agent lineage**: `subtask`/`agent` part types are not captured.
- **No cross-session fork lineage**: `parent_session_id` and
  `fork_point_message_id` are stored as properties but not used to stitch
  artifact DAGs across forks.
- **Property-based correlation only**: the link between an agent turn and
  the user's ML execution is a custom property, not a structural edge.
