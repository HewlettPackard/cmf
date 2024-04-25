from cmflib import cmfquery, cmf_merger
import pandas as pd
import json,glob
import os
from server.app.query_visualization import query_visualization
from server.app.query_visualization_execution import query_visualization_execution
from fastapi.responses import FileResponse

async def get_executions_by_ids(mlmdfilepath, pipeline_name, exe_ids):
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

async def get_all_exe_ids(mlmdfilepath):
    '''
    Returns:
        returns a dictionary which has pipeline_name as key and dataframe which includes {id,Execution_uuid,Context_Type,Context_id} as value.
    '''
    query = cmfquery.CmfQuery(mlmdfilepath)
    execution_ids = {}
    names = query.get_pipeline_names()
    for name in names:
        df = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
        stages = query.get_pipeline_stages(name)
        for stage in stages:
            executions = query.get_all_executions_in_stage(stage)
            df = pd.concat([df, executions], sort=True, ignore_index=True)
        # check if df is empty return just pipeline_name: {}
        # if df is not empty return dictionary with pipeline_name as key 
        # and df with id, context_type, uuid, context_ID as value.
        if not df.empty:
            execution_ids[name] = df[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
        else:
            execution_ids[name] = pd.DataFrame()
    return execution_ids

async def get_all_artifact_ids(mlmdfilepath):
    # following is a dictionary of dictionary
    # First level dictionary key is pipeline_name
    # First level dicitonary value is nested dictionary
    # Nested dictionary key is type i.e. Dataset, Model, etc.
    # Nested dictionary value is ids i.e. set of integers
    artifact_ids = {}
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()
    execution_ids = await get_all_exe_ids(mlmdfilepath)
    for name in names:
        df = pd.DataFrame()
        if not execution_ids.get(name).empty:
            exe_ids = execution_ids[name]['id'].tolist()
            for id in exe_ids:
                artifacts = query.get_all_artifacts_for_execution(id)
                df = pd.concat([df, artifacts], sort=True, ignore_index=True)
            #acknowledging pipeline exist even if df is empty. 
            if df.empty:
                artifact_ids[name] = pd.DataFrame()   # { pipeline_name: {empty df} }
            else:
                df.sort_values("id", inplace=True)
                df.drop_duplicates(subset="id", keep='first', inplace=True)
                artifact_ids[name] = {}
                for art_type in df['type']:
                    filtered_values = df.loc[df['type'] == art_type, ['id', 'name']]
                    artifact_ids[name][art_type] = filtered_values
        # if execution_ids is empty create dictionary with key as pipeline name
        # and value as empty df
        else:
            artifact_ids[name] = pd.DataFrame()
    return artifact_ids

async def get_artifacts(mlmdfilepath, pipeline_name, art_type, artifact_ids):
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()  # getting all pipeline names in mlmd
    df = pd.DataFrame()
    for name in names:
        if name == pipeline_name:
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
        stages = query.get_pipeline_stages(pipeline_name)
        for stage in stages:
            executions = []
            executions = query.get_all_executions_in_stage(stage)
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


async def get_mlmd_from_server(server_store_path, pipeline_name, exec_id):
    query = cmfquery.CmfQuery(server_store_path)
    execution_flag = 0
    # checks if given execution_id present in mlmd
    if (
        pipeline_name in query.get_pipeline_names()
    ):  # checks if pipeline name is available in mlmd
        json_payload = query.dumptojson(pipeline_name, None)
        mlmd_data = json.loads(json_payload)["Pipeline"]
        if exec_id == None:
            json_payload = query.dumptojson(pipeline_name, exec_id)
        else:
            for stage in mlmd_data[0]["stages"]:
                for execution in stage["executions"]:
                    if execution["id"] == int(exec_id):
                        execution_flag = 1
                        break
            if execution_flag == 1:
                json_payload = query.dumptojson(pipeline_name, exec_id)
            else:
                json_payload = "no_exec_id"
                return json_payload
    else:
        json_payload = "NULL"
    return json_payload

async def get_lineage_data(server_store_path,pipeline_name,type,dict_of_art_ids,dict_of_exe_ids):
    query = cmfquery.CmfQuery(server_store_path)
    if type=="Artifacts":
        lineage_data = query_visualization(server_store_path, pipeline_name, dict_of_art_ids)
        '''
        returns dictionary of nodes and links for artifact lineage.
        lineage_data= {
                       nodes:[],
                       links:[]
                      }
        '''
    elif type=="Execution":
        lineage_data = query_visualization_execution(server_store_path, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
        '''
        returns list of execution types for specific pipeline.
        '''
    else:
        lineage_data = query_visualization_ArtifactExecution(server_store_path, pipeline_name)
    return lineage_data

