# cmf-server api's
from fastapi import FastAPI, Request, APIRouter, status, HTTPException, Query
from contextlib import asynccontextmanager
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from cmflib import cmfquery, cmf_merger
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from server.app.get_data import get_executions, get_artifacts, get_lineage_img_path, create_unique_executions, get_mlmd_from_server, get_artifact_types, get_all_artifact_ids
from server.app.query_visualization import query_visualization
from server.app.schemas.dataframe import ExecutionDataFrame
from pathlib import Path
import os
import json

server_store_path = "/cmf-server/data/mlmd"

dict_of_art_ids = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    #loaded artifact ids into memory
    global dict_of_art_ids
    dict_of_art_ids = get_all_artifact_ids(server_store_path)
    #print(dict_of_art_ids)
    yield
    dict_of_art_ids.clear()

app = FastAPI(title="cmf-server", lifespan=lifespan)

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH/"template"))
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")
server_store_path = "/cmf-server/data/mlmd"
if os.environ.get("MYIP") != "127.0.0.1":
    url="http://"+os.environ.get('MYIP')+":3000"
else:
    url="http://"+os.environ.get('HOSTNAME')+":3000"

origins = [
    "http://localhost:3000",
    "localhost:3000",
    url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root(request: Request):
    return {"cmf-server"}


# api to post mlmd file to cmf-server
@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info = await info.json()
    status= create_unique_executions(server_store_path,req_info)
    # check how to make it async 
    global dict_of_art_ids
    result_dict = dict_of_art_ids.copy()
    output_dict = get_all_artifact_ids(server_store_path)
    for key, value in output_dict.items():
        if key in result_dict:
            result_dict[key].update(value)
        else:
            result_dict[key] = value.copy()
    dict_of_art_ids = result_dict
    #print("print dict_ids after the mlmd push ")
    #print(dict_of_art_ids)
    return {"status": status, "data": req_info}


# api to get mlmd file from cmf-server
@app.get("/mlmd_pull/{pipeline_name}",response_class=HTMLResponse)
async def mlmd_pull(info: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    req_info = await info.json()
    if os.path.exists(server_store_path):
        json_payload= get_mlmd_from_server(server_store_path,pipeline_name,req_info['exec_id'])
    else:
        print("No mlmd file submitted.")
        json_payload = ""
    return json_payload


# api to display executions available in mlmd
@app.get("/display_executions/{pipeline_name}")
async def display_exec(request: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        execution_df = get_executions(server_store_path, pipeline_name)
    tempOut = execution_df.to_json(orient="records")
    parsed = json.loads(tempOut)
    return parsed

@app.get("/display_lineage/{pipeline_name}")
async def display_lineage(request: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    img_path=""
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            response=get_lineage_img_path(server_store_path,pipeline_name)
            return response
        else:
            return f"Pipeline name {pipeline_name} doesn't exist."

    else:
        return 'mlmd doesnt exist'

# api to display artifacts available in mlmd
@app.get("/display_artifacts/{pipeline_name}/{type}")
async def display_artifact(
    request: Request, 
    pipeline_name: str,
    type: str,   # type = artifact type 
    page: int = Query(1, description="Page number", gt=0),
    per_page: int = Query(10, description="Items per page", le=100),
    ):
    # checks if mlmd file exists on server
    artifact_id_set = dict_of_art_ids.get(pipeline_name, set())
    #print(type(artifact_id_set))
    #print(artifact_id_set)
    if not artifact_id_set:
       artifact_df = ""
       return artifact_df
    if os.path.exists(server_store_path):
        artifact_df = get_artifacts(server_store_path, pipeline_name, type, artifact_id_set)
        total_items = len(artifact_df)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        data_paginated = artifact_df[start_idx:end_idx]

        return {
            "total_items": total_items,
            "items": data_paginated
        }
        #return artifact_df
    else:
        artifact_df = ""
        return artifact_df

@app.get("/display_artifact_types")
async def display_artifact_types(request: Request):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        artifact_types = get_artifact_types(server_store_path)
        return artifact_types
    else:
        artifact_types = ""
        return


@app.get("/display_pipelines")
async def display_list_of_pipelines(request: Request):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        pipeline_names = query.get_pipeline_names()
        return pipeline_names
    else:
        print("No mlmd file submitted.")
        pipeline_names = []
        return pipeline_names

