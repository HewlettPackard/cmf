---
name: cmf
description: >
  Use when working with the Common Metadata Framework (CMF) — initializing CMF in a project,
  instrumenting ML pipeline code, syncing metadata and artifacts with a CMF Server, querying
  lineage and artifacts, or setting up the CMF MCP server for AI assistant integration.
  Routes to the appropriate specialized skill based on the task.
version: 1.0.0
user_invocable: true
argument_hint: "<task>"
---

Route to the appropriate sub-skill based on the user's task. If the task is ambiguous, ask one clarifying question before routing.

## Quickstart (default path)

If the user wants to add CMF to their project for the first time, or the request is general/unclear, route here:

**[cmf-init](../cmf-init/SKILL.md)** — Install cmflib, configure a storage backend, and create the mlmd metadata store.

## Routing Table

| Task | Sub-skill |
|------|-----------|
| Install CMF, configure storage backend (local, S3, MinIO, SSH, OSDF), run `cmf init` | [cmf-init](../cmf-init/SKILL.md) |
| Add `Cmf()` calls to existing ML pipeline code — contexts, executions, datasets, models, metrics | [cmf-instrument](../cmf-instrument/SKILL.md) |
| Push or pull metadata and artifacts using the CMF CLI | [cmf-sync](../cmf-sync/SKILL.md) |
| Query pipeline history, artifact lineage, and execution metadata using `CmfQuery` | [cmf-query](../cmf-query/SKILL.md) |
| Deploy CMF Server with Docker Compose, or connect to an existing shared server | [cmf-server](../cmf-server/SKILL.md) |
| Set up the CMF MCP server so an AI assistant can query CMF metadata | [cmf-mcp](../cmf-mcp/SKILL.md) |

## Key Concepts

- **Pipeline** — top-level grouping of stages, identified by `pipeline_name` passed to `Cmf()`
- **Context** — a stage type (e.g. `"train"`, `"evaluate"`), created with `create_context()`
- **Execution** — one run of a stage, created with `create_execution()`; hyperparameters go here
- **Artifact** — dataset, model, or metrics file logged as input or output of an execution
- **mlmd** — the local SQLite file that stores all metadata; pushed to CMF Server for collaboration

---

**Docs:** [Getting Started](https://hewlettpackard.github.io/cmf/) · [cmflib API](https://hewlettpackard.github.io/cmf/cmflib/) · [CLI Reference](https://hewlettpackard.github.io/cmf/cmf_client/) · [MCP Server](https://hewlettpackard.github.io/cmf/mcp/)
