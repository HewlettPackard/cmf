---
name: cmf-server
description: >
  Use when deploying the CMF Server locally with Docker Compose, or connecting to an
  existing shared CMF Server. Covers creating the .env file, starting the container
  stack, verifying the web UI, and pointing cmflib clients at the server. If a server
  is already running and credentials are available, skip to the connection section.
version: 1.0.0
---

First check: **is a CMF Server already running?** If yes, skip to [Connecting to an existing server](#connecting-to-an-existing-cmf-server).

## Local deployment

### Prerequisites
- Docker Engine + Docker Compose plugin
- Host IP or hostname (for `REACT_APP_CMF_API_URL`)
- Ports 80 and 443 free (configurable via `NGINX_HTTP_PORT` / `NGINX_HTTPS_PORT`)
- `openssl` on the host (for the self-signed cert helper)

### Step 1 — Clone CMF

```bash
git clone https://github.com/HewlettPackard/cmf
cd cmf
```

### Step 2 — Create `.env`

```env
CMF_DATA_DIR=./data
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
REACT_APP_CMF_API_URL=http://<your-server-ip>:80

POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword    # change in production
POSTGRES_DB=mlmd
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

MCP_EXTERNAL_PORT=8382
```

See [references/env-variables.md](references/env-variables.md) for full variable descriptions and common customizations.

### Step 3 — Generate the TLS certificate (required)

The `nginx` service has a `443 ssl` server block and **will crash on startup if the certificate files are missing**. Generate a self-signed cert before starting the stack:

```bash
scripts/generate-self-signed-cert.sh
```

This writes `cmf.crt` and `cmf.key` into `$CMF_DATA_DIR/nginx-certs/`, which the `nginx` service mounts read-only at `/etc/nginx/certs/`. To use your own certificate instead, copy your `cmf.crt` / `cmf.key` into that directory.

### Step 4 — Start

```bash
docker compose -f docker-compose-server.yml up -d
docker compose -f docker-compose-server.yml ps   # all services should be healthy within ~60s
```

Services started: `postgres`, `server` (CMF API), `ui` (React), `tensorboard`, `nginx` (HTTP + HTTPS), `mcp`.

### Step 5 — Verify

```bash
curl http://<your-server-ip>:80/api/pipelines
# []
```

Open `http://<your-server-ip>:80` (or `https://<your-server-ip>:443`, accepting the self-signed cert warning) in a browser — CMF web UI should load.

### Step 6 — Point clients at the server

On each client machine:
```bash
cmf init local \
  --path /path/to/artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git \
  --cmf-server-url http://<your-server-ip>:80
```

---

## Connecting to an existing CMF Server

```bash
cmf init local \
  --path /path/to/artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git \
  --cmf-server-url http://<server-url>:<port>

cmf init show                       # verify the URL is set
cmf metadata pull -p my_pipeline    # confirm access
```

The CMF Server uses network-level access control (no built-in username/password by default). If your deployment has an auth proxy, ask the administrator for credentials.

---

## Manage the server

```bash
docker compose -f docker-compose-server.yml stop    # stop (data preserved)
docker compose -f docker-compose-server.yml start   # restart
docker compose -f docker-compose-server.yml down    # remove containers (data preserved in CMF_DATA_DIR)

# Destructive — backup CMF_DATA_DIR first!
docker compose -f docker-compose-server.yml down -v && rm -rf ./data
```

## Upgrade

```bash
git pull
docker compose -f docker-compose-server.yml build --no-cache
docker compose -f docker-compose-server.yml up -d
```

## Troubleshooting

- **`REACT_APP_CMF_API_URL` not set** — required; set to the host's IP/hostname
- **`nginx` crashes on startup** — almost always a missing TLS certificate. Run `scripts/generate-self-signed-cert.sh` (or place your own `cmf.crt` / `cmf.key` in `$CMF_DATA_DIR/nginx-certs/`), then `docker compose -f docker-compose-server.yml up -d`. Check with `docker compose -f docker-compose-server.yml logs nginx`.
- **Port 80 in use** — change `NGINX_HTTP_PORT` and update `REACT_APP_CMF_API_URL` to match
- **`postgres` not healthy** — check `docker compose -f docker-compose-server.yml logs postgres`; usually a `CMF_DATA_DIR` permissions issue
- **UI loads but API calls fail** — use the host IP, not `localhost`, in `REACT_APP_CMF_API_URL`; must be reachable from the browser
- **MCP server not reachable** — check `MCP_EXTERNAL_PORT` in `.env` and confirm it is not blocked by a firewall; test with `curl http://<server-ip>:<MCP_EXTERNAL_PORT>/health`
- **Clients cannot push metadata** — confirm `cmf init show` shows the correct server URL; verify with `curl http://<server-ip>:80/api/pipelines` (expect `[]` for an empty server, or a list of pipeline names)

---

**Docs:** [Installation Guide](https://hewlettpackard.github.io/cmf/setup/) · [CMF Client Guide](https://hewlettpackard.github.io/cmf/cmf_client/) · [Web UI Reference](https://hewlettpackard.github.io/cmf/ui/lineage/)
