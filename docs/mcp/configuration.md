# Configuration Guide

This guide covers all configuration options for the CMF MCP Server, including environment variables, multi-server setup, and advanced deployment scenarios.

## Environment Variables

The MCP Server is configured primarily through environment variables, which can be set in a `.env` file or passed directly to the Docker container.

### Required Configuration

#### CMF_BASE_URL

The base URL of your primary CMF Server.

**Required**: Yes

**Format**: `http://host:port` or `https://host:port`

**Examples**:

=== "Local Development"
    ```env
    CMF_BASE_URL=http://localhost:8080
    ```

=== "Docker Compose"
    ```env
    CMF_BASE_URL=http://server:8080
    ```

=== "Remote Server"
    ```env
    CMF_BASE_URL=https://cmf-prod.example.com
    ```

!!! warning "Docker Network Names"
    When running in Docker Compose, use the service name from `docker-compose.yml` (e.g., `http://server:8080`) instead of `localhost`.

### Optional Configuration

#### Additional CMF Servers

Connect to multiple CMF Servers for cross-environment queries.

**Required**: No

**Variables**:
- `CMF2_BASE_URL` - Secondary CMF Server
- `CMF3_BASE_URL` - Tertiary CMF Server
- `CMF4_BASE_URL` - Quaternary CMF Server

**Example**:

```env
# Primary server (production)
CMF_BASE_URL=http://cmf-prod:8080

# Development server
CMF2_BASE_URL=http://cmf-dev:8080

# Staging server
CMF3_BASE_URL=http://cmf-staging:8080

# Test environment
CMF4_BASE_URL=http://cmf-test:8080
```

**Use Cases**:
- Compare artifacts across environments
- Aggregate metadata from multiple teams
- Unified view of development and production pipelines

#### CMF_TLS_VERIFY

Controls TLS/SSL certificate verification for CMF API requests over HTTPS.

**Required**: No

**Default**: `false` (CMF server typically runs on HTTP)

**Options**:
- `false` - Disable verification (default, suitable for HTTP or self-signed HTTPS)
- `true` - Verify certificates using system CA bundle
- `/path/to/ca-bundle.crt` - Use custom CA bundle file

**Examples**:

=== "Default (HTTP or Self-Signed)"
    ```env
    CMF_TLS_VERIFY=false
    # OR omit the variable to use default
    ```

=== "Production HTTPS with Valid Certs"
    ```env
    CMF_TLS_VERIFY=true
    ```

=== "Custom CA Bundle"
    ```env
    CMF_TLS_VERIFY=/etc/ssl/certs/company-ca-bundle.crt
    ```

!!! info "HTTP vs HTTPS"
    CMF server typically runs on HTTP (e.g., `http://server:8080`), so TLS verification is not applicable. Only configure this when using HTTPS URLs.

!!! tip "Best Practice"
    For production HTTPS deployments with properly signed certificates, set `CMF_TLS_VERIFY=true` to enable certificate validation. If using internal CAs, specify the CA bundle path.

#### MCP_HOST

The host interface the MCP Server binds to.

**Required**: No

**Default**: `0.0.0.0`

**Examples**:

```env
# Listen on all interfaces (default)
MCP_HOST=0.0.0.0

# Listen only on localhost
MCP_HOST=127.0.0.1
```

!!! tip "Security"
    In production, consider using `127.0.0.1` and proxying through Nginx for better security control.

#### MCP_PORT

The port the MCP Server listens on.

**Required**: No

**Default**: `8000`

**Example**:

```env
MCP_PORT=8000
```

#### MCP_TRANSPORT_SECURITY

Controls DNS rebinding protection for the MCP server.

**Required**: No

**Default**: `disabled`

**Options**:
- `disabled` - Disable DNS rebinding protection (recommended for Docker/proxy setups)
- `enabled` - Enable DNS rebinding protection with allowed hosts/origins

**Example**:

=== "Disabled (Docker/Proxy)"
    ```env
    MCP_TRANSPORT_SECURITY=disabled
    ```

=== "Enabled (Direct Access)"
    ```env
    MCP_TRANSPORT_SECURITY=enabled
    MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,myserver.com:8000
    MCP_ALLOWED_ORIGINS=http://localhost:*,http://127.0.0.1:*
    ```

!!! info "When to Enable"
    Only enable transport security when the MCP Server is directly exposed to the internet. For Docker deployments behind Nginx, keep it disabled.

#### MCP_ALLOWED_HOSTS

Comma-separated list of allowed hosts when transport security is enabled.

**Required**: Only if `MCP_TRANSPORT_SECURITY=enabled`

**Format**: Supports wildcard ports with `*`

**Example**:

```env
MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*,cmf.example.com:8000
```

#### MCP_ALLOWED_ORIGINS

Comma-separated list of allowed origins when transport security is enabled.

**Required**: Only if `MCP_TRANSPORT_SECURITY=enabled`

