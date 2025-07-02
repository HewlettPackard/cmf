import json
import typing as t
from cmflib.cmfquery import CmfQuery
from cmflib.cmf_merger import parse_json_to_mlmd


def identify_existing_and_new_executions(query: CmfQuery, pipeline_data: dict, pipeline_name: str) -> t.Tuple[list, list, list, str]:
    """
    Identifies and compares existing executions from a given MLMD store path with those in the MLMD payload.
    This method supports both push and pull operations by analyzing execution UUIDs and identifying overlap
    and differences between the source and target MLMD stores.

    Args:
        query (CmfQuery): The CmfQuery object.
        mlmd_data (dict): MLMD data in dictionary format.
        pipeline_name (str): The name of the pipeline.

    Returns:
        tuple: A 4-element tuple containing:
        - executions_from_path (list): All execution UUIDs found in the MLMD store at the given path.
        - list_executions_exists (list): Intersection of execution UUIDs between store and request (already present).
        - executions_from_req (list): Execution UUIDs present in the incoming MLMD payload.
        - status (str): Returns "version_update" if the payload is malformed or missing execution UUIDs.
    """
    executions_from_path = []  # Stores existing execution UUIDs from the path
    list_executions_exists: list[str] = []  # Stores the intersection of existing and new executions
    executions_from_req = []  # Extract execution UUIDs from the MLMD data payload
    status = ""

    # For metadata push → path is the server MLMD store path
    # For metadata pull → path is the client MLMD store path
    executions = query.get_all_executions_in_pipeline(pipeline_name)

    # Collect all execution UUIDs from the queried data
    for i in executions.index:
        for uuid in executions['Execution_uuid'][i].split(","):
            executions_from_path.append(uuid)

    # For metadata push → mlmd_data comes from client MLMD file
    # For metadata pull → mlmd_data comes from server MLMD file
    for stage in pipeline_data['stages']:  # checks if given execution_id present in mlmd
        for execution in stage["executions"]:
            if execution['name'] != "":  # If executions have name , they are reusable executions
                continue                # which needs to be merged in irrespective of whether already
                                        # present or not so that new artifacts associated with it gets in.
            if 'Execution_uuid' in execution['properties']:
                for uuid in execution['properties']['Execution_uuid'].split(","):
                    executions_from_req.append(uuid)
            else:
                # mlmd push is failed here
                status = "version_update"
                return executions_from_path, list_executions_exists, executions_from_req, status

    # Intersection check:
    # For metadata push → ensures only new executions get pushed
    # For metadata pull → ensures only missing executions get pull
    if executions_from_path != []:
        list_executions_exists = list(set(executions_from_path).intersection(set(executions_from_req)))
    return executions_from_path, list_executions_exists, executions_from_req, status


def update_mlmd(query: CmfQuery, req_info: str, pipeline_name: str, cmd: str, exe_uuid: str) -> str:
    """
    Updates metadata for a given pipeline by filtering out executions that already exist
    on the server and then pushing or pulling the remaining data.
    
    Args:
        query (CmfQuery): The CmfQuery object.
        req_info (str): Contains MLMD data — client-side for push, server-side for pull.  
        pipeline_name (str): The name of the pipeline to update.
        cmd (str): The command being executed, either "push" or "pull."  
        exe_uuid (str, optional): User-provided execution UUID (default: None).  
    
    Returns: A status message indicating the result of the operation:
        - "pipeline_not_exist": Pipeline does not exists inside CMF server.
        - "exists": Execution already exists on the CMF server.
        - "success": Execution successfully pushed to the CMF server.
        - "invalid_json_payload": If the JSON payload is invalid or incorrectly formatted.
        - "version_update": Mlmd push failed due to version update. 
    """
    # load the mlmd_data from the request info
    # in create executions we get full mlmd data
    mlmd_data = json.loads(req_info)
    # Ensure the pipeline name in req_info matches the one in the JSON payload to maintain data integrity
    pipelines = mlmd_data.get("Pipeline", []) # Extract "Pipeline" list, default to empty list if missing
    # pipelines contain full mlmd data with the tag - 'Pipeline'

    if not pipelines:
        return "invalid_json_payload"  # No pipelines found in payload
  
    len_pipelines = len(pipelines)
    if pipeline_name:
        # in case of push check pipeline name exists inside mlmd_data
        pipeline = [pipeline for pipeline in pipelines if pipeline.get("name") == pipeline_name]
        if not pipeline:
            return "pipeline_not_exist"

        pipeline = pipeline[0]  # Extract the first matching pipeline    

        _, list_executions_exists, _, status = identify_existing_and_new_executions(
            query, pipeline, pipeline_name
        ) 

        if status == "version_update":
            return status
        
        # remove already existing executions from the data
        for stage in pipeline['stages']:
            # Create a new filtered list to avoid modifying while iterating
            filtered_executions = []
            # Iterate through executions and remove the ones that already exist
            for cmf_exec in stage['executions']:
                uuids = cmf_exec["properties"]["Execution_uuid"].split(",")
                for uuid in uuids:
                    if not any(uuid in list_executions_exists for uuid in uuids):
                        filtered_executions.append(cmf_exec)
            stage['executions'] = filtered_executions

        # remove empty stages (those without remaining executions)
        pipeline['stages'] = [stage for stage in pipeline['stages'] if stage['executions'] != []]

        # determine if data remains to push/pull
        if len(pipeline['stages']) == 0 :
            status="exists"
        else:
            # metadata push → merge client data into server path
            # metadata pull → merge server data into client path
            if cmd == "pull":
                parse_json_to_mlmd(
                    json.dumps(pipeline), query.filepath, cmd, exe_uuid
                )
            else:
                parse_json_to_mlmd(
                    json.dumps(pipeline), "", cmd, exe_uuid
                )
            status = "success"
        return status
    else:
            for pipeline in pipelines:
                pipeline_name = pipeline.get("name")

                _, list_executions_exists, _, status = identify_existing_and_new_executions(
                    query, pipeline, pipeline_name
                )  
                if status == "version_update":
                    return status

                for stage in pipeline['stages']:
                    # Iterate through executions and remove the ones that already exist
                    for cmf_exec in stage['executions'][:]:
                        uuids = cmf_exec["properties"]["Execution_uuid"].split(",")
                        for uuid in uuids:
                            if uuid in list_executions_exists:
                                stage['executions'].remove(cmf_exec)

                # remove empty stages (those without remaining executions)
                pipeline['stages'] = [stage for stage in pipeline['stages'] if stage['executions'] != []]

                # determine if data remains to push/pull
                if len(pipeline['stages']) == 0 :
                    status="exists"
                else:
                    # metadata push → merge client data into server path
                    # metadata pull → merge server data into client path
                    if cmd == "pull":
                        parse_json_to_mlmd(
                            json.dumps(pipeline), query.filepath, cmd, exe_uuid
                        )
                    else:
                        parse_json_to_mlmd(
                            json.dumps(pipeline), "", cmd, exe_uuid
                        )
                    # we are passing this success in a very wrong way
                    status = "success"

            return status

