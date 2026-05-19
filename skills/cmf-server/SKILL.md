---
name: cmf-server
description: >
  Use when deploying the CMF Server locally with Docker Compose, or when connecting
  to an existing shared CMF Server using credentials. Covers editing the .env file,
  configuring PostgreSQL, starting containers, verifying the web UI, and pointing
  cmflib clients at the server. If a CMF Server is already running and the user has
  a URL and credentials, skip to the connection section.
version: 1.0.0
---

First check: **is a CMF Server already available?**

Ask the user whether a teammate or administrator has already deployed a CMF Server. If yes, and they have the server URL and credentials, skip to [Connecting to an existing CMF Server](#connecting-to-an-existing-cmf-server).

If not, guide the user through a local Docker Compose deployment below.

## Prerequisites (local deployment)

- Docker Engine with Docker Compose plugin installed
- Git (to clone the CMF repository)
- Ports 80 and 443 free on the host (configurable)
- The host machine's IP address or hostname (for `REACT_APP_CMF_API_URL`)

## Step 1 — Clone the CMF repository

```bash
git clone https://github.com/HewlettPackard/cmf
cd cmf
```

## Step 2 — Create the `.env` file

The `docker-compose-server.yml` file reads configuration from a `.env` file in the same directory. Create it:

```bash
cat > .env << 'EOF'
# Data storage — where PostgreSQL, TensorBoard logs, and uploaded files live.
# Use an absolute path for production deployments.
CMF_DATA_DIR=./data

# Nginx port bindings
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# The URL clients and the UI use to reach the CMF API.
# Replace with your server's IP or hostname. Must be reachable from browsers and cmflib clients.
REACT_APP_CMF_API_URL=http://<your-server-ip>:80

# PostgreSQL credentials (change from defaults in production)
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mlmd
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MCP server — external port for the CMF MCP server (default 8382)
MCP_EXTERNAL_PORT=8382
EOF
```

### Key `.env` variables explained

| Variable | Default | Purpose |
|----------|---------|---------|
| `CMF_DATA_DIR` | `./data` | Host path for all persistent data (PostgreSQL, logs, uploads) |
| `NGINX_HTTP_PORT` | `80` | Host port for HTTP traffic |
| `NGINX_HTTPS_PORT` | `443` | Host port for HTTPS traffic |
| `REACT_APP_CMF_API_URL` | _(required)_ | Full URL clients use to reach the API — must match actual host address |
| `POSTGRES_USER` | `myuser` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `mypassword` | PostgreSQL password — **change this in production** |
| `POSTGRES_DB` | `mlmd` | Database name |
| `MCP_EXTERNAL_PORT` | `8382` | Host port mapped to the CMF MCP server |

### Common `.env` customizations

**Use a non-standard port (if 80 is taken):**
```env
NGINX_HTTP_PORT=8080
REACT_APP_CMF_API_URL=http://<your-server-ip>:8080
```

**Store data on a specific volume or NFS mount:**
```env
CMF_DATA_DIR=/mnt/nfs/cmf-data
```

**Expose PostgreSQL externally (uncomment the ports section in docker-compose-server.yml):**
```env
POSTGRES_PORT=5432
```

## Step 3 — Build and start the containers

```bash
docker compose -f docker-compose-server.yml up -d
```

This starts five services:

| Service | Role |
|---------|------|
| `postgres` | Metadata database (starts first) |
| `server` | CMF API server (waits for postgres health check) |
| `ui` | React web interface (waits for server health check) |
| `tensorboard` | Training metrics visualization |
| `nginx` | Reverse proxy on ports 80/443 |
| `mcp` | CMF MCP server on `MCP_EXTERNAL_PORT` |

Check that all containers are healthy:

```bash
docker compose -f docker-compose-server.yml ps
```

All services should show `healthy` or `running` within ~60 seconds.

## Step 4 — Verify the web UI

Open a browser and navigate to:

```
http://<your-server-ip>:80
```

(or whatever port you set in `NGINX_HTTP_PORT`). The CMF web UI should load and show an empty pipelines list.

Verify the API is responding:

```bash
curl http://<your-server-ip>:80/apiv1.0/pipelines
# {"pipelines": []}
```

## Step 5 — Point cmflib clients at this server

On each client machine that will push/pull metadata, run `cmf init` with the `--cmf-server-url` flag pointing at this server:

```bash
cmf init local \
  --path /path/to/artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git \
  --cmf-server-url http://<your-server-ip>:80
```

Confirm the client is configured:

```bash
cmf init show
# Should show CMF Server URL: http://<your-server-ip>:80
```

Push a pipeline's metadata to verify end-to-end:

```bash
cmf metadata push -p my_pipeline
```

---

## Connecting to an existing CMF Server

If a CMF Server is already running, skip the Docker setup entirely and just point your local CMF client at it.

### Configure the client

```bash
# Re-initialize CMF with the server URL (keeps existing storage backend config)
cmf init local \
  --path /path/to/artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git \
  --cmf-server-url http://<server-url>:<port>
```

Or, if CMF is already initialized and you only want to update the server URL, re-run `cmf init` — it will update the configuration in place.

### Verify connectivity

```bash
cmf init show   # confirm the server URL is set
cmf pipeline list   # should list pipelines on the remote server (after a pull)
cmf metadata pull -p my_pipeline   # fetch a pipeline's metadata to confirm access
```

### What credentials are needed?

The CMF Server does not use username/password authentication by default. Access is controlled at the network level (firewall rules, VPN). If your organization has added an authentication layer in front of the server (e.g. Nginx basic auth or an SSO proxy), ask your administrator for the necessary credentials or token and configure them in your HTTP client or `~/.netrc`.

---

## Stopping and managing the server

```bash
# Stop containers (data is preserved)
docker compose -f docker-compose-server.yml stop

# Start again
docker compose -f docker-compose-server.yml start

# Remove containers (data in CMF_DATA_DIR is preserved)
docker compose -f docker-compose-server.yml down

# Remove containers AND all data (destructive — backup first)
docker compose -f docker-compose-server.yml down -v
rm -rf ./data
```

## Upgrading the server

After pulling a new version of the CMF repository, rebuild images before restarting:

```bash
git pull
docker compose -f docker-compose-server.yml build --no-cache
docker compose -f docker-compose-server.yml up -d
```

## Troubleshooting

- **`REACT_APP_CMF_API_URL` not set**: The `server` and `ui` containers will fail to start. This variable is required — set it to the server's actual IP or hostname.
- **Port 80 already in use**: Change `NGINX_HTTP_PORT` in `.env` and update `REACT_APP_CMF_API_URL` to match.
- **`postgres` container not healthy**: Check PostgreSQL logs with `docker compose -f docker-compose-server.yml logs postgres`. Usually a permission issue with `CMF_DATA_DIR`.
- **UI loads but API calls fail**: `REACT_APP_CMF_API_URL` must be reachable from the browser, not just the Docker network. Use the host machine's IP, not `localhost`, when accessing from other machines.
- **MCP server not reachable**: Check `MCP_EXTERNAL_PORT` in `.env` and confirm it is not blocked by a firewall. Test with `curl http://<server-ip>:<MCP_EXTERNAL_PORT>/health`.
- **Clients cannot push metadata**: Confirm `cmf init show` shows the correct server URL. Ensure the server port is reachable from the client (`curl http://<server-ip>:80/apiv1.0/pipelines`).

## Further reading

- `docs/setup/index.md` — Full installation guide with Docker prerequisites
- `docs/cmf_client/index.md` — CMF Client CLI guide and push/pull workflow
- `docs/ui/index.md` — Web UI reference
- `docs/mcp/index.md` — CMF MCP server (included in docker-compose-server.yml)
