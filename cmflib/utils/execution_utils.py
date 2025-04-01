import json
import os
from cmflib import cmfquery, cmf_merger

def create_unique_executions(path: str, req_info: str, cmd: str, exe_uuid: str) -> str:
    """
    Creates a list of unique executions by checking if they already exist on the server or not.
    Locking is introduced to avoid data corruption on the server when multiple similar pipelines are pushed at the same time.

    Args:
        path (str): Path to the MLMD file — server-side for push commands, client-side for pull commands.  
        req_info (str): Contains MLMD data — client-side for push, server-side for pull.  
        cmd (str): The command being executed, either "push" or "pull."  
        exe_uuid (str, optional): User-provided execution UUID (default: None).  

    Returns:
        str: A status message indicating the result of the operation:
            - "exists": Execution already exists on the CMF server.
            - "success": Execution successfully pushed to the CMF server.
            - "invalid_json_payload": If the JSON payload is invalid or incorrectly formatted.
    """
    # Load the MLMD data from the request info
    mlmd_data = json.loads(req_info)
    pipelines = mlmd_data.get("Pipeline", [])
    if not pipelines:
        return "invalid_json_payload"  # No pipelines found in payload

    pipeline = pipelines[0]
    pipeline_name = pipeline.get("name")
    if not pipeline_name:
        return "invalid_json_payload"  # Missing pipeline name

    executions_from_path = []
    list_executions_exists = []

    if os.path.exists(path):
        query = cmfquery.CmfQuery(path)
        executions = query.get_all_executions_in_pipeline(pipeline_name)

        for i in executions.index:
            for uuid in executions['Execution_uuid'][i].split(","):
                executions_from_path.append(uuid)

        executions_from_req = []
        for stage in mlmd_data['Pipeline'][0]["stages"]:
            for execution in stage["executions"]:
                if execution['name'] != "":
                    continue
                if 'Execution_uuid' in execution['properties']:
                    for uuid in execution['properties']['Execution_uuid'].split(","):
                        executions_from_req.append(uuid)
                else:
                    return "version_update"

        if executions_from_path:
            list_executions_exists = list(set(executions_from_path).intersection(set(executions_from_req)))

        for pipeline in mlmd_data["Pipeline"]:
            for stage in pipeline['stages']:
                stage['executions'] = [
                    cmf_exec for cmf_exec in stage['executions']
                    if cmf_exec["properties"]["Execution_uuid"] not in list_executions_exists
                ]

            pipeline['stages'] = [stage for stage in pipeline['stages'] if stage['executions']]

    for pipeline in mlmd_data["Pipeline"]:
        if len(pipeline['stages']) == 0:
            return "exists"
        else:
            cmf_merger.parse_json_to_mlmd(
                json.dumps(mlmd_data), path, cmd, exe_uuid
            )
            return "success"
