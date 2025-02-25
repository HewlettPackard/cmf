from cmflib import cmfquery, cmf_merger
import pandas as pd
import json
import os
import typing as t
from fastapi.concurrency import run_in_threadpool
from server.app.query_artifact_lineage_d3force import query_artifact_lineage_d3force
from server.app.query_list_of_executions import query_list_of_executions

# Converts sync functions to async
async def async_api(function_to_async, mlmdfilepath: str, *argv):
    return await run_in_threadpool(function_to_async, mlmdfilepath, *argv)

async def get_model_data(mlmdfilepath, modelId):
    '''
      This function retrieves the necessary model data required for generating a model card.

      Arguments:
        mlmdfilepath (str): The file path to the metadata.
        modelId (int): The ID of the model for which data is required.

      Returns:
        This function returns a tuple of DataFrames containing the following:

        model_data_df (DataFrame): Metadata related to the model itself.
        model_exe_df (DataFrame): Metadata of the executions in which the specified modelId was an input or output.
        model_input_df (DataFrame): Metadata of input artifacts that led to the creation of the model.
        model_output_df (DataFrame): Metadata of artifacts that used the model as an input.
        The returned DataFrames provide comprehensive metadata for the specified model, aiding in the creation of detailed and accurate model cards.
    '''
    query = cmfquery.CmfQuery(mlmdfilepath)
    pd.set_option('display.max_columns', None)
    model_data_df = pd.DataFrame()
    model_exe_df = pd.DataFrame()
    model_input_df = pd.DataFrame()
    model_output_df = pd.DataFrame()

    # get name from id
    modelName = ""
    model_data_df = query.get_all_artifacts_by_ids_list([modelId])
    # if above dataframe is not empty, we have the dataframe for given modelId with full model related details
    if model_data_df.empty:
        return model_data_df, model_exe_df, model_input_df, model_output_df
    # However following check is done, in case, variable 'modelId' is not an ID for model artifact
    modelType = model_data_df['type'].tolist()[0]
    if not modelType == "Model":
        # making model_data_df empty
        model_data_df = pd.DataFrame()
        return model_data_df, model_exe_df, model_input_df, model_output_df


    # extracting modelName
    modelName = model_data_df['name'].tolist()[0]

    # model's executions data with props and custom props
    exe_df = query.get_all_executions_for_artifact(modelName)
    exe_ids = []
    if not exe_df.empty:
        exe_df.drop(columns=['execution_type_name', 'execution_name'], inplace=True)
        exe_ids = exe_df['execution_id'].tolist()


    if not exe_ids:
         return model_data_df, model_exe_df, model_input_df, model_output_df
    model_exe_df = query.get_all_executions_by_ids_list(exe_ids)
    model_exe_df.drop(columns=['Git_Start_Commit', 'Git_End_Commit'], inplace=True)

    in_art_ids =  []
    # input artifacts
    # it is usually not a good practice to use functions starting with _ outside of the file they are defined .. should i change??
    in_art_ids.extend(query._get_input_artifacts(exe_ids))
    if modelId in in_art_ids:
        in_art_ids.remove(modelId)
    model_input_df = query.get_all_artifacts_by_ids_list(in_art_ids)

    out_art_ids = []
    # output artifacts
    out_art_ids.extend(query._get_output_artifacts(exe_ids))
    if modelId in out_art_ids:
        out_art_ids.remove(modelId)
    model_output_df = query.get_all_artifacts_by_ids_list(out_art_ids)

    return model_data_df, model_exe_df, model_input_df, model_output_df


def get_executions(mlmdfilepath: str, pipeline_name, exe_ids) -> pd.DataFrame:
    '''
    Args:
     mlmdfilepath: mlmd file path.
     pipeline_name: name of the pipeline.
     exe_ids: list of execution ids.

    Returns:
     returns dataframe of executions using execution_ids.
    '''

    query = cmfquery.CmfQuery(mlmdfilepath)
    df = pd.DataFrame()
    executions = query.get_all_executions_by_ids_list(exe_ids)
    df = pd.concat([df, executions], sort=True, ignore_index=True)
    return df


