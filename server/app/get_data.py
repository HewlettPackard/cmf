from cmflib import cmfquery, cmf_merger
import pandas as pd
import json,glob
import os
from server.app.query_visualization import query_visualization
from fastapi.responses import FileResponse

def get_executions_old(mlmdfilepath, pipeline_name):
    query = cmfquery.CmfQuery(mlmdfilepath)
    stages = query.get_pipeline_stages(pipeline_name)
    df = pd.DataFrame()
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        if str(executions.Pipeline_Type[0]) == pipeline_name:
            df = pd.concat([df, executions], sort=True, ignore_index=True)
    return df

def get_executions_by_ids(mlmdfilepath, pipeline_name, exe_ids):
    query = cmfquery.CmfQuery(mlmdfilepath)
    df = pd.DataFrame()
    executions = query.get_executions_by_id(exe_ids)
    df = pd.concat([df, executions], sort=True, ignore_index=True)
    return df

def get_all_exe_ids(mlmdfilepath):
    query = cmfquery.CmfQuery(mlmdfilepath)
    df = pd.DataFrame()
    execution_ids = {}
    names = query.get_pipeline_names()
    for name in names:
        stages = query.get_pipeline_stages(name)
        for stage in stages:
            executions = query.get_all_executions_in_stage(stage)
            df = pd.concat([df, executions], sort=True, ignore_index=True)
    if df.empty:
        return
    for name in names:
        execution_ids[name] = df.loc[df['Pipeline_Type'] == name, ['id', 'Context_Type']]
    return execution_ids

def get_all_artifact_ids(mlmdfilepath):
    # following is a dictionary of dictionary
    # First level dictionary key is pipeline_name
    # First level dicitonary value is nested dictionary
    # Nested dictionary key is type i.e. Dataset, Model, etc.
    # Nested dictionary value is ids i.e. set of integers
    artifact_ids = {}
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()
    for name in names:
        df = pd.DataFrame()
        artifacts = query.get_all_artifacts_by_context(name)
        df = pd.concat([df, artifacts], sort=True, ignore_index=True)
        if df.empty:
            return
        else:
            artifact_ids[name] = {}
            for art_type in df['type']:
                filtered_values = df.loc[df['type'] == art_type, ['id', 'name']]
                artifact_ids[name][art_type] = filtered_values
    return artifact_ids


# This function fetches all the artifacts available in given mlmd
def get_artifacts_old(mlmdfilepath, pipeline_name, data):  # get_artifacts return value (artifact_type or artifact_df) is 
  # determined by a data variable().
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()  # getting all pipeline names in mlmd
    identifiers = []
    for name in names:
        if name==pipeline_name:
            stages = query.get_pipeline_stages(name)
            for stage in stages:
                executions = query.get_all_exe_in_stage(stage)
                for exe in executions:
                    identifiers.append(exe.id)
    name = []
    url = []
    df = pd.DataFrame()
    for identifier in identifiers:
        get_artifacts = query.get_all_artifacts_for_execution(
            identifier
        )  # getting all artifacts
        df = pd.concat([df, get_artifacts], sort=True, ignore_index=True)
    df['event'] = df.groupby('id')['event'].transform(lambda x: ', '.join(x))
    df['name'] = df['name'].str.split(':').str[0]
    df=df.drop_duplicates()
    if data == "artifact_type":
        tempout = list(set(df["type"]))
    else:
        df = df.loc[df["type"] == data]
        result = df.to_json(orient="records")
        tempout = json.loads(result)
    return tempout


def get_artifacts(mlmdfilepath, pipeline_name, art_type, artifact_ids):
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()  # getting all pipeline names in mlmd
    df = pd.DataFrame()
    for name in names:
        if name == pipeline_name:
            df = query.get_all_artifacts_by_ids_list(artifact_ids)
            if len(df) == 0:
                return df
            df = df.drop_duplicates()
            df['name'] = df['name'].apply(lambda x: x.split(':')[0] if ':' in x else x)
            df = df.loc[df["type"] == art_type]
            result = df.to_json(orient="records")
            tempout = json.loads(result)
            return tempout

def get_artifact_types(mlmdfilepath):
    query = cmfquery.CmfQuery(mlmdfilepath)
    artifact_types = query.get_all_artifact_types()
    #print(artifact_types)
    return artifact_types

def create_unique_executions(server_store_path, req_info):
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


def get_mlmd_from_server(server_store_path, pipeline_name, exec_id):
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

def get_lineage_img_path(server_store_path,pipeline_name):
    query = cmfquery.CmfQuery(server_store_path)
    del_img = glob.glob("./data/static/*.png")
    for img in del_img:
        os.remove(img)
    img_path = query_visualization(server_store_path, pipeline_name)
    response = FileResponse(img_path,
    media_type="image/png",)
    return response

