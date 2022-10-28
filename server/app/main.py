from fastapi import FastAPI,Request
from server.app.mlmd import merge_mlmd
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from get_data import index,artifact
from pathlib import Path
import json
app = FastAPI()

BASE_PATH=Path(__file__).resolve().parent
templates=Jinja2Templates(directory=str(BASE_PATH/'template'))

@app.get("/")
def read_root():
    return {"Use this api for sending json payload":"http://127.0.0.1:8000/mlmd_push/"}


@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info=await info.json()
    merge_mlmd(req_info)

    return{
        'status':'success',
        'data':req_info
    }


@app.get("/display_executions",response_class=HTMLResponse)
async def display_exec(request: Request):

    execution_df=index("/home/abhinavchobey/hp_server/cmf/pipeline/example-get-started/mlmd")
    return templates.TemplateResponse('execution.html',{'request':request,'exec_df':execution_df})

@app.get("/display_artifacts",response_class=HTMLResponse)
async def display_exec(request: Request):

    artifact_df=artifact("/home/abhinavchobey/hp_server/cmf/pipeline/example-get-started/mlmd")
    return templates.TemplateResponse('artifacts.html',{'request':request,'artifact_df':artifact_df})