**Format**: Full origin URLs with protocol

**Example**:

```env
MCP_ALLOWED_ORIGINS=http://localhost:*,https://cmf.example.com
```

## Configuration Files

### .env File

Create a `.env` file in the `cmf/mcp` directory for local development:

```bash
cp example.env .env
```

**Example `.env`**:

```env
###
# CMF MCP Server Configuration
###

# Primary CMF Server (required)
CMF_BASE_URL=http://localhost:8080

# Additional CMF Servers (optional)
# CMF2_BASE_URL=http://cmf-server-2:8080
# CMF3_BASE_URL=http://cmf-server-3:8080
# CMF4_BASE_URL=http://cmf-server-4:8080

# MCP Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Transport Security (disabled for Docker/proxy setups)
MCP_TRANSPORT_SECURITY=disabled
```

### Docker Compose Configuration

The MCP Server configuration is integrated into `docker-compose-server.yml`.

**Location**: `cmf/docker-compose-server.yml`

**MCP Service Configuration**:

```yaml
services:
  mcp:
    image: mcp:latest
    container_name: cmf-mcp-server
    build:
      context: ./
      dockerfile: ./mcp/Dockerfile
    environment:
      # Primary CMF Server
      CMF_BASE_URL: ${CMF_BASE_URL:-http://server:8080}
      
      # Additional servers (if configured)
      CMF2_BASE_URL: ${CMF2_BASE_URL:-}
      CMF3_BASE_URL: ${CMF3_BASE_URL:-}
      CMF4_BASE_URL: ${CMF4_BASE_URL:-}
      
      # MCP Server settings
      MCP_HOST: ${MCP_HOST:-0.0.0.0}
      MCP_PORT: ${MCP_PORT:-8000}
      MCP_TRANSPORT_SECURITY: ${MCP_TRANSPORT_SECURITY:-disabled}
    
    ports:
      - "8382:8000"
    
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000 || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 30s
    
    depends_on:
      server:
        condition: service_healthy
    
    networks:
      - cmf_network
```

**Key Features**:
- **Environment Variables**: Pulled from `.env` file with defaults
- **Health Checks**: Ensures MCP Server is responding before marking as healthy
- **Dependencies**: Waits for CMF Server to be healthy before starting
- **Networking**: Connected to CMF network for service discovery

## Multi-Server Setup

Configure multiple CMF Servers to query across environments.

### Scenario: Dev, Staging, Production

**Goal**: Query metadata from development, staging, and production environments.

**Configuration** (`.env`):

```env
# Production (primary)
CMF_BASE_URL=http://cmf-prod.internal:8080

# Staging
CMF2_BASE_URL=http://cmf-staging.internal:8080

# Development
CMF3_BASE_URL=http://cmf-dev.internal:8080
```

**Usage**:

When AI assistants query, they can target specific servers or query all:

```
# Query all environments
"What pipelines exist across all CMF servers?"

# Query specific environment
"Show me models in the production CMF server"
```

### Scenario: Multi-Team Setup

**Goal**: Aggregate metadata from different team CMF Servers.

**Configuration**:

```env
CMF_BASE_URL=http://team-ml.internal:8080
CMF2_BASE_URL=http://team-data.internal:8080
CMF3_BASE_URL=http://team-research.internal:8080
```

**Benefits**:
- Cross-team metadata discovery
- Unified artifact search
- Collaborative lineage analysis

## Health Checks

The MCP Server includes built-in health checks to ensure proper operation.

### Docker Health Check

**Configuration** (in `docker-compose-server.yml`):

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000 || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 30s
```

**Health Check Process**:

1. Waits 30 seconds after container start (start_period)
2. Checks every 15 seconds (interval)
3. Times out after 5 seconds (timeout)
4. Marks unhealthy after 5 failed attempts (retries)

**Viewing Health Status**:

```bash
# Check health status
docker-compose -f docker-compose-server.yml ps

# Expected output:
# NAME              STATUS
# cmf-mcp-server    Up (healthy)
```

### Manual Health Check

Test the health endpoint directly:

```bash
# Check if MCP Server is responding
curl http://localhost:8382/mcp

# Check from inside Docker network
docker exec cmf-mcp-server curl -f http://localhost:8000
```

## Network Configuration

### Docker Network Setup

The MCP Server communicates with the CMF Server over a Docker network.

**Network**: `cmf_network` (defined in `docker-compose-server.yml`)

**Service Discovery**:
- CMF Server: `http://server:8080`
- MCP Server: `http://mcp:8000`
- Database: `http://db:3306` or `http://db:5432`

### Port Mapping

**Internal Port**: 8000 (inside container)

**External Port**: 8382 (on host)

**Access Methods**:

| Method | URL | Use Case |
|--------|-----|----------|
| Direct | `http://localhost:8382/mcp` | MCP client connections |
| Via Nginx | `http://localhost/mcp` | Web-based access |

