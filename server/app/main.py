from fastapi import FastAPI,Request
from server.app.mlmd import merge_mlmd
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from get_executions import index
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


@app.get("/display_exec",response_class=HTMLResponse)
async def display_exec(request: Request):
    # with open('execution.json','r') as f:
    #     data=json.load(f)
    #
    df=index("/home/abhinavchobey/server_demo/cmf/pipeline_data/example_get_started/mlmd")
    return templates.TemplateResponse('index.html',{'request':request,'df':df})
