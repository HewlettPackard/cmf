"""
CMF MCP Execution tools
"""

from typing import List, Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


def register_tools(mcp, cmf_clients):
    """Register execution related tools for Common Metadata Framework (CMF) with the MCP server."""

    @mcp.tool(name="cmf_show_executions", description="Provides Executions details for a given pipeline in CMF server")
    def cmf_show_executions(pipeline: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Show Executions in CMF Server(s)
        Select only one pipeline to show all the executions for it.
        
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
                data = client.get_executions(pipeline)
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result

    @mcp.tool(name="cmf_show_executions_list", description="Lists executions for a Pipeline in CMF Server")
    def cmf_show_executions_list(pipeline: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Lists executions for a Pipeline in CMF Server(s). 
        This tools returns only a brief list of names of executions. 
        Can run cmf_show_executions tool to get ALL details of the executions for a pipeline. 
        
        
        Args:
            pipeline: Name of the pipeline to show executions for
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        
        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_executions_list(pipeline)
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result

    @mcp.tool(name="cmf_execution_lineage", description="Fetch execution lineage for a `selected_uuid` and `specific_pipeline`. Must have run cmf_show_pipelines and validated that `selected_pipeline` exists AND cmf_show_execution_detail to validate that `selected_uuid` before running this.")
    def cmf_execution_lineage(pipeline: str, selected_uuid: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch execution lineage for a `selected_uuid` and `specific_pipeline` for CMF_Server(s). 
        You can run cmf_show_pipelines to validate that `selected_pipeline` exists AND cmf_show_execution_detail to validate `selected_uuid` is an "Execution_uuid" before running this.

        Args:
            pipeline: Name of the pipeline to show executions for.
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        selected_uuid_pared = selected_uuid[:4] #get_execution_lineage_tangled_tree() takes only the first 4 characters of the uuid

        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_execution_lineage_tangled_tree(selected_uuid_pared,pipeline)
                result.append({"cmfClient": url, "data": data})
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result
