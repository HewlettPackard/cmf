# CMF MCP Server

A Model Context Protocol (MCP) server for CMF Server. This server exposes CMF Server functionality as tools that can be used by AI assistants, enabling LLMs to interact directly with your CMF infrastructure.

## Overview

The CMF MCP Server translates AI assistant requests into CMF API calls and returns structured results suitable for AI processing. This allows tools like GitHub Copilot, Claude Desktop, and custom AI applications to query pipelines, executions, artifacts, and more.

## Features

- **Pipeline Tools**: List and explore pipelines in your CMF Server
- **Execution Tools**: Retrieve execution details and lineage information
- **Artifact Tools**: Discover artifact types, retrieve artifacts, and analyze artifact lineage
- **Model Card Tool**: Get model card information for model artifacts
- **Multi-Server Support**: Connect to up to 4 CMF Servers simultaneously
- **Production Ready**: Docker containerization and health checks included

## Architecture

```
AI Assistant (Claude, Copilot, etc.)
    ↓
MCP Server (Port 8000)
    ↓
CMF Server (Port 8080)
```

## Quick Start

### Docker Deployment

The easiest way to run the MCP Server is as part of the CMF Docker Compose stack:

```bash
# Start the full stack with MCP Server
docker-compose -f docker-compose-server.yml up -d

# Check the status
docker-compose -f docker-compose-server.yml ps

# View logs
docker-compose -f docker-compose-server.yml logs -f mcp
```

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp example.env .env
# Edit .env with your CMF Server URL
```

3. **Run the server**:
```bash
python main.py
```

The server will be available at `http://localhost:8000`

## Configuration

### Environment Variables

- **CMF_BASE_URL** (Required): Base URL of your primary CMF Server
  - Example: `http://localhost:8080` or `http://cmf-server:8080`

- **CMF2_BASE_URL** (Optional): Secondary CMF Server
- **CMF3_BASE_URL** (Optional): Tertiary CMF Server  
- **CMF4_BASE_URL** (Optional): Quaternary CMF Server

- **CMF_TLS_VERIFY** (Optional): TLS certificate verification for HTTPS connections
  - Default: `false` (CMF server typically runs on HTTP)
  - Options: `false`, `true`, or path to CA bundle file
  - Set to `true` when using HTTPS with valid certificates

### Example .env

```env
# Primary CMF Server (required)
CMF_BASE_URL=http://server:8080

# Additional servers (optional)
CMF2_BASE_URL=http://cmf-server-2:8080
CMF3_BASE_URL=http://cmf-server-3:8080
CMF4_BASE_URL=http://cmf-server-4:8080
```

## Tools Reference

### Pipeline Tools

#### cmf_show_pipelines
Lists all pipelines available in the configured CMF Server(s).

**Parameters**: None (optional: cmfClient_instances)

**Returns**: List of pipelines with their metadata

**Example**:
```
Get all pipelines from the CMF Server
```

### Execution Tools

#### cmf_show_executions
Retrieves detailed execution information for a specific pipeline.

**Parameters**:
- `pipeline` (string): Name of the pipeline

**Returns**: Detailed execution data

#### cmf_show_executions_list
Lists execution names for a pipeline (brief list).

**Parameters**:
- `pipeline` (string): Name of the pipeline

**Returns**: List of execution names

#### cmf_execution_lineage
Fetches execution lineage for a specific execution UUID.

**Parameters**:
- `pipeline` (string): Name of the pipeline
- `selected_uuid` (string): Execution UUID

**Returns**: Execution lineage tree

### Artifact Tools

#### cmf_show_artifact_types
Lists all artifact types available in CMF Server(s).

**Parameters**: None (optional: cmfClient_instances)

**Returns**: List of artifact types

#### cmf_show_artifacts
Retrieves artifacts of a specific type for a pipeline.

**Parameters**:
- `pipeline` (string): Name of the pipeline
- `artifact_type` (string): Type of artifact (e.g., "Model", "Dataset")

**Returns**: List of artifacts matching the criteria

#### cmf_artifact_lineage
Fetches the complete artifact lineage tree for a pipeline.

**Parameters**:
- `pipeline` (string): Name of the pipeline

**Returns**: Artifact lineage tree showing relationships

### Additional Tools

#### cmf_show_model_card
Retrieves the model card for a specific model artifact.

**Parameters**:
- `model_id` (string): ID of the model artifact

