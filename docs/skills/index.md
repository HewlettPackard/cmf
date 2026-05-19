# CMF Agent Skills

CMF ships a set of **agent skills** that let AI coding assistants (Claude Code, GitHub Copilot in agent mode, Cursor, Gemini CLI, and others) guide users through every CMF workflow — from first-time setup to querying artifact lineage.

Skills are prompt files that follow the [agentskills.io](https://agentskills.io) standard. Once installed, they appear as slash commands in your coding assistant's chat interface.

---

## Installing the skills

### Automatic (recommended)

From your ML project directory, run:

```bash
npx skills add HewlettPackard/cmf --full-depth -y
```

This detects your coding agent and copies skills to the right directory automatically. Works with Claude Code, GitHub Copilot, Cursor, Codex, OpenCode, and any [agentskills.io](https://agentskills.io)-compatible tool.

To install a single skill:

```bash
npx skills add HewlettPackard/cmf/tree/main/skills/cmf-instrument -y
```

To install globally across all projects:

```bash
npx skills add HewlettPackard/cmf --full-depth -y --global
```

### Manual installation

Copy each skill directory into your agent's skills folder:

| Tool | Project-level directory | Global directory |
|------|------------------------|-----------------|
| Claude Code | `.claude/skills/<skill-name>/` | `~/.claude/skills/<skill-name>/` |
| GitHub Copilot | `.agents/skills/<skill-name>/` | `~/.copilot/skills/<skill-name>/` |
| Cursor | `.agents/skills/<skill-name>/` | `~/.cursor/skills/<skill-name>/` |
| Codex | `.agents/skills/<skill-name>/` | `~/.codex/skills/<skill-name>/` |
| OpenCode | `.agents/skills/<skill-name>/` | `~/.config/opencode/skills/<skill-name>/` |

---

## Available skills

| Skill | Slash command | Purpose |
|-------|--------------|---------|
| **cmf** | `/cmf <task>` | Router — describe your task in plain language and get routed to the right skill |
| **cmf-init** | `/cmf-init` | Install cmflib and run `cmf init` to configure a storage backend (local, S3, MinIO, SSH, OSDF) |
| **cmf-instrument** | `/cmf-instrument` | Add CMF tracking to existing Python ML pipeline code |
| **cmf-sync** | `/cmf-sync` | Push/pull metadata and artifacts to/from a CMF Server |
| **cmf-query** | `/cmf-query` | Query pipeline history and artifact lineage with `CmfQuery` |
| **cmf-server** | `/cmf-server` | Deploy CMF Server locally with Docker Compose, or connect to an existing server |
| **cmf-mcp** | `/cmf-mcp` | Deploy the CMF MCP server for natural language metadata queries |

---

## Skill details

### `/cmf` — Router skill

The entry point for all CMF tasks. Describe what you want to do in plain language and the skill will route you to the correct specialized skill.

**Usage examples:**

```
/cmf I want to start tracking metadata in my ML pipeline
/cmf how do I push my artifacts to the CMF Server?
/cmf show me the lineage for my trained model
```

---

### `/cmf-init` — Initialize CMF

Walks through installing `cmflib` and running `cmf init` with any supported storage backend:

- **Local** — single-machine development, artifacts in a local directory
- **MinIO / Amazon S3** — shared object storage for teams
- **SSH remote** — artifacts stored on a remote server
- **OSDF** — distributed data federation across institutions (Pelican Platform)

After this skill completes you will have a working configuration (`cmf init show` returns valid output) and be ready to instrument your pipeline.

---

### `/cmf-instrument` — Instrument ML code

The core instrumentation skill. It adds CMF metadata tracking calls to your Python ML pipeline scripts:

1. Imports `Cmf` and initializes the metadata writer
2. Creates contexts (stage types) and executions (stage runs) with hyperparameters
3. Logs datasets, models, and metrics as inputs and outputs
4. Calls `finalize()` to record the Git commit SHA

Includes copy-paste templates for data preparation, training, and evaluation stages, plus a checklist for auditing existing scripts.

**Example instrumented training stage:**

```python
from cmflib.cmf import Cmf

def train(train_path: str, model_path: str, params: dict) -> None:
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Train")
    metawriter.create_execution(execution_type="Train", custom_properties=params)

    metawriter.log_dataset(train_path, "input")

    model = fit_model(train_path, params)

    metawriter.log_model(path=model_path, event="output",
                         model_framework="scikit-learn",
                         model_type="RandomForestClassifier",
                         model_name="RandomForestClassifier:default")
    metawriter.finalize()
```

---

### `/cmf-sync` — Sync metadata and artifacts

Guides through the push/pull workflow for sharing results with teammates and a central CMF Server:

```bash
# Push your results
cmf metadata push -p my_pipeline
cmf artifact push -p my_pipeline

# Pull a teammate's work
cmf metadata pull -p my_pipeline
cmf artifact pull -p my_pipeline
```

Covers solo and team workflows, error diagnosis, and the complete command reference.

---

### `/cmf-query` — Query lineage and artifacts

Writes `CmfQuery` Python code for common metadata questions:

- Listing pipelines and their stages
- Comparing hyperparameters across training runs
- Tracing a model's full data lineage
- Finding all artifacts consumed or produced by an execution

Also covers the CLI equivalents (`cmf pipeline list`, `cmf execution list`, `cmf artifact list`).

---

### `/cmf-server` — Deploy or connect to CMF Server

Handles two scenarios:

1. **Local deployment** — walks through cloning the CMF repo, creating a `.env` file with the right variables (`CMF_DATA_DIR`, `REACT_APP_CMF_API_URL`, `POSTGRES_*`, `MCP_EXTERNAL_PORT`), starting the Docker Compose stack, and verifying the web UI.

2. **Existing server** — if a shared CMF Server is already running, guides the user through pointing their local `cmf init` at it with `--cmf-server-url`, verifying connectivity, and pushing the first pipeline.

---

### `/cmf-mcp` — CMF MCP server

Covers two scenarios:

1. **Setting up** — deploys the [CMF MCP Server](../mcp/index.md) with Docker and connects it to your AI assistant (Claude Code, GitHub Copilot, Cursor, Codex).
2. **Already running** — if the CMF MCP server is already configured, shows how to use it from within your agent using natural language prompts like _"What pipelines are available?"_ or _"Show the artifact lineage for models/rf.pkl"_.

After setup, the assistant calls CMF tools directly — no manual `CmfQuery` scripting required.

---

## Skill files

The skill source files live in the `skills/` directory of the CMF repository:

```
skills/
├── README.md               # Installation and usage instructions
├── cmf/
│   └── SKILL.md            # Router skill
├── cmf-init/
│   └── SKILL.md
├── cmf-instrument/
│   └── SKILL.md
├── cmf-sync/
│   └── SKILL.md
├── cmf-query/
│   └── SKILL.md
├── cmf-server/
│   └── SKILL.md
└── cmf-mcp/
    └── SKILL.md
```

See the [skills/README.md](https://github.com/HewlettPackard/cmf/blob/master/skills/README.md) for full details on installation, usage, and contributing new skills.
