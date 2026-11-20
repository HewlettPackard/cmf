# CMF Server Environment Variables

All variables are set in the `.env` file in the same directory as `docker-compose-server.yml`.

## Optional

| Variable | Example | Purpose |
|----------|---------|---------|
| `REACT_APP_CMF_API_URL` | `http://192.168.1.10:80` | URL the browser uses to fetch API calls from the UI. **Optional**: when unset, the browser uses its own origin (`window.location.origin`), so HTTP and HTTPS both work automatically. Set it only if the API is on a different host than the UI, or a different port. |

## Storage

| Variable | Default | Purpose |
|----------|---------|---------|
| `CMF_DATA_DIR` | `./data` | Host path for all persistent data (PostgreSQL files, TensorBoard logs, uploaded artifacts). Use an absolute path for production. |

## Network / Ports

| Variable | Default | Purpose |
|----------|---------|---------|
| `NGINX_HTTP_PORT` | `80` | Host port for HTTP |
| `NGINX_HTTPS_PORT` | `443` | Host port for HTTPS. nginx auto-generates a throwaway self-signed cert on startup if none is mounted; for a stable cert, run `scripts/generate-self-signed-cert.sh` (or place `cmf.crt` / `cmf.key` in `$CMF_DATA_DIR/nginx-certs/`). |
| `MCP_EXTERNAL_PORT` | `8382` | Host port mapped to the CMF MCP server |

## PostgreSQL

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `myuser` | Database username |
| `POSTGRES_PASSWORD` | `mypassword` | Database password — **change in production** |
| `POSTGRES_DB` | `mlmd` | Database name |
| `POSTGRES_HOST` | `postgres` | Service name (internal Docker network) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |

## MCP (Multi-server)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CMF_BASE_URL` | `http://server:8080` | Primary CMF Server URL (internal) |
| `CMF2_BASE_URL` | — | Optional second CMF Server |
| `CMF3_BASE_URL` | — | Optional third CMF Server |
| `CMF4_BASE_URL` | — | Optional fourth CMF Server |

## Common customizations

**Non-standard HTTP port** (no `REACT_APP_CMF_API_URL` needed — browser uses its own origin):
```env
NGINX_HTTP_PORT=8080
```

**Split front/back-end** (API on a different host — set `REACT_APP_CMF_API_URL`):
```env
REACT_APP_CMF_API_URL=http://192.168.1.10:8080
```

**External data volume:**
```env
CMF_DATA_DIR=/mnt/nfs/cmf-data
```

**Bring-your-own TLS certificate** (instead of the self-signed one):
```env
# Place cmf.crt and cmf.key in $CMF_DATA_DIR/nginx-certs/ before starting.
# No env change required — nginx reads them from the mounted certs dir.
```

**Multi-environment MCP:**
```env
CMF_BASE_URL=http://server:8080
CMF2_BASE_URL=http://staging-server:8080
CMF3_BASE_URL=http://prod-server:8080
```
