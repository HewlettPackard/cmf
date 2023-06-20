from cmflib import cmfquery, cmf_merger
import pandas as pd
import json,glob
import os
from server.app.query_visualization import query_visualization
from fastapi.responses import FileResponse

def get_executions(mlmdfilepath, pipeline_name):
    query = cmfquery.CmfQuery(mlmdfilepath)
    stages = query.get_pipeline_stages(pipeline_name)
    df = pd.DataFrame()
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage.name)
        if str(executions.Pipeline_Type[0]) == pipeline_name:
            df = pd.concat([df, executions], sort=True, ignore_index=True)
    return df


# This function fetches all the artifacts available in given mlmd
def get_artifacts(mlmdfilepath, pipeline_name, data):  # get_artifacts return value (artifact_type or artifact_df) is 
  # determined by a data variable().
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()  # getting all pipeline names in mlmd
    identifiers = []
    for name in names:
        if name==pipeline_name:
            stages = query.get_pipeline_stages(name)
            for stage in stages:
                executions = query.get_all_executions_in_stage(stage.name)
                dict_executions = executions.to_dict("dict")  # converting it to dictionary
                identifiers.append(dict_executions["id"][0])
    name = []
    url = []
    df = pd.DataFrame()
    for identifier in identifiers:
        get_artifacts = query.get_all_artifacts_for_execution(
            identifier
        )  # getting all artifacts
        artifacts_dict = get_artifacts.to_dict("dict")  # converting it to dictionary
        df = pd.concat([df, get_artifacts], sort=True, ignore_index=True)
    if data == "artifact_type":
        tempout = list(set(df["type"]))
    else:
        df = df.loc[df["type"] == data]
        result = df.to_json(orient="records")
        tempout = json.loads(result)
    return tempout


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
            executions = query.get_all_executions_in_stage(stage.name)
            for i in executions.index:
                executions_server.append(executions['Context_Type'][i])
        executions_client = []
        for i in mlmd_data['Pipeline'][0]["stages"]:  # checks if given execution_id present in mlmd
            for j in i["executions"]:
                print(j['name'])
                if j['name'] != "":
                    continue
                executions_client.append(j['properties']['Context_Type'])
        if executions_server != []:
            list_executions_exists = list(set(executions_client).intersection(set(executions_server)))
        for i in mlmd_data["Pipeline"]:
            for stage in i['stages']:
                for exec in stage['executions']:
                    if exec["properties"]["Context_Type"] in list_executions_exists:
                        stage['executions'].remove(exec)
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

