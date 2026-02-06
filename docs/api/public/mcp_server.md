# CMF MCP Server

## Overview

The CMF MCP Server is a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes CMF Server functionality as tools and resources that can be used by AI assistants and language models. This enables LLMs to interact directly with your CMF infrastructure to query pipelines, executions, artifacts, and more.

## Architecture

The MCP Server is a separate service that communicates with the CMF Server API. It translates AI assistant requests into CMF API calls and returns the results in a structured format suitable for AI processing.

```
AI Assistant (e.g., Claude, VSCode Copilot)
    ↓
MCP Server (Port 8000)
    ↓
CMF Server (Port 8080)
```

## Configuration

The MCP Server is configured via environment variables. The following options are available:

### Primary CMF Server (Required)

- `CMF_BASE_URL`: The base URL of your primary CMF Server (e.g., `http://server:8080`)

### Additional CMF Servers (Optional)

You can configure up to 3 additional CMF servers:

- `CMF2_BASE_URL`: Secondary CMF Server URL
- `CMF3_BASE_URL`: Tertiary CMF Server URL
- `CMF4_BASE_URL`: Quaternary CMF Server URL

## API

### Tools

The MCP Server exposes the following tools that can be called by AI assistants:

#### Pipeline Tools

- **`cmf_show_pipelines`**: Lists all pipelines in the configured CMF Server(s)

#### Execution Tools

- **`cmf_show_executions`**: Lists all executions for a given pipeline
- **`cmf_show_executions_list`**: Returns a brief list of execution names for a pipeline
- **`cmf_execution_lineage`**: Fetch execution lineage for a specific execution UUID and pipeline

#### Artifact Tools

- **`cmf_show_artifact_types`**: Lists all artifact types available in CMF Server(s)
- **`cmf_show_artifacts`**: Retrieve artifacts of a specific type for a given pipeline
- **`cmf_artifact_lineage`**: Fetch artifact lineage tree for a pipeline

#### Additional Tools

- **`cmf_show_model_card`**: Retrieve the model card for a Model Artifact (identified by ID)

### Tool Response Format

All tools return results as a list of dictionaries with the following structure:

```json
[
  {
    "cmfClient": "http://cmf-server-url",
    "data": [ ... ]  // Result data from CMF Server
  }
]
```

## Usage

### Docker Deployment

The MCP Server is automatically deployed as part of the CMF Docker Compose stack when using `docker-compose-server.yml`.

```bash
# Start the full stack including MCP Server
docker compose -f docker-compose-server.yml up -d

# View MCP Server logs
docker compose -f docker-compose-server.yml logs -f mcp
```

### Connecting to the MCP Server

Once deployed, the MCP Server can be accessed via two endpoints:

| Access Method | URL | Use Case |
|---------------|-----|----------|
| **Via Nginx (port 80)** | `http://<host>/mcp` | When accessing through the main CMF web interface |
| **Direct (port 8382)** | `http://<host>:8382/mcp` | Direct access to the MCP container |

Replace `<host>` with your server's hostname or IP address (e.g., `localhost`, `10.93.232.86`).

!!! tip "Recommended"
    Use the direct port `8382` for MCP client connections as it provides the most reliable connectivity.

### VSCode with GitHub Copilot

To use the MCP Server with GitHub Copilot in VSCode:

1. Create a `.vscode` directory in your project root
2. Add the following configuration to `.vscode/mcp.json`:

```json
{
  "servers": {
    "cmf-mcp-server": {
      "type": "http",
      "url": "http://<host>:8382/mcp"
    }
  }
}
```

Replace `<host>` with your CMF server's hostname or IP address.

3. Reload VSCode or restart the Copilot extension
4. Copilot will now have access to CMF tools and can query your metadata

### Claude Desktop

To use with Claude Desktop:

1. Update your Claude Desktop configuration (usually at `~/.claude_desktop_config.json`)
2. Add the MCP Server entry for HTTP transport:

```json
{
  "mcpServers": {
    "cmf-mcp": {
      "transport": "streamable-http",
      "url": "http://<host>:8382/mcp"
    }
  }
}
```

Replace `<host>` with your CMF server's hostname or IP address.

3. Restart Claude Desktop

### Cursor IDE

To use with Cursor IDE:

1. Open Cursor Settings → Features → MCP Servers
2. Add a new server with the following configuration:
   - **Name**: `cmf-mcp-server`
   - **Type**: `http`
   - **URL**: `http://<host>:8382/mcp`

Replace `<host>` with your CMF server's hostname or IP address.

## Project Structure

```
mcp/
├── main.py              # Main application entry point
├── tools/               # MCP CMF tools organized by functionality
│   ├── __init__.py
│   ├── pipeline.py      # Pipeline-related tools
│   ├── execution.py     # Execution-related tools
│   ├── artifact.py      # Artifact-related tools
│   └── additional.py    # Additional / Miscellaneous tools
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
└── Dockerfile           # Docker build configuration
```

## Development

### Local Setup

To develop the MCP Server locally:

1. Install dependencies:
```bash
pip install -r mcp/requirements.txt
```

2. Set environment variables:
```bash
export CMF_BASE_URL=http://localhost:8080
```

3. Run the server:
```bash
python mcp/main.py
```

The server will be available at `http://localhost:8000`

### Testing with MCP Inspector

To test tools and resources interactively:

```bash
pip install mcp-inspector
mcp-inspector python /path/to/cmf/mcp/main.py
```

This opens an interactive interface at `http://localhost:6274` where you can test individual tools.

## Integration with Other Platforms

The MCP Server can be integrated with various AI platforms and tools:

- **n8n**: Add an HTTP node pointing to the MCP Server
- **Langflow**: Use the MCP Server integration
- **Claude Desktop**: Direct MCP server integration
- **VSCode/Cursor**: SSE-based connection through MCP config
- **Custom Tools**: Use the HTTP/SSE interface directly

## Health Checks

The MCP Server includes a health check endpoint that monitors its connection to the CMF Server. In Docker Compose, it will not be considered healthy until it can successfully communicate with the upstream CMF Server.

## Troubleshooting

### Connection Issues

If the MCP Server cannot connect to CMF:

1. Verify `CMF_BASE_URL` is set correctly
2. Check that the CMF Server is running and healthy
3. Check network connectivity between containers (in Docker environments)

### Tool Failures

If a tool returns an error:

1. Check the MCP Server logs: `docker-compose logs mcp`
2. Verify the required parameters are provided
3. Check that the resource exists on the CMF Server (e.g., pipeline name is correct)

### Performance

For better performance with multiple CMF Servers:

1. Limit the number of additional CMF Servers to those actually needed
2. Monitor the MCP Server resource usage
3. Consider caching frequently accessed data

## License

Licensed under the Apache License 2.0. See LICENSE file for details.