**Returns**: Model card with 4 sections:
- Model Data
- Model Execution  
- Model Input Artifacts
- Model Output Artifacts

## Usage with AI Tools

### GitHub Copilot in VSCode

1. Create `.vscode/mcp.json`:
```json
{
  "servers": {
    "cmf-mcp-server": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

2. Configure VSCode to use this MCP configuration
3. Start using CMF tools in your Copilot interactions

### Claude Desktop

1. Update `~/.claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cmf-mcp": {
      "command": "python",
      "args": ["/path/to/cmf/mcp/main.py"]
    }
  }
}
```

2. Restart Claude Desktop

### Cursor IDE

Similar configuration as VSCode - the MCP Server works with Cursor's built-in AI features.

## Project Structure

```
mcp/
├── main.py              # Application entry point
├── tools/               # Tool implementations
│   ├── __init__.py
│   ├── pipeline.py      # Pipeline-related tools
│   ├── execution.py     # Execution-related tools
│   ├── artifact.py      # Artifact-related tools
│   └── additional.py    # Additional tools (model cards, etc.)
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── Dockerfile           # Docker build configuration
├── .dockerignore        # Docker build exclusions
├── example.env          # Example environment configuration
└── README.md            # This file
```

## Docker Compose Integration

The MCP Server is configured as a service in `docker-compose-server.yml` with:

- Dependency on the main CMF Server service (service_healthy)
- Health checks to ensure the MCP Server is running
- Automatic startup and shutdown with the main stack
- Environment configuration from the main compose file

```yaml
mcp:
  image: mcp:latest
  container_name: cmf-mcp-server
  build:
    context: ./
    dockerfile: ./mcp/Dockerfile
  environment:
    CMF_BASE_URL: ${CMF_BASE_URL:-http://server:8080}
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000 || exit 1"]
    interval: 15s
    timeout: 5s
    retries: 5
    start_period: 30s
  depends_on:
    server:
      condition: service_healthy
```

## Development

### Testing Tools Locally

Use the MCP Inspector to test tools interactively:

```bash
pip install mcp-inspector
mcp-inspector python main.py
```

Opens interactive interface at `http://localhost:6274`

### Adding New Tools

1. Create a new module in `tools/` directory
2. Implement a `register_tools(mcp, cmf_clients)` function
3. Import and call in `main.py`

Example:
```python
# tools/my_tool.py
def register_tools(mcp, cmf_clients):
    @mcp.tool(name="my_tool", description="Does something")
    def my_tool(param: str) -> List[Dict[str, Any]]:
        result = []
        for url in cmf_clients.keys():
            # Implementation
            result.append({"cmfClient": url, "data": ...})
        return result
```

## Troubleshooting

### MCP Server won't start

Check logs:
```bash
docker-compose logs mcp
```

Common issues:
- CMF_BASE_URL not set or incorrect
- CMF Server not running or not healthy
- Port 8000 already in use

### Tools return errors

1. Verify parameter values are correct
2. Check that resources exist (e.g., pipeline names)
3. Ensure CMF Server is running and accessible
4. Check MCP Server logs for detailed error messages

### Performance issues

- Monitor container resource usage
- Consider caching frequently accessed data
- Limit number of additional CMF Servers
- Check network latency between containers

## Deployment Considerations

### Production

- Use environment-specific .env files
- Set resource limits in Docker Compose
- Configure appropriate timeouts
- Monitor MCP Server health
- Set up log aggregation
- Consider load balancing if high volume

### Security

- Keep CMF_BASE_URL internal/private
- Use network security groups to limit access
- Authenticate requests to MCP Server endpoint
- Encrypt credentials in environment variables
- Regular updates of MCP and dependencies

## API Response Format

All tools return responses as a list of dictionaries:

```json
[
  {
    "cmfClient": "http://cmf-server-url",
    "data": [ /* results from CMF Server */ ]
  }
]
```

This allows querying multiple CMF Servers and aggregating results.

## Health Checks

The MCP Server includes health checks that:

1. Verify the MCP Server is running
2. Check connectivity to the CMF Server
3. Ensure all dependencies are working

In Docker Compose, the service is marked as healthy only after successful health checks.

## License

Licensed under the Apache License 2.0. See LICENSE file for details.

## Support

For issues, questions, or feature requests, please refer to the main CMF project documentation at https://github.com/HewlettPackard/cmf
