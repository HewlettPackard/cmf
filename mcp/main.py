###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware.cors import CORSMiddleware
from tools.cmfclient import cmfClient
import os
import tomli
from dotenv import load_dotenv
import uvicorn
import contextlib
 
from pathlib import Path
import atexit
import signal
import sys
import logging

# Import modular components
from tools import pipeline, execution, artifact, additional

# Setup logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("cmf-mcp")

# Load environment variables from .env file
load_dotenv()

# Get version from pyproject.toml
def get_version() -> str:
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
            return pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError, tomli.TOMLDecodeError):
        # Fallback version if we can't read from pyproject.toml
        return "0.0.0"

# Get host and port configuration
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

# Get transport security configuration from environment
# Options:
#   "disabled" - Disable DNS rebinding protection (for Docker/proxy with port mapping)
#   "enabled" - Enable DNS rebinding protection with custom allowed hosts
MCP_TRANSPORT_SECURITY = os.getenv("MCP_TRANSPORT_SECURITY", "disabled").lower()
MCP_ALLOWED_HOSTS = os.getenv("MCP_ALLOWED_HOSTS", "")
MCP_ALLOWED_ORIGINS = os.getenv("MCP_ALLOWED_ORIGINS", "")


def get_transport_security_settings() -> TransportSecuritySettings:
    """
    Get TransportSecuritySettings based on environment configuration.
    
    Uses the official MCP SDK TransportSecuritySettings class for proper
    DNS rebinding protection configuration.
    
    Environment variables:
        MCP_TRANSPORT_SECURITY: "disabled" or "enabled" (default: disabled)
        MCP_ALLOWED_HOSTS: Comma-separated list of allowed hosts with optional wildcard ports
                          e.g., "localhost:*,127.0.0.1:*,myserver.com:8000"
        MCP_ALLOWED_ORIGINS: Comma-separated list of allowed origins
                            e.g., "http://localhost:*,http://127.0.0.1:*"
    """
    if MCP_TRANSPORT_SECURITY == "disabled":
        logger.info("MCP transport security: DISABLED (DNS rebinding protection off)")
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        )
    
    # Parse allowed hosts and origins
    allowed_hosts = [h.strip() for h in MCP_ALLOWED_HOSTS.split(",") if h.strip()] if MCP_ALLOWED_HOSTS else []
    allowed_origins = [o.strip() for o in MCP_ALLOWED_ORIGINS.split(",") if o.strip()] if MCP_ALLOWED_ORIGINS else []
    
    # Use defaults if not specified
    if not allowed_hosts:
        allowed_hosts = ["localhost:*", "127.0.0.1:*"]
    if not allowed_origins:
        allowed_origins = ["http://localhost:*", "http://127.0.0.1:*"]
    
    logger.info(f"MCP transport security: ENABLED")
    logger.info(f"  Allowed hosts: {allowed_hosts}")
    logger.info(f"  Allowed origins: {allowed_origins}")
    
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )

# Create MCP server
mcp = FastMCP(
    "cmf-mcp-server",
    instructions="You are a helpful assistant that can help with Common Metadata Framework (CMF) server tasks. You can show pipelines, artifacts, executions, and more on a Common Metadata Framework (CMF) server",
)

# Initialize cmf clients based on environment variables
cmf_clients = {}

# Initialize primary CMF (required)
primary_url = os.getenv("CMF_BASE_URL")

if not primary_url:
    raise ValueError("Primary CMF configuration (CMF_BASE_URL) is required")

cmf_clients[primary_url] = cmfClient(primary_url)
print(f"CMF Client initialized for {primary_url}")

# Initialize optional cmf Clients (2-4)
for i in range(2, 5):
    url = os.getenv(f"CMF{i}_BASE_URL")
    if url:
        cmf_clients[url] = cmfClient(url)
        print(f"Additional CMF Client initialized for {url}")


# Flag to track if sessions have been closed
sessions_closed = False

# Function to close all cmf client sessions
def close_cmfAPIClient_sessions():
    global sessions_closed
    
    # Avoid closing sessions more than once
    if sessions_closed:
        return
    
    logger.info("Closing cmfapi client sessions...")
    for url, client in cmf_clients.items():
        try:
            client.close_session()
            logger.info(f"Successfully closed session for cmfapi Server: {url}")
        except Exception as e:
            logger.error(f"Error closing session for cmfapi Server {url}: {e}")
    
    sessions_closed = True


# Register cleanup handlers
atexit.register(close_cmfAPIClient_sessions)

def signal_handler(sig, frame):
    logger.info("Received shutdown signal, cleaning up...")
    close_cmfAPIClient_sessions()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register resources, tools, and prompts
# Tools
pipeline.register_tools(mcp, cmf_clients)
execution.register_tools(mcp, cmf_clients)
artifact.register_tools(mcp, cmf_clients)
additional.register_tools(mcp, cmf_clients)


# Get transport security settings
transport_security_settings = get_transport_security_settings()

# Create StreamableHTTP session manager with security settings
# This is the recommended approach for MCP SDK v1.x with custom transport security
session_manager = StreamableHTTPSessionManager(
    app=mcp._mcp_server,  # Access the underlying low-level server
    json_response=True,    # Use JSON responses (simpler than SSE streams)
    stateless=True,        # Stateless mode for Docker/proxy compatibility
    security_settings=transport_security_settings,
)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Manage the StreamableHTTP session manager lifecycle."""
    async with session_manager.run():
        logger.info("StreamableHTTP session manager started")
        try:
            yield
        finally:
            logger.info("StreamableHTTP session manager stopping...")


# Create the ASGI app with StreamableHTTP transport

from starlette.responses import PlainTextResponse
from starlette.routing import Route

async def health(request):
    return PlainTextResponse("OK")

app = Starlette(
    debug=False,
    routes=[
        Mount("/mcp", app=session_manager.handle_request),
        Route("/health", health, methods=["GET"]),
    ],
    lifespan=lifespan,
)

# Add CORS middleware for browser-based clients
app = CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    expose_headers=["Mcp-Session-Id"],
)


def main():
    """Run MCP server with StreamableHTTP transport (recommended for production)."""
    logger.info(f"Starting CMF MCP server on {MCP_HOST}:{MCP_PORT}")
    logger.info(f"Transport: StreamableHTTP (stateless, json_response)")
    logger.info(f"Endpoint: http://{MCP_HOST}:{MCP_PORT}/mcp")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


if __name__ == "__main__":
    logger.info(f"CMF MCP Server configuration:")
    logger.info(f"  Host: {MCP_HOST}")
    logger.info(f"  Port: {MCP_PORT}")
    logger.info(f"  Transport: StreamableHTTP (stateless)")
    logger.info(f"  Security: {MCP_TRANSPORT_SECURITY}")
    main()
