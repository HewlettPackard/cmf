# cmf-server api's
from fastapi import FastAPI, Request
from cmflib import cmfquery, cmf_merger
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from server.app.get_data import get_executions, get_artifacts
from server.app.query_visualization import query_visualization
from pathlib import Path
import glob
import os
import json

app = FastAPI()

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "template"))
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")
server_store_path = "/cmf-server/data/mlmd"


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(
        "home.html", {'request': request}
    )


# api to posAt mlmd file to cmf-server
@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info = await info.json()
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
                executions_server.append(executions['Context_Type'][i])
            executions_client = []
            for i in mlmd_data['Pipeline'][0]["stages"]:  # checks if given execution_id present in mlmd
                for j in i["executions"]:
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
                json.dumps(mlmd_data), server_store_path, "push", req_info["id"]
            )
            status='success'
    return {"status": status, "data": req_info}


# api to get mlmd file from cmf-server
@app.get("/mlmd_pull/{pipeline_name}", response_class=HTMLResponse)
async def mlmd_pull(info: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    req_info = await info.json()
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        execution_flag = 0
        # checks if given execution_id present in mlmd
        if (
                pipeline_name in query.get_pipeline_names()
        ):  # checks if pipeline name is available in mlmd
            json_payload = query.dumptojson(pipeline_name, None)
            mlmd_data = json.loads(json_payload)["Pipeline"]
            if req_info["exec_id"] == None:
                json_payload = query.dumptojson(pipeline_name, req_info["exec_id"])
            else:
                for stage in mlmd_data[0]["stages"]:
                    for execution in stage["executions"]:
                        if execution["id"] == int(req_info["exec_id"]):
                            execution_flag = 1
                            break
                if execution_flag == 1:
                    json_payload = query.dumptojson(pipeline_name, req_info["exec_id"])
                else:
                    json_payload = "no_exec_id"
                    return json_payload
        else:
            json_payload = "NULL"
    else:
        print("No mlmd file submitted.")
        json_payload = ""
    return json_payload


# api to display executions available in mlmd
@app.get("/display_executions/{pipeline_name}", response_class=HTMLResponse)
async def display_exec(request: Request, pipeline_name: str):
    # checks if mlmd file exists on server

    if os.path.exists(server_store_path):
        execution_df = get_executions(server_store_path, pipeline_name)
        exec_val = "true"

    return templates.TemplateResponse(
        "execution.html",
        {"request": request, "exec_df": execution_df, "exec_val": exec_val},
    )


@app.get("/display_lineage/{pipeline_name}", response_class=HTMLResponse)
async def display_lineage(request: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    img_path=""
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            del_img = glob.glob("./data/static/*.jpg")
            for img in del_img:
                os.remove(img)
            img_path = query_visualization(server_store_path, pipeline_name)
        else:
            print("Pipeline name " + pipeline_name + " doesn't exist.")


    else:
        print('mlmd doesnt exist')
    return templates.TemplateResponse(
        "lineage.html", {"request": request, "img_path": img_path},
    )


# api to display artifacts available in mlmd
@app.get("/display_artifact_type/{pipeline_name}/{data}", response_class=HTMLResponse)
async def display_artifact(request: Request, pipeline_name: str,data: str):
    # checks if mlmd file exists on server
    if data=="artifact_type":
        html_to_render="artifact_by_type.html"
    else:
        html_to_render="artifacts.html"
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            artifact_df = get_artifacts(server_store_path, pipeline_name,data)
            artifact_val = "true"
    else:
        artifact_val = "false"
        artifact_df = ""
    return templates.TemplateResponse(
        html_to_render,
        {"request": request, "artifact_df": artifact_df, "artifact_val": artifact_val,"pipeline_name": pipeline_name},
    )


@app.get("/display_pipelines/{disp_val}", response_class=HTMLResponse)
async def display_list_of_pipelines(request: Request,disp_val:str):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        pipeline_names = query.get_pipeline_names()
        exec_val = 'True'
    else:
        print("No mlmd file submitted.")
        pipeline_names = []
        exec_val = "False"
    return templates.TemplateResponse(
        "list_of_pipelines.html",
        {"request": request, "exec_val": exec_val, 'pipeline_names': pipeline_names,'disp_val':disp_val},
    )

