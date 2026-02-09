# Quick Start Guide

This guide will help you get the CMF MCP Server up and running in minutes.

## Prerequisites

Before you begin, ensure you have:

- A running CMF Server instance (see [Installation & Setup](../setup/index.md))
- Docker and Docker Compose (for containerized deployment)
- Python 3.10+ (for local development)

## Docker Deployment (Recommended)

The easiest way to run the MCP Server is as part of the CMF Docker Compose stack.

### Start the Stack

The MCP Server is automatically deployed when you start the full CMF stack:

```bash
# Start all services including MCP Server
docker-compose -f docker-compose-server.yml up -d
```

### Verify Deployment

Check that all services are running:

```bash
# View service status
docker-compose -f docker-compose-server.yml ps

# Check MCP Server logs
docker-compose -f docker-compose-server.yml logs -f mcp
```

You should see output indicating the MCP Server is running:

```
cmf-mcp-server | INFO:     Started server process
cmf-mcp-server | INFO:     Waiting for application startup.
cmf-mcp-server | INFO:     Application startup complete.
cmf-mcp-server | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Access Endpoints

Once deployed, the MCP Server is accessible via two endpoints:

| Method | URL | Use Case |
|--------|-----|----------|
| **Via Nginx** | `http://localhost/mcp` | Access through CMF web interface |
| **Direct** | `http://localhost:8382/mcp` | Direct MCP client connections (recommended) |

!!! tip "Recommended Access Method"
    Use the direct port `8382` for MCP client connections as it provides the most reliable connectivity.

### Stop the Stack

```bash
docker-compose -f docker-compose-server.yml down
```

## Local Development

For development or testing, you can run the MCP Server locally outside of Docker.

### Install Dependencies

```bash
# Navigate to the MCP directory
cd cmf/mcp

# Install Python dependencies
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file from the example:

```bash
cp example.env .env
```

Edit `.env` to set your CMF Server URL:

```env
# Primary CMF Server (required)
CMF_BASE_URL=http://localhost:8080
```

See [Configuration](configuration.md) for more environment variables.

### Run the Server

```bash
python main.py
```

The server will start on `http://localhost:8000` In the compose image, it is redirected to either : `http://localhost:8382/mcp` OR `http://localhost/mcp`

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Connecting AI Assistants

Once the MCP Server is running, you can connect it to your AI assistant.

### GitHub Copilot (VSCode)

=== "VSCode Configuration"

    1. Create `.vscode/mcp.json` in your workspace:

    ```json
    {
      "servers": {
        "cmf-mcp-server": {
          "type": "http",
          "url": "http://localhost:8382/mcp"
        }
      }
    }
    ```

    2. Reload VSCode or restart the Copilot extension

    3. Copilot will now have access to CMF tools

=== "Remote Server"

    If your CMF Server is on a remote machine:

    ```json
    {
      "servers": {
        "cmf-mcp-server": {
          "type": "http",
          "url": "http://YOUR_SERVER_IP:8382/mcp"
        }
      }
    }
    ```

    Replace `YOUR_SERVER_IP` with your server's IP address.

### Claude Desktop

=== "macOS/Linux"

    1. Edit `~/.claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "cmf-mcp": {
          "transport": "streamable-http",
          "url": "http://localhost:8382/mcp"
        }
      }
    }
    ```

    2. Restart Claude Desktop

=== "Windows"

    1. Edit `%APPDATA%\Claude\claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "cmf-mcp": {
          "transport": "streamable-http",
          "url": "http://localhost:8382/mcp"
        }
      }
    }
    ```

    2. Restart Claude Desktop

### Cursor IDE

1. Open Cursor Settings → Features → MCP Servers
2. Add a new server:
   - **Name**: `cmf-mcp-server`
   - **Type**: `http`
   - **URL**: `http://localhost:8382/mcp`
3. Save and reload Cursor

## Testing the Connection

### Using MCP Inspector

Test your MCP Server interactively with the MCP Inspector tool:

```bash
# Install MCP Inspector
pip install mcp-inspector

# Test the server
mcp-inspector python /path/to/cmf/mcp/main.py
```

This opens an interactive interface at `http://localhost:6274` where you can:

- View available tools
- Test tool calls with sample parameters
- Inspect responses

### Using Your AI Assistant

Try these example queries in your AI assistant:

```
What pipelines are available in CMF?
```

```
Show me executions for the Test-env pipeline
```

```
List all artifact types in the CMF Server
```

If the MCP Server is connected correctly, your AI assistant will use the CMF tools to answer these questions.

## Troubleshooting

### MCP Server Won't Start

**Check logs**:
```bash
docker-compose -f docker-compose-server.yml logs mcp
```

**Common issues**:

- `CMF_BASE_URL` not set or incorrect
  - Solution: Verify the environment variable in your `.env` or `docker-compose-server.yml`

- CMF Server not running or not healthy
  - Solution: Check CMF Server status with `docker-compose ps`

- Port 8000 already in use
  - Solution: Change `MCP_PORT` in your configuration

### Connection Issues

If AI assistants can't connect:

1. **Verify the MCP Server is accessible**:
   ```bash
   curl http://localhost:8382/mcp
   ```

2. **Check firewall settings** if accessing remotely

3. **Ensure correct URL** in your AI assistant configuration

4. **Review AI assistant logs** for connection errors

### Tools Return Errors

If tools execute but return errors:

1. **Verify parameters** - Check that pipeline names and IDs exist
2. **Test directly** - Use MCP Inspector to isolate the issue
3. **Check CMF Server** - Ensure the CMF Server API is responding
4. **Review logs** - Look for detailed error messages in MCP Server logs

### Network Issues in Docker

If the MCP Server can't reach the CMF Server:

1. **Check Docker network**:
   ```bash
   docker network inspect cmf_default
   ```

2. **Use service names** - In Docker Compose, use `http://server:8080` not `http://localhost:8080`

3. **Verify health checks**:
   ```bash
   docker-compose -f docker-compose-server.yml ps
   ```

## Next Steps

Now that your MCP Server is running:

- **[Configuration](configuration.md)** - Learn about advanced configuration options
- **[Tools Reference](tools.md)** - Explore all available CMF tools
- **[Examples](examples.md)** - See real-world usage examples and integration patterns
