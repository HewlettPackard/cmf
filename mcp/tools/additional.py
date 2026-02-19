"""
CMF MCP Additional tools
"""

from typing import List, Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

def register_tools(mcp, cmf_clients):
    """Register additional tools for Common Metadata Framework (CMF) with the MCP server."""

    @mcp.tool(name="cmf_show_model_card", description="Retrieve the model card for a Model Artifact type (identified by its ID) from Common Metadata Framework (CMF) server")
    def cmf_show_model_card(model_id: str, cmfClient_instances: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the model card for a Model Artifact in CMF Server(s)
        This requires that the model_id provided is a valid ID of a Model Artifact type on the CMF server.
        Can run cmf_show_artifacts tool with artifact_type="Model" to find out "id" of the artifact on Common Metadata Framework (CMF) server.
        Can run cmf_show_artifact_types tool to validate that Model artifact type exists on the Common Metadata Framework (CMF) server.
        
        Args:
            model_id: ID of the model artifact to retrieve the model card for (Obtained as string).
            cmfClient_instances: Optional list of cmfClient_instances to query. If None, query all configured cccAPI_instances.
        
        Output: 
            4 JSON payloads (Pandas dataframes) in a List containing the model card data for each Model queried on the CMF server.
            The sections are: Model Data, Model Execution, Model Input Artifacts and Model Output Artifacts
        """
        result = []
        
        # Determine which ccc_instances to query
        targets = cmf_clients.keys() if cmfClient_instances is None else [p for p in cmfClient_instances if p in cmf_clients]
        
        for url in targets:
            client = cmf_clients[url]
            try:
                data = client.get_model_card(model_id)
                result.append({"cmfClient": url, "data": data})
                # The response is 4 JSON payloads (Pandas dataframes) in a List corresponding to the 4 sections of the Model card: 
                # Model Data, Model Execution, Model Input Artifacts, Model Output Artifacts
                # Each of these dataframes can be converted to JSON format using the json.dumps function.
                logger.debug(json.dumps(data, indent=4))
            except Exception as e:
                result.append({"cmfClient": url, "error": str(e)})
        
        return result
