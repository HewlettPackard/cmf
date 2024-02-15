# cmf-server api's
from fastapi import FastAPI, Request, status, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
import pandas as pd

from cmflib import cmfquery, cmf_merger
from server.app.get_data import (
    get_artifacts,
    get_lineage_img_path,
    create_unique_executions,
    get_mlmd_from_server,
    get_artifact_types,
    get_all_artifact_ids,
    get_all_exe_ids,
    get_executions_by_ids
)
from server.app.query_visualization import query_visualization

from pathlib import Path
import os
import json

server_store_path = "/cmf-server/data/mlmd"

dict_of_art_ids = {}
dict_of_exe_ids = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dict_of_art_ids
    global dict_of_exe_ids
    if os.path.exists(server_store_path):
        # loaded artifact ids into memory
        dict_of_art_ids = get_all_artifact_ids(server_store_path)
        # loaded execution ids with names into memory
        dict_of_exe_ids = get_all_exe_ids(server_store_path)
    yield
    dict_of_art_ids.clear()
    dict_of_exe_ids.clear()

app = FastAPI(title="cmf-server", lifespan=lifespan)

BASE_PATH = Path(__file__).resolve().parent
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")
server_store_path = "/cmf-server/data/mlmd"

my_ip = os.environ.get("MYIP", "127.0.0.1")
hostname = os.environ.get('HOSTNAME', "localhost")

if my_ip != "127.0.0.1":
    url="http://"+my_ip+":3000"
else:
    url="http://"+hostname+":3000"

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
    print("mlmd push started")
    print("......................")
    req_info = await info.json()
    status= create_unique_executions(server_store_path,req_info)
    # async function
    await update_global_art_dict()
    await update_global_exe_dict()
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
async def display_exec(
    request: Request,
    pipeline_name: str,
    page: int = Query(1, description="Page number", gt=0),
    per_page: int = Query(5, description="Items per page", le=100),
    sort_field: str = Query("Context_Type", description="Column to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_by: str = Query(None, description="Filter by column"),
    filter_value: str = Query(None, description="Filter value"),
    ):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        exe_ids_initial = dict_of_exe_ids[pipeline_name]
        # Apply filtering if provided
        if filter_by and filter_value:
            exe_ids_initial = exe_ids_initial[exe_ids_initial[filter_by].str.contains(filter_value, case=False)]
        # Apply sorting if provided
        exe_ids_sorted = exe_ids_initial.sort_values(by=sort_field, ascending=(sort_order == "asc"))
        exe_ids = exe_ids_sorted['id'].tolist()
        total_items = len(exe_ids)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        if total_items < end_idx:
            end_idx = total_items
        exe_ids_list = exe_ids[start_idx:end_idx]
        executions_df = get_executions_by_ids(server_store_path, pipeline_name, exe_ids_list)
        temp = executions_df.to_json(orient="records")
        executions_parsed = json.loads(temp)
        return {
            "total_items": total_items,
            "items": executions_parsed
        }
    else:
        return


@app.get("/display_lineage/{lineage_type}/{pipeline_name}")
async def display_lineage(request: Request,lineage_type: str, pipeline_name: str):
    # checks if mlmd file exists on server
    img_path=""
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            if lineage_type=="Artifacts":
                response=get_lineage_img_path(server_store_path,pipeline_name,"Artifacts")
            elif lineage_type=="Execution":
                response=get_lineage_img_path(server_store_path,pipeline_name,"Execution")
            else:
                response=get_lineage_img_path(server_store_path,pipeline_name,"ArtifactExecution")
            return response
        else:
            return f"Pipeline name {pipeline_name} doesn't exist."

    else:
        return 'mlmd does not exist!!'


# api to display artifacts available in mlmd
@app.get("/display_artifacts/{pipeline_name}/{type}")
async def display_artifact(
    request: Request,
    pipeline_name: str,
    type: str,   # type = artifact type
    page: int = Query(1, description="Page number", gt=0),
    per_page: int = Query(5, description="Items per page", le=100),
    sort_field: str = Query("name", description="Column to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_by: str = Query(None, description="Filter by column"),
    filter_value: str = Query(None, description="Filter value"),
    ):
    empty_df = pd.DataFrame()
    art_ids_dict = {}
    art_type = type
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        art_ids_dict = dict_of_art_ids[pipeline_name]
        if not art_ids_dict:
            return
        art_ids_initial = []
        if art_type in art_ids_dict:
            art_ids_initial = art_ids_dict[art_type]
        else:
            return
        # Apply filtering if provided
        if filter_by and filter_value:
            art_ids_initial = art_ids_initial[art_ids_initial[filter_by].str.contains(filter_value, case=False)]
        # Apply sorting if provided
        art_ids_sorted = art_ids_initial.sort_values(by=sort_field, ascending=(sort_order == "asc"))
        art_ids = art_ids_sorted['id'].tolist()
        total_items = len(art_ids)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        if total_items < end_idx:
            end_idx = total_items
        artifact_id_list = list(art_ids)[start_idx:end_idx]
        artifact_df = get_artifacts(server_store_path, pipeline_name, art_type, artifact_id_list)
        data_paginated = artifact_df
        return {
            "total_items": total_items,
            "items": data_paginated
        }
    else:
        return f"{server_store_path} file doesn't exist."



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



async def update_global_art_dict():
    global dict_of_art_ids
    output_dict = get_all_artifact_ids(server_store_path)
    dict_of_art_ids = output_dict
    return


async def update_global_exe_dict():
    global dict_of_exe_ids
    output_dict = get_all_exe_ids(server_store_path)
    dict_of_exe_ids = output_dict
    return
