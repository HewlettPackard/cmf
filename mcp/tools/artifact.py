"""
CMF MCP Artifact tools
"""

from typing import List, Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

def register_tools(mcp, cmf_clients):
    """Register artifact related tools for Common Metadata Framework (CMF) with the MCP server."""

    @mcp.tool(name="cmf_show_artifact_types", description="Retrieve a list of artifact types on Common Metadata Framework (CMF) server")
    def cmf_show_artifact_types(cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Show Artifact Types in CMF Server(s)
        
        Args:
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        
        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_artifact_types()
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result

    @mcp.tool(name="cmf_show_artifacts", description="Retrieve artifacts of a specific `artifact_type` for a given `pipeline` on Common Metadata Framework (CMF) server")
    def cmf_show_artifacts(pipeline: str, artifact_type: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        This tool retrieves artifacts of a specific `artifact_type` for a given `pipeline` on Common Metadata Framework (CMF) server (s)
        Can run cmf_show_artifact_types tool to validate that a artifact_type is a valid one on the Common Metadata Framework (CMF) server.
        Can run cmf_show_pipelines tool to validate that a pipeline is a valid one on the Common Metadata Framework (CMF) server.
        
        Args:
            pipeline: Name of the pipeline to show artifacts for.
            artifact_type: Type of artifact to retrieve.
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        
        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_artifacts(pipeline, artifact_type)
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result

    @mcp.tool(name="cmf_artifact_lineage", description="Fetch artifact lineage tree for a specific `pipeline` on Common Metadata Framework (CMF) server. Must have run cmf_show_pipelines and validated that requested `pipeline` exists before running this.")
    def cmf_artifact_lineage(pipeline: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        This tool can Fetch artifact lineage tree for a specific `pipeline` on Common Metadata Framework (CMF) Server(s). 
        Can run the tool - cmf_show_pipelines and validate that `selected_pipeline` exists before running this.

        Args:
            pipeline: Name of the pipeline to show executions for.
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]

        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_artifact_lineage_tangled_tree(pipeline)
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result
