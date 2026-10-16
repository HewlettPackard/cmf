# agent_recorder

Records coding-agent session traces into CMF as `Dataset` artifacts under an
`AgentTurn` stage within the user's pipeline.

## Overview

The agent-recorder captures the turn-by-turn trace of a coding-agent session
(e.g., OpenCode driving an autoresearch loop) and records it into the **same
mlmd file** the user's pipeline is already using. Each agent turn produces
three trace files that are logged as `Dataset` artifacts:

- `transcript.jsonl` — every part in sequence order
- `reasoning.jsonl` — reasoning/thinking parts only
- `tool-calls.jsonl` — tool call parts only

Turn-to-turn lineage is threaded by logging the previous turn's transcript as
an `input` to the next turn's execution.

## Architecture

```
opencode (with opencode-capture plugin)
    --JSONL--> spool/<session_id>.jsonl  --tail--> cmf recorder start --> user's mlmd
```

The recorder is a **separate process**, not an in-process hook. This is a
hard constraint: the complete turn trace only exists after `turn_end`, which
arrives *after* the user's code (e.g., `train.py`) has already run and exited.

See [DESIGN.md](DESIGN.md) for the full design document.

## Quick Start

### 1. Install opencode-capture

Configure the opencode-capture plugin in your project's `opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [["opencode-capture", {
    "pipelineName": "my_pipeline",
    "spoolDir": "/path/to/spool"
  }]]
}
```

### 2. Initialize CMF (one-time)

```bash
cmf init local --path ./cmf_artifacts --git-remote-url https://github.com/you/repo.git
```

### 3. Start the recorder

```bash
cmf recorder start --spool-dir /path/to/spool
```

### 4. Run your agent

```bash
opencode
```

As the agent runs, each completed turn is automatically recorded into your
`mlmd` file as `Dataset` artifacts under the `AgentTurn` stage.

## Configuration

All settings can be overridden via CLI flags or environment variables:

| Flag               | Env var                       | Default      | Description                          |
|--------------------|-------------------------------|--------------|--------------------------------------|
| `--spool-dir`      | `CMF_AGENT_SPOOL_DIR`         | `./spool`    | Spool directory with JSONL files     |
| `--runs-dir`       | `CMF_AGENT_RUNS_DIR`          | `./cmf-runs` | Per-turn trace file staging          |
| `--mlmd-path`      | `CMF_AGENT_MLMD_PATH`         | `mlmd`       | Path to the mlmd file                |
| `--poll-interval`  | `CMF_AGENT_POLL_INTERVAL`     | `1.0`        | Poll cadence in seconds              |
| `--once`           |                               |              | Process current spool and exit (testing) |
| `-v` / `--verbose` |                               |              | Enable debug logging                 |
|                    | `CMF_AGENT_SERVER_URL`        | *(from .cmfconfig)* | CMF server URL for push     |

CLI flags override environment variables, which override `.cmfconfig`
defaults.

## Querying Recorded Turns

After running, query the recorded agent turns with standard CMF commands:

```bash
# List all pipelines (includes your pipeline with AgentTurn stage)
cmf pipeline list

# List executions (shows both your ML executions and AgentTurn executions)
cmf execution list -p my_pipeline

# List artifacts (shows transcript.jsonl, reasoning.jsonl, tool-calls.jsonl)
cmf artifact list -p my_pipeline
```

Each `AgentTurn` execution has a `correlated_ml_exec_id` custom property
linking it to the user's ML execution (e.g., `train.py`) that ran during
that turn.

## Testing

```bash
# Spool reader tests (pure stdlib, no cmflib required)
python3 -m pytest cmflib/tests/agent_recorder/test_spool_reader.py

# Trace writer tests (mocks Cmf, no real mlmd/DVC needed)
python3 -m pytest cmflib/tests/agent_recorder/test_trace_writer.py

# Run all agent_recorder tests
python3 -m pytest cmflib/tests/agent_recorder/
```

## Event Schema

The recorder consumes the 5-event trace schema emitted by opencode-capture:

| Event type      | Key fields                                        |
|-----------------|---------------------------------------------------|
| `session_start` | `session_id`, `source`, `pipeline_name`           |
| `session_end`   | `session_id`, `status`                            |
| `turn_start`    | `session_id`, `turn_id`, `turn_index`, `role`     |
| `turn_end`      | `session_id`, `turn_id`, `status`                 |
| `part`          | `session_id`, `turn_id`, `part_id`, `part_type`   |

Any producer that emits this schema to the spool directory will work — the
recorder is not specific to opencode-capture.
