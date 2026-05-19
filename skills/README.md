# CMF Skills

Agent skills for the [Common Metadata Framework (CMF)](https://github.com/HewlettPackard/cmf) that help coding assistants instrument ML pipelines, query metadata, and manage artifacts.

Compatible with Claude Code, GitHub Copilot (agent mode), Cursor, Gemini CLI, and any tool that supports the [agentskills.io](https://agentskills.io) standard.

---

## Installing the skills

### Recommended — `npx skills add` (automatic, all agents)

Run this command from your ML project directory:

```bash
npx skills add HewlettPackard/cmf --full-depth -y
```

This detects your coding agent and copies the skills to the correct directory automatically. Works with Claude Code, GitHub Copilot, Cursor, Codex, OpenCode, Gemini CLI, and any tool that supports the [agentskills.io](https://agentskills.io) standard.

To install a single skill instead of the full set:

```bash
npx skills add HewlettPackard/cmf/tree/main/skills/cmf-instrument -y
```

To install globally (available in all projects):

```bash
npx skills add HewlettPackard/cmf --full-depth -y --global
```

### Manual installation (any agent)

Clone or download this repository, then copy each skill directory you want into your agent's skills folder. The skill directory name must be preserved (e.g. `cmf-instrument/`).

**Project-level** (skills available in this project only):

| Tool | Skills directory |
|------|-----------------|
| Claude Code | `.claude/skills/<skill-name>/` |
| GitHub Copilot | `.agents/skills/<skill-name>/` |
| Cursor | `.agents/skills/<skill-name>/` |
| Codex | `.agents/skills/<skill-name>/` |
| OpenCode | `.agents/skills/<skill-name>/` |

**Global** (skills available in all projects):

| Tool | Skills directory |
|------|-----------------|
| Claude Code | `~/.claude/skills/<skill-name>/` |
| GitHub Copilot | `~/.copilot/skills/<skill-name>/` |
| Cursor | `~/.cursor/skills/<skill-name>/` |
| Codex | `~/.codex/skills/<skill-name>/` |
| OpenCode | `~/.config/opencode/skills/<skill-name>/` |

**Example — install `cmf-instrument` globally for Claude Code:**

```bash
cp -r skills/cmf-instrument ~/.claude/skills/
```

**Example — install all CMF skills for GitHub Copilot (project-level):**

```bash
mkdir -p .agents/skills
cp -r skills/cmf skills/cmf-init skills/cmf-instrument skills/cmf-sync skills/cmf-query skills/cmf-server skills/cmf-mcp .agents/skills/
```

### Claude Code marketplace

```
/plugin marketplace add HewlettPackard/cmf
```

---

## Available skills

| Skill | Invoke with | What it does |
|-------|-------------|--------------|
| **cmf** | `/cmf <task>` | Router — describes your task and gets routed to the right skill |
| **cmf-init** | `/cmf-init` | Install cmflib, run `cmf init`, configure a storage backend (local, S3, MinIO, SSH, OSDF) |
| **cmf-instrument** | `/cmf-instrument` | Add CMF tracking calls to existing Python ML pipeline code |
| **cmf-sync** | `/cmf-sync` | Push/pull metadata and artifacts to/from a CMF Server |
| **cmf-query** | `/cmf-query` | Query pipeline history and artifact lineage with `CmfQuery` |
| **cmf-server** | `/cmf-server` | Deploy CMF Server locally with Docker Compose, or connect to an existing server |
| **cmf-mcp** | `/cmf-mcp` | Deploy the CMF MCP server and connect it to your AI assistant |

---

## Using the skills

After installation, activate a skill by typing its slash command in your coding assistant's chat:

```
/cmf I want to add metadata tracking to my training script
```

```
/cmf-instrument
```

```
/cmf-init
```

The **`/cmf`** router skill accepts a free-text description of your task and routes you to the right specialized skill automatically. Use the specific skill commands if you already know what you need.

---

## Skill descriptions

### `/cmf` — Router

Describe what you want to do with CMF in plain language. The skill identifies the right workflow and loads the appropriate sub-skill.

**Examples:**
- `/cmf I need to set up CMF for the first time`
- `/cmf add metadata logging to my scikit-learn pipeline`
- `/cmf how do I push my results to the CMF Server?`
- `/cmf query the artifact lineage for my model`

---

### `/cmf-init` — Initialize CMF

Guides you through installing `cmflib` and running `cmf init` with your chosen storage backend:

- **Local** — artifacts stored on the local filesystem
- **MinIO / Amazon S3** — object storage for teams
- **SSH remote** — artifacts on a remote machine
- **OSDF** — distributed data federation across institutions (Pelican Platform)

After this skill completes, you will have a working `cmf init show` output and be ready to instrument your pipeline.

---

### `/cmf-instrument` — Instrument ML code

Adds CMF metadata tracking to your Python ML pipeline scripts. The skill will:

1. Identify the stages in your code
2. Add `Cmf()` initialization, `create_context()`, and `create_execution()` calls
3. Log datasets, models, and metrics as inputs and outputs
4. Add `finalize()` at the end of each stage

Includes ready-to-use templates for data preparation, training, and evaluation stages, plus a checklist for auditing existing scripts.

---

### `/cmf-sync` — Sync metadata & artifacts

Guides you through pushing your results to the CMF Server and pulling a teammate's work:

```bash
# Share your results
cmf metadata push -p my_pipeline
cmf artifact push -p my_pipeline

# Get a teammate's results
cmf metadata pull -p my_pipeline
cmf artifact pull -p my_pipeline
```

Covers solo and collaborative team workflows, error handling, and the full push/pull command reference.

---

### `/cmf-query` — Query lineage & artifacts

Writes `CmfQuery` Python code to answer questions about your pipeline:

- List all pipelines and their stages
- Compare hyperparameters across training runs
- Trace a model's full data lineage (which datasets produced it?)
- Find all artifacts consumed or produced by a specific execution
- Export metadata for offline analysis

Also covers the CLI equivalents (`cmf pipeline list`, `cmf execution list`, `cmf artifact list`).

---

### `/cmf-server` — Deploy or connect to CMF Server

Two scenarios:

1. **Local deployment** — clones the CMF repo, creates a `.env` file, and starts the full server stack with `docker compose -f docker-compose-server.yml up -d`. Stack includes PostgreSQL, CMF API server, React UI, TensorBoard, MCP server, and Nginx.

2. **Connect to existing server** — if a CMF Server is already running (e.g. shared team server), configures the local `cmf init` to point at it with `--cmf-server-url`.

Key `.env` variables covered: `CMF_DATA_DIR`, `NGINX_HTTP_PORT`, `REACT_APP_CMF_API_URL`, `POSTGRES_*`, `MCP_EXTERNAL_PORT`.

---

### `/cmf-mcp` — CMF MCP server

Deploys the CMF MCP server with Docker and connects it to your AI assistant. After setup, your assistant can answer natural language questions like _"What pipelines are available?"_ or _"Show me the artifact lineage for the production model"_ by calling CMF tools directly.

---

## Updating the skills

Run the same install command again to get the latest version:

```bash
npx skills add HewlettPackard/cmf --full-depth -y
```

---

## Contributing

Skills live in the `skills/` directory of this repository. Each skill is a folder containing a `SKILL.md` file with YAML frontmatter and instructional content.

To add or improve a skill, edit the corresponding `SKILL.md` and open a pull request against the `master` branch.

---

## License

Apache 2.0 — see [LICENSE](../LICENSE) for details.
