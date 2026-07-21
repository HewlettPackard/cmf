# CMF Server Environment Variables

All variables are set in the `.env` file in the same directory as `docker-compose-server.yml`.

## Required

| Variable | Example | Purpose |
|----------|---------|---------|
| `REACT_APP_CMF_API_URL` | `http://192.168.1.10:80` | URL clients and the browser use to reach the CMF API. Must be reachable from client machines — use the host IP, not `localhost` if accessed remotely. |

## Storage

| Variable | Default | Purpose |
|----------|---------|---------|
| `CMF_DATA_DIR` | `./data` | Host path for all persistent data (PostgreSQL files, TensorBoard logs, uploaded artifacts). Use an absolute path for production. |

## Network / Ports

| Variable | Default | Purpose |
|----------|---------|---------|
| `NGINX_HTTP_PORT` | `80` | Host port for HTTP |
| `NGINX_HTTPS_PORT` | `443` | Host port for HTTPS |
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

**Non-standard HTTP port:**
```env
NGINX_HTTP_PORT=8080
REACT_APP_CMF_API_URL=http://192.168.1.10:8080
```

**External data volume:**
```env
CMF_DATA_DIR=/mnt/nfs/cmf-data
```

**Multi-environment MCP:**
```env
CMF_BASE_URL=http://server:8080
CMF2_BASE_URL=http://staging-server:8080
CMF3_BASE_URL=http://prod-server:8080
```