def get_all_exe_ids(mlmdfilepath: str, pipeline_name: str = None) -> t.Dict[str, pd.DataFrame]:
    '''
    Returns:
    returns a dictionary which has pipeline_name as key and dataframe which includes {id,Execution_uuid,Context_Type,Context_id} as value.
    '''
    query = cmfquery.CmfQuery(mlmdfilepath)
    execution_ids = {}
    executions = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
    if pipeline_name:
        executions = query.get_all_executions_in_pipeline(pipeline_name)
        if not executions.empty:
            execution_ids[pipeline_name] = executions[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
        else:
            execution_ids[pipeline_name] = pd.DataFrame()
    else:
        names = query.get_pipeline_names()
        for name in names:
            executions = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
            executions = query.get_all_executions_in_pipeline(name)
            # check if df is empty return just pipeline_name: {}
            # if df is not empty return dictionary with pipeline_name as key
            # and df with id, context_type, uuid, context_ID as value.
            if not executions.empty:
                execution_ids[name] = executions[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
            else:
                execution_ids[name] = pd.DataFrame()
    return execution_ids


def get_all_artifact_ids(mlmdfilepath: str, execution_ids, pipeline_name: str = None) -> t.Dict[str, t.Dict[str, pd.DataFrame]]:
    # following is a dictionary of dictionaries
    # First level dictionary key is pipeline_name
    # First level dicitonary value is nested dictionary
    # Nested dictionary key is type i.e. Dataset, Model, etc.
    # Nested dictionary value is a pandas df with id and artifact name
    artifact_ids = {}
    query = cmfquery.CmfQuery(mlmdfilepath)
    artifacts = pd.DataFrame()
    if pipeline_name:
        if not execution_ids.get(pipeline_name).empty:
            exe_ids = execution_ids[pipeline_name]['id'].tolist()
            artifacts = query.get_all_artifacts_for_executions(exe_ids)
            #acknowledging pipeline exist even if df is empty. 
            if artifacts.empty:
                artifact_ids[pipeline_name] = pd.DataFrame()   # { pipeline_name: {empty df} }
            else:
                artifact_ids[pipeline_name] = {}
                for art_type in artifacts['type']:
                    filtered_values = artifacts.loc[artifacts['type'] == art_type, ['id', 'name']]
                    artifact_ids[pipeline_name][art_type] = filtered_values
        # if execution_ids is empty then create dictionary with key as pipeline name
        # and value as empty df
        else:
            artifact_ids[pipeline_name] = pd.DataFrame()
    else:
        names = query.get_pipeline_names()
        for name in names:
            if not execution_ids.get(name).empty:
                exe_ids = execution_ids[name]['id'].tolist()
                artifacts = query.get_all_artifacts_for_executions(exe_ids)
                #acknowledging pipeline exist even if df is empty. 
                if artifacts.empty:
                    artifact_ids[name] = pd.DataFrame()   # { pipeline_name: {empty df} }
                else:
                    artifact_ids[name] = {}
                    for art_type in artifacts['type']:
                        filtered_values = artifacts.loc[artifacts['type'] == art_type, ['id', 'name']]
                        artifact_ids[name][art_type] = filtered_values
            # if execution_ids is empty then create dictionary with key as pipeline name
            # and value as empty df
            else:
                artifact_ids[name] = pd.DataFrame()
    return artifact_ids

def get_artifacts(mlmdfilepath, pipeline_name, art_type, artifact_ids):
    query = cmfquery.CmfQuery(mlmdfilepath)
    df = pd.DataFrame()
    if (query.get_pipeline_id(pipeline_name) != -1):
        df = query.get_all_artifacts_by_ids_list(artifact_ids)
        if len(df) == 0:
            return
        df = df.drop_duplicates()
        art_names = df['name'].tolist()
        name_dict = {}
        name_list = []
        exec_type_name_list = []
        exe_type_name = pd.DataFrame()
        for name in art_names:
            executions = query.get_all_executions_for_artifact(name)
            exe_type_name = pd.concat([exe_type_name, executions], ignore_index=True)
            execution_type_name = exe_type_name["execution_type_name"].drop_duplicates().tolist()
            execution_type_name = [str(element).split('"')[1] for element in execution_type_name]
            execution_type_name_str = ',\n '.join(map(str, execution_type_name))
            name_list.append(name)
            exec_type_name_list.append(execution_type_name_str)
        name_dict['name'] = name_list
        name_dict['execution_type_name'] = exec_type_name_list
        name_df = pd.DataFrame(name_dict)
        merged_df = df.merge(name_df, on='name', how='left')
        merged_df['name'] = merged_df['name'].apply(lambda x: x.split(':')[0] if ':' in x else x)
        merged_df = merged_df.loc[merged_df["type"] == art_type]
        result = merged_df.to_json(orient="records")
        tempout = json.loads(result)
        return tempout

def get_artifact_types(mlmdfilepath) -> t.List[str]:
    query = cmfquery.CmfQuery(mlmdfilepath)
    artifact_types = query.get_all_artifact_types()
    return artifact_types

def create_unique_executions(server_store_path, req_info) -> str:
    """
    Creates list of unique executions by checking if they already exist on server or not.
    locking is introduced lock to avoid data corruption on server, 
    when multiple similar pipelines pushed on server at same time.
    Args:
       server_store_path = mlmd file path on server
    Returns:
       str: A status message indicating the result of the operation:
            - "exists": Execution already exists on the CMF server.
            - "success": Execution successfully pushed to the CMF server.
            - "invalid_json_payload": If the JSON payload is invalid or incorrectly formatted.
            - "pipeline_not_exist": If the provided pipeline name does not match the one in the payload. 
    """
    mlmd_data = json.loads(req_info["json_payload"])
    # Ensure the pipeline name in req_info matches the one in the JSON payload to maintain data integrity
    pipelines = mlmd_data.get("Pipeline", []) # Extract "Pipeline" list, default to empty list if missing
    if not pipelines:
        return "invalid_json_payload"  # No pipelines found in payload
    pipeline = pipelines[0]
    pipeline_name = pipeline.get("name")  # Extract pipeline name, use .get() to avoid KeyError
    if not pipeline_name:
        return "invalid_json_payload"  # Missing pipeline name
    req_pipeline_name = req_info["pipeline_name"]
    if req_pipeline_name != pipeline_name:
        return "pipeline_not_exist"  # Mismatch between provided pipeline name and payload
    executions_server = []
    list_executions_exists = []
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        executions = query.get_all_executions_in_pipeline(pipeline_name)
        for i in executions.index:
            for uuid in executions['Execution_uuid'][i].split(","):
                executions_server.append(uuid)
        executions_client = []
        for i in mlmd_data['Pipeline'][0]["stages"]:  # checks if given execution_id present in mlmd
            for j in i["executions"]:
                if j['name'] != "": #If executions have name , they are reusable executions
                    continue       #which needs to be merged in irrespective of whether already
                                #present or not so that new artifacts associated with it gets in.
                if 'Execution_uuid' in j['properties']:
                    for uuid in j['properties']['Execution_uuid'].split(","):
                        executions_client.append(uuid)
                else:
                    # mlmd push is failed here
                    status="version_update"
                    return status
        if executions_server != []:
            list_executions_exists = list(set(executions_client).intersection(set(executions_server)))
        for i in mlmd_data["Pipeline"]:
            for stage in i['stages']:
                for cmf_exec in stage['executions'][:]:
                    uuids = cmf_exec["properties"]["Execution_uuid"].split(",")
                    for uuid in uuids:
                        if uuid in list_executions_exists:
                            stage['executions'].remove(cmf_exec)
        
        for i in mlmd_data["Pipeline"]:
            i['stages']=[stage for stage in i['stages'] if stage['executions']!=[]]
            
    for i in mlmd_data["Pipeline"]:

        if len(i['stages']) == 0 :
            status="exists"
        else:
            cmf_merger.parse_json_to_mlmd(
                json.dumps(mlmd_data), "/cmf-server/data/mlmd", "push", req_info["exec_uuid"]
            )
            status='success'

    return status


def get_mlmd_from_server(server_store_path: str, pipeline_name: str, exec_uuid: str, dict_of_exe_ids: dict):
    """
    Retrieves metadata from the server for a given pipeline and execution UUID.

    Args:
        server_store_path (str): The path to the server store.
        pipeline_name (str): The name of the pipeline.
        exec_uuid (str): The execution UUID.
        dict_of_exe_ids (dict): A dictionary containing execution IDs for pipelines.

    Returns:
        json_payload (str or None): The metadata in JSON format if found, "no_exec_uuid" if the execution UUID is not found, or None if the pipeline name is not available.
    """
    query = cmfquery.CmfQuery(server_store_path)
    json_payload = None
    flag=False
    if(query.get_pipeline_id(pipeline_name)!=-1):  # checks if pipeline name is available in mlmd
        if exec_uuid != None:
            dict_of_exe_ids = dict_of_exe_ids[pipeline_name]
            for index, row in dict_of_exe_ids.iterrows():
                exec_uuid_list = row['Execution_uuid'].split(",")
                if exec_uuid in exec_uuid_list:
                    flag=True
                    break
            if not flag:
                json_payload = "no_exec_uuid"
                return json_payload
        json_payload = query.dumptojson(pipeline_name, exec_uuid)
    return json_payload

def get_lineage_data(
        server_store_path, 
        pipeline_name, type,
        dict_of_art_ids,
        dict_of_exe_ids):
    """
    Retrieves lineage data based on the specified type.

    Parameters:
    server_store_path (str): The path to the server store.
    pipeline_name (str): The name of the pipeline.
    type (str): The type of lineage data to retrieve. Can be "Artifacts" or "Execution".
    dict_of_art_ids (dict): A dictionary of artifact IDs.
    dict_of_exe_ids (dict): A dictionary of execution IDs.

    Returns:
    dict or list: 
        - If type is "Artifacts", returns a dictionary with nodes and links for artifact lineage.
                lineage_data= {
                    nodes:[],
                    links:[]
                }
        - If type is "Execution", returns a list of execution types for the specified pipeline.
        - Otherwise, returns visualization data for artifact execution.
    """
    if type=="Artifacts":
        lineage_data = query_artifact_lineage_d3force(server_store_path, pipeline_name, dict_of_art_ids)
    elif type=="Execution":
        lineage_data = query_list_of_executions(server_store_path, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
    else:
        lineage_data = query_visualization_ArtifactExecution(server_store_path, pipeline_name)
    return lineage_data