**Custom Port Mapping**:

Edit `docker-compose-server.yml`:

```yaml
ports:
  - "9000:8000"  # Map to port 9000 instead
```

## Security Considerations

### Network Isolation

**Production Recommendation**: Use Docker networks to isolate the MCP Server.

```yaml
networks:
  cmf_network:
    internal: true  # No external access
  
  proxy_network:
    internal: false  # External access via proxy only
```

**MCP Server**:
```yaml
networks:
  - cmf_network      # Access CMF Server
  - proxy_network    # Access via Nginx
```

### Authentication

The MCP Server currently relies on network-level security.

**Recommended Approaches**:

1. **Reverse Proxy Authentication**:
   - Use Nginx with HTTP basic auth
   - Configure OAuth2 proxy

2. **Network Security**:
   - Deploy in private network
   - Use VPN for remote access
   - Configure firewall rules

3. **API Keys** (future enhancement):
   - Token-based authentication
   - Role-based access control

### Transport Security

**TLS/HTTPS**:

For production deployments, use HTTPS:

```yaml
# Nginx configuration
server {
    listen 443 ssl;
    server_name cmf.example.com;
    
    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    
    location /mcp {
        proxy_pass http://mcp:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Configuration Issues

#### MCP Server Can't Connect to CMF Server

**Symptom**: Health checks fail, logs show connection errors

**Solutions**:

1. **Verify CMF_BASE_URL**:
   ```bash
   # Check environment variable
   docker exec cmf-mcp-server env | grep CMF_BASE_URL
   ```

2. **Test network connectivity**:
   ```bash
   # From MCP container
   docker exec cmf-mcp-server curl http://server:8080
   ```

3. **Check CMF Server status**:
   ```bash
   docker-compose -f docker-compose-server.yml ps server
   ```

#### Port Conflicts

**Symptom**: `Error: Address already in use`

**Solution**: Change the external port mapping:

```yaml
ports:
  - "8383:8000"  # Use different external port
```

#### Health Check Failures

**Symptom**: Container keeps restarting

**Debug Steps**:

1. **Check logs**:
   ```bash
   docker-compose -f docker-compose-server.yml logs mcp
   ```

2. **Disable health check temporarily**:
   ```yaml
   # Comment out healthcheck section for debugging
   # healthcheck:
   #   test: ["CMD-SHELL", "curl -f http://localhost:8000 || exit 1"]
   ```

3. **Verify dependencies**:
   ```bash
   # Ensure CMF Server is healthy first
   docker-compose -f docker-compose-server.yml ps server
   ```

### Performance Tuning

#### Multiple Server Latency

**Issue**: Queries to multiple CMF Servers are slow

**Solutions**:

1. **Limit concurrent servers**:
   - Only configure servers you actively query
   - Remove unused CMF2/CMF3/CMF4 URLs

2. **Use targeted queries**:
   - Specify `cmfClient_instances` parameter
   - Query specific servers instead of all

3. **Cache frequently accessed data** (future enhancement)

#### Resource Limits

Set resource limits in Docker Compose:

```yaml
mcp:
  # ... other configuration ...
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

## Advanced Configuration

### Custom Dockerfile

Extend the MCP Server for custom requirements:

```dockerfile
FROM mcp:latest

# Install additional packages
RUN pip install custom-package

# Add custom configuration
COPY custom_config.py /app/

# Set custom environment
ENV CUSTOM_VAR=value
```

### Custom Tools

Add custom MCP tools by creating new modules in `tools/`:

```python
# tools/custom.py
def register_tools(mcp, cmf_clients):
    @mcp.tool(name="custom_query", description="Custom CMF query")
    def custom_query(param: str) -> List[Dict[str, Any]]:
        result = []
        for url in cmf_clients.keys():
            client = cmf_clients[url]
            # Custom implementation
            data = client.custom_api_call(param)
            result.append({"cmfClient": url, "data": data})
        return result
```

Register in `main.py`:

```python
from tools import custom

# In main()
custom.register_tools(mcp, cmf_clients)
```

## Configuration Best Practices

1. **Use environment-specific .env files**:
   - `.env.dev` for development
   - `.env.staging` for staging
   - `.env.prod` for production

2. **Version control**:
   - ✅ Commit `example.env`
   - ❌ Never commit `.env` with real URLs/credentials

3. **Document your setup**:
   - Maintain README with environment details
   - Document custom configurations

4. **Test configurations**:
   - Verify each CMF Server URL is accessible
   - Test health checks before deployment

5. **Monitor in production**:
   - Set up log aggregation
   - Monitor health check status
   - Track response times

## Next Steps

- **[Quick Start](quickstart.md)** - Deploy with these configurations
- **[Tools Reference](tools.md)** - Understand what the MCP Server can do
- **[Examples](examples.md)** - See multi-server queries in action
