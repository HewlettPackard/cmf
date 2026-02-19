"""
CMF MCP Pipeline tools
"""

from typing import List, Dict, Optional, Any
import time
import secrets
import threading
import json
import logging

logger = logging.getLogger(__name__)

def register_tools(mcp, cmf_clients):
    """Register pipeline related tools for Common Metadata Framework (CMF) with the MCP server."""

    @mcp.tool(name="cmf_show_pipelines", description="Lists all Pipelines in Common Metadata Framework (CMF) server")
    def cmf_show_pipelines(cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Show Pipelines in CMF Server(s)
        
        Args:
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        
        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_pipelines()
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result
