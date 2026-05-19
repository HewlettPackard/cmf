---
name: cmf-mcp
description: >
  Use when setting up the CMF MCP (Model Context Protocol) server so that an AI coding
  assistant (Claude, GitHub Copilot, Cursor, etc.) can query CMF pipeline metadata,
  artifact lineage, and model information using natural language. Also use when the CMF
  MCP server is already running and the user wants to query CMF metadata directly from
  their coding agent. Covers Docker deployment, per-agent configuration, using MCP tools
  from within the agent, and multi-server setup.
version: 1.0.0
---

First check: **is the CMF MCP server already running and configured?**

Ask the user, or check for an existing `.mcp.json` / MCP configuration in their project. If the server is already available, skip to [Using CMF MCP from your coding agent](#using-cmf-mcp-from-your-coding-agent).

If not yet set up, guide the user through deploying the server and connecting it to their assistant.

## Prerequisites

- Docker and Docker Compose installed
- A running CMF Server (see `docs/setup/index.md` if not yet deployed)
- An MCP-compatible AI assistant (Claude Code, GitHub Copilot in agent mode, Cursor, etc.)

## What the CMF MCP server provides

Once configured, your AI assistant can answer questions like:

- _"What pipelines are available in CMF?"_
- _"Show me all executions for the Train stage"_
- _"What datasets were used in the last experiment?"_
- _"Get the artifact lineage for models/rf.pkl"_
- _"Show the model card for model ID 42"_

## Step 1 — Clone and configure

The MCP server lives in the `mcp/` directory of the CMF repository.

```bash
cd mcp/
cp .env.example .env   # or create .env manually
```

Edit `.env` to point at your CMF Server(s):

```env
# Required: at least one CMF Server URL
CMF_SERVER_URL=http://<your-cmf-server-host>:80

# Optional: up to 4 CMF Servers for multi-environment support
# CMF_SERVER_URL_2=http://staging-server:80
# CMF_SERVER_URL_3=http://prod-server:80
```

## Step 2 — Start the MCP server with Docker

```bash
cd mcp/
docker compose up -d
```

Verify it is running:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

The MCP server listens on port **8000** by default.

## Step 3 — Connect to your AI assistant

### Claude Code

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "cmf": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

Then restart Claude Code or run `/mcp` to reload. Claude will automatically discover and use the CMF tools.

### GitHub Copilot (VS Code)

Open VS Code settings (`Ctrl+,` / `Cmd+,`), search for **MCP**, and add the server under **GitHub Copilot → MCP Servers**:

```json
{
  "github.copilot.chat.mcpServers": {
    "cmf": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

Alternatively, add it to your workspace's `.vscode/settings.json`. Reload the VS Code window after saving.

### Cursor

Add to Cursor's MCP settings (`~/.cursor/mcp.json` or Cursor Settings → MCP → Add Server):

```json
{
  "mcpServers": {
    "cmf": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Codex

Add to `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "cmf": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Other MCP-compatible assistants

Use the server URL `http://localhost:8000/mcp` with HTTP transport in your assistant's MCP configuration file.

## Step 4 — Verify with natural language

Once connected, test with a natural language query in your AI assistant:

```
What pipelines are available in CMF?
```

Expected: the assistant lists your pipelines by calling `cmf_show_pipelines` internally.

## Available MCP tools

| Tool | What it returns |
|------|----------------|
| `cmf_show_pipelines` | All pipeline names |
| `cmf_show_executions` | Executions for a pipeline and stage |
| `cmf_execution_lineage` | Full lineage tree for an execution |
| `cmf_show_artifacts` | Artifacts filtered by type and pipeline |
| `cmf_artifact_lineage` | Artifact lineage for a pipeline |
| `cmf_show_model_card` | Model metadata, inputs, and training details |

## Using CMF MCP from your coding agent

Once the MCP server is configured, you can query CMF metadata using natural language directly in your agent's chat. The agent calls the CMF MCP tools automatically — no code required.

### Example prompts

**Explore pipelines:**
```
What pipelines are tracked in CMF?
List the stages in the my_pipeline pipeline.
```

**Inspect executions:**
```
Show me all executions for the Train stage in my_pipeline.
What hyperparameters were used in the last training run?
```

**Trace lineage:**
```
What datasets were used to produce models/rf.pkl?
Show me the full artifact lineage for the production pipeline.
Get the execution lineage for execution ID 42.
```

**Model governance:**
```
Show the model card for model ID 7.
What were the evaluation metrics for the latest model?
Which datasets were the inputs for model 7?
```

### Checking available CMF tools

In Claude Code, run `/mcp` to list all connected MCP servers and their tools. You should see the `cmf` server with its six tools listed.

In Cursor and GitHub Copilot, open the agent chat and type `@cmf` — the agent will show available CMF tools.

In any agent, you can ask:
```
What CMF tools do you have available?
```

### Workflow: instrument, run, then query

A typical workflow combining CMF instrumentation and MCP querying:

1. Instrument your pipeline with the **cmf-instrument** skill
2. Run your pipeline — metadata is written to the local `mlmd` file
3. Push metadata: `cmf metadata push -p my_pipeline`
4. Ask your agent: _"Show me the artifact lineage for the latest training run"_

The agent calls `cmf_artifact_lineage` or `cmf_execution_lineage` against the CMF Server and presents the results.

## Multi-server configuration

To query development, staging, and production simultaneously, configure multiple server URLs in `.env`:

```env
CMF_SERVER_URL=http://dev-server:80
CMF_SERVER_URL_2=http://staging-server:80
CMF_SERVER_URL_3=http://prod-server:80
```

The MCP server exposes each as a separate context; your assistant can query across environments.

## Troubleshooting

- **`Connection refused` on port 8000**: Docker container is not running. Run `docker compose up -d` in the `mcp/` directory.
- **`CMF Server unreachable`**: The URL in `.env` is wrong or the CMF Server is not running. Verify with `curl http://<cmf-server-host>:80/apiv1.0/health`.
- **MCP tools not appearing in assistant**: Restart the assistant after updating `.mcp.json`. Some assistants require a full restart to reload MCP servers.
- **Empty results from tools**: No pipelines have been pushed to the CMF Server yet. Run `cmf metadata push -p <name>` from a client machine first.

## Further reading

- `docs/mcp/index.md` — MCP server overview and architecture
- `docs/mcp/quickstart.md` — Quick start guide
- `docs/mcp/configuration.md` — Full configuration reference
- `docs/mcp/tools.md` — Complete MCP tool reference
- `docs/setup/index.md` — CMF Server installation
