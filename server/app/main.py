from fastapi import FastAPI,Request
from server.app.mlmd import merge_mlmd
from cmflib import cmfquery
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from server.app.get_data import artifact,index
from pathlib import Path
import os
import json
app = FastAPI()

BASE_PATH=Path(__file__).resolve().parent
templates=Jinja2Templates(directory=str(BASE_PATH/'template'))

@app.get("/")
def read_root():
    return {"Use this api for sending json payload":"http://127.0.0.1/mlmd_push/"}


@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info=await info.json()
    merge_mlmd(req_info['json_payload'],req_info['id'])

    return{
        'status':'success',
        'data':req_info
    }

@app.get("/mlmd_pull",response_class=HTMLResponse)
async def mlmd_pull(request: Request):
    if os.path.exists("/cmf-server/data/mlmd"):
        query = cmfquery.CmfQuery("/cmf-server/data/mlmd")
        json_payload = query.dumptojson("Test-env")
        return json_payload
    else:
        print("No mlmd file submitted")
        json_payload=""
        return json_payload

@app.get("/mlmd_pull_exec_by_id",response_class=HTMLResponse)
async def mlmd_pull(request: Request):
    if os.path.exists("/cmf-server/data/mlmd"):
        query = cmfquery.CmfQuery("/cmf-server/data/mlmd")
        json_payload = query.dumptojson("Test-env")
        return json_payload
    else:
        print("No mlmd file submitted")
        json_payload=""
        return json_payload


@app.get("/display_executions",response_class=HTMLResponse)
async def display_exec(request: Request):
    if os.path.exists("/cmf-server/data/mlmd"):
        execution_df=index("/cmf-server/data/mlmd")
        query = cmfquery.CmfQuery("/cmf-server/data/mlmd")
        json_payload = query.dumptojson("Test-env")
        exec_val="true"
    else:
        print("No mlmd file submitted")
        exec_val="false"
        execution_df=" "
    return templates.TemplateResponse('execution.html',{'request':request,'exec_df':execution_df,'exec_val':exec_val})

@app.get("/display_artifacts",response_class=HTMLResponse)
async def display_artifact(request: Request):
    if os.path.exists("/cmf-server/data/mlmd"):
        artifact_df=artifact("/cmf-server/data/mlmd")
        artifact_val="true"
    else:
        artifact_val="false"
        artifact_df=""
    return templates.TemplateResponse('artifacts.html',{'request':request,'artifact_df':artifact_df,'artifact_val':artifact_val})
