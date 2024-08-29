from cmflib import cmfquery, cmf_merger
import pandas as pd
import json
import os
from server.app.query_artifact_lineage_d3force import query_artifact_lineage_d3force
from server.app.query_list_of_executions import query_list_of_executions
from fastapi.responses import FileResponse


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
    model_exe_df.drop(columns=['Python_Env', 'Git_Start_Commit', 'Git_End_Commit'], inplace=True)

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

async def get_executions(mlmdfilepath, pipeline_name, exe_ids):
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
    #df=df.drop('name',axis=1)
    return df


async def get_all_exe_ids(mlmdfilepath, pipeline_name: str = None):
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


async def get_all_artifact_ids(mlmdfilepath, execution_ids, pipeline_name: str = None):
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


async def get_artifacts(mlmdfilepath, pipeline_name, art_type, artifact_ids):
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

def get_artifact_types(mlmdfilepath):
    query = cmfquery.CmfQuery(mlmdfilepath)
    artifact_types = query.get_all_artifact_types()
    return artifact_types

async def create_unique_executions(server_store_path, req_info):
    mlmd_data = json.loads(req_info["json_payload"])
    pipelines = mlmd_data["Pipeline"]
    pipeline = pipelines[0]
    pipeline_name = pipeline["name"]
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
                json.dumps(mlmd_data), "/cmf-server/data/mlmd", "push", req_info["id"]
            )
            status='success'
    return status


async def get_mlmd_from_server(server_store_path: str, pipeline_name: str, exec_id: str):
    query = cmfquery.CmfQuery(server_store_path)
    execution_flag = 0
    json_payload = None
    df = pd.DataFrame()
    if(query.get_pipeline_id(pipeline_name)!=-1):  # checks if pipeline name is available in mlmd
        if exec_id != None:
            exec_id = int(exec_id)
            df = query.get_all_executions_by_ids_list([exec_id])
            if df.empty:
                json_payload = "no_exec_id"
                return json_payload
        json_payload = query.dumptojson(pipeline_name, exec_id)
    return json_payload


async def get_lineage_data(server_store_path,pipeline_name,type,dict_of_art_ids,dict_of_exe_ids):
    query = cmfquery.CmfQuery(server_store_path)
    if type=="Artifacts":
        lineage_data = query_artifact_lineage_d3force(server_store_path, pipeline_name, dict_of_art_ids)
        '''
        returns dictionary of nodes and links for artifact lineage.
        lineage_data= {
                       nodes:[],
                       links:[]
                      }
        '''
    elif type=="Execution":
        lineage_data = query_list_of_executions(server_store_path, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
        '''
        returns list of execution types for specific pipeline.
        '''
    else:
        lineage_data = query_visualization_ArtifactExecution(server_store_path, pipeline_name)
    return lineage_data

