import json
import os
from cmflib import cmfquery, cmf_merger
import time
import typing as t

def identify_existing_and_new_executions(path: str, mlmd_data: dict, pipeline_name: str) -> t.Tuple[list, list]:
    """
    Identify existing and new executions by comparing server MLMD data with client MLMD data.

    Args:
        path (str): Path to the MLMD file.
        mlmd_data (dict): MLMD data in dictionary format.
        pipeline_name (str): The name of the pipeline.

    Returns:
        tuple: A tuple containing two lists:
            - List of existing execution UUIDs.
            - List of new execution UUIDs.
    """
    existing_executions = []
    new_executions = []

    if os.path.exists(path):
        query = cmfquery.CmfQuery(path)
        executions = query.get_all_executions_in_pipeline(pipeline_name)

        # Collect all execution UUIDs from the queried data
        for i in executions.index:
            for uuid in executions['Execution_uuid'][i].split(","):
                existing_executions.append(uuid)

    # Extract execution UUIDs from the MLMD data payload
    executions_from_req = []
    for stage in mlmd_data['Pipeline'][0]["stages"]:
        for execution in stage["executions"]:
            if execution['name'] != "":
                continue
            if 'Execution_uuid' in execution['properties']:
                for uuid in execution['properties']['Execution_uuid'].split(","):
                    executions_from_req.append(uuid)

    # Identify new executions
    new_executions = list(set(executions_from_req) - set(existing_executions))

    return existing_executions, new_executions


def create_unique_executions(path: str, req_info: str, cmd: str, exe_uuid: str) -> str:
    """
    Creates a list of unique executions by checking if they already exist on the server or not.

    Args:
        path (str): Path to the MLMD file.
        req_info (str): Contains MLMD data.
        cmd (str): The command being executed, either "push" or "pull."
        exe_uuid (str, optional): User-provided execution UUID.

    Returns:
        str: A status message indicating the result of the operation.
    """
    mlmd_data = json.loads(req_info)
    pipeline_name = mlmd_data["Pipeline"][0]["name"]

    # Identify existing and new executions
    existing_executions, new_executions = identify_existing_and_new_executions(path, mlmd_data, pipeline_name)

    if not new_executions:
        return "exists"

    # Remove already existing executions from the data
    for pipeline in mlmd_data["Pipeline"]:
        for stage in pipeline['stages']:
            stage['executions'] = [
                cmf_exec for cmf_exec in stage['executions']
                if cmf_exec["properties"]["Execution_uuid"] in new_executions
            ]

    # Remove empty stages
    for pipeline in mlmd_data["Pipeline"]:
        pipeline['stages'] = [stage for stage in pipeline['stages'] if stage['executions']]

    # Determine if data remains to push/pull
    for pipeline in mlmd_data["Pipeline"]:
        if len(pipeline['stages']) == 0:
            return "exists"
        else:
            cmf_merger.parse_json_to_mlmd(
                json.dumps(mlmd_data), path, cmd, exe_uuid
            )
            return "success"
        
def get_unique_executions(server_store_path: str, client_mlmd_json: str) -> list:
    """
    Get unique executions from the server MLMD data that are not present in the client MLMD data.

    Args:
        server_store_path (str): The path to the server MLMD store.
        client_mlmd_json (str): JSON string of the client MLMD data.
        pipeline_name (str): The name of the pipeline.

    Returns:
        list: A list of unique executions with Execution_uuid and utc_time in epoch format.
    """
    mlmd_data = json.loads(client_mlmd_json)
    pipeline_name = mlmd_data["Pipeline"][0]["name"]

    # Use identify_existing_and_new_executions to find new executions
    _, new_executions = identify_existing_and_new_executions(server_store_path, mlmd_data, pipeline_name)

    # Extract details of unique executions
    unique_executions = []
    for stage in mlmd_data["Pipeline"][0]["stages"]:
        for execution in stage["executions"]:
            if execution["properties"]["Execution_uuid"] in new_executions:
                utc_time_epoch = int(time.time() * 1000)
                unique_executions.append({
                    "Execution_uuid": execution["properties"]["Execution_uuid"],
                    "last_sync_time": utc_time_epoch
                })

    return unique_executions
