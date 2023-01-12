# cmf-server api's

from fastapi import FastAPI, Request
from server.app.mlmd import merge_mlmd
from cmflib import cmfquery, merger
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from server.app.get_data import get_executions, get_artifacts
from pathlib import Path
import os
import json

app = FastAPI()

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "template"))
server_store_path = "/cmf-server/data/mlmd"


@app.get("/")
def read_root():
    return {
        "Welcome to cmf-server, Use various APIs to interact with cmf-server eg: http://server_ip/mlmd_push/ "
    }


# api to posAt mlmd file to cmf-server
@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info = await info.json()
    merger.parse_json_to_mlmd(
        req_info["json_payload"], "data/mlmd", "push", req_info["id"]
    )
    return {"status": "success", "data": req_info}


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
        execution_df = get_executions(server_store_path)
        query = cmfquery.CmfQuery(server_store_path)
        if (
            pipeline_name in query.get_pipeline_names()
        ):  # checks if pipeline name is available in mlmd
            json_payload = query.dumptojson(pipeline_name, None)
            exec_val = "true"
        else:
            print("Pipeline name " + pipeline_name + " doesn't exist.")
            exec_val = "nopipeline"
    else:
        print("No mlmd file submitted.")
        exec_val = "false"
        execution_df = " "
    return templates.TemplateResponse(
        "execution.html",
        {"request": request, "exec_df": execution_df, "exec_val": exec_val},
    )


# api to display artifacts available in mlmd
@app.get("/display_artifacts", response_class=HTMLResponse)
async def display_artifact(request: Request):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        artifact_df = get_artifacts(server_store_path)
        artifact_val = "true"
    else:
        artifact_val = "false"
        artifact_df = ""
    return templates.TemplateResponse(
        "artifacts.html",
        {"request": request, "artifact_df": artifact_df, "artifact_val": artifact_val},
    )
