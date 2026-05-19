---
name: cmf-mcp
description: >
  Use when setting up the CMF MCP server so an AI coding assistant can query CMF metadata
  using natural language, or when the CMF MCP server is already running and the user wants
  to use it from their coding agent. Covers Docker deployment, per-agent configuration
  (Claude Code, GitHub Copilot, Cursor, Codex), and example prompts.
version: 1.0.0
---

First check: **is the CMF MCP server already running?** Check for an existing `.mcp.json` in the project. If yes, skip to [Using CMF MCP from your coding agent](#using-cmf-mcp-from-your-coding-agent).

## Prerequisites (new deployment)

- Docker + Docker Compose
- A running CMF Server (see [`../cmf-server/SKILL.md`](../cmf-server/SKILL.md))
- An MCP-compatible AI assistant

## Deploy the MCP server

```bash
cd mcp/
cp .env.example .env
```

Edit `.env`:
```env
CMF_SERVER_URL=http://<your-cmf-server-host>:80
# Optional second/third server:
# CMF_SERVER_URL_2=http://staging-server:80
```

```bash
docker compose up -d
curl http://localhost:8000/health   # → {"status": "ok"}
```

## Connect to your coding agent

### Claude Code — `.mcp.json` (project root)
```json
{
  "mcpServers": {
    "cmf": { "url": "http://localhost:8000/mcp", "transport": "http" }
  }
}
```
Restart Claude Code or run `/mcp` to reload.

### GitHub Copilot — VS Code settings
```json
{
  "github.copilot.chat.mcpServers": {
    "cmf": { "url": "http://localhost:8000/mcp", "transport": "http" }
  }
}
```
Add to `.vscode/settings.json` or VS Code user settings. Reload the window.

### Cursor — `~/.cursor/mcp.json`
```json
{
  "mcpServers": {
    "cmf": { "url": "http://localhost:8000/mcp", "transport": "http" }
  }
}
```

### Codex — `~/.codex/config.json`
```json
{
  "mcpServers": {
    "cmf": { "url": "http://localhost:8000/mcp", "transport": "http" }
  }
}
```

---

## Using CMF MCP from your coding agent

Once connected, query CMF metadata in natural language:

```
What pipelines are tracked in CMF?
Show all executions for the Train stage in my_pipeline.
What datasets produced models/rf.pkl?
Show the model card for model ID 7.
What were the evaluation metrics for the latest run?
```

**Check available tools** — in Claude Code run `/mcp`; in Cursor/Copilot type `@cmf` in agent chat.

**End-to-end workflow:**
1. Instrument pipeline → `cmf metadata push -p my_pipeline` → ask the agent natural language questions

See [references/mcp-tools.md](references/mcp-tools.md) for the full tool reference.

## Troubleshooting

- **`Connection refused` on port 8000** — run `docker compose up -d` in `mcp/`
- **CMF Server unreachable** — verify with `curl http://<cmf-server>:80/apiv1.0/pipelines`
- **Tools not appearing** — restart the agent after updating `.mcp.json`
- **Empty results** — push metadata first: `cmf metadata push -p <name>`

---

**Docs:** [MCP Server overview](https://hewlettpackard.github.io/cmf/mcp/) · [Quick Start](https://hewlettpackard.github.io/cmf/mcp/quickstart/) · [Configuration](https://hewlettpackard.github.io/cmf/mcp/configuration/) · [Tools Reference](https://hewlettpackard.github.io/cmf/mcp/tools/)
