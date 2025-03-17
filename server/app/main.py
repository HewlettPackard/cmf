# cmf-server api's
from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import pandas as pd
from typing import List, Dict, Any
from cmflib import cmfquery
import asyncio
import threading
from collections import defaultdict
from server.app.get_data import (
    get_artifacts,
    get_lineage_data,
    create_unique_executions,
    get_mlmd_from_server,
    get_artifact_types,
    get_all_artifact_ids,
    get_all_exe_ids,
    async_api,
    get_executions,
    get_model_data

)
from server.app.query_artifact_lineage_d3force import query_artifact_lineage_d3force
from server.app.query_execution_lineage_d3force import query_execution_lineage_d3force
from server.app.query_execution_lineage_d3tree import query_execution_lineage_d3tree
from server.app.query_artifact_lineage_d3tree import query_artifact_lineage_d3tree
from server.app.query_visualization_artifact_execution import query_visualization_artifact_execution
from cmflib.cmf_exception_handling import MlmdNotFoundOnServer
from pathlib import Path
import os
import json
import typing as t
from server.app.schemas.dataframe import MLMDPushRequest, ExecutionRequest, ArtifactRequest

server_store_path = "/cmf-server/data/mlmd"

dict_of_art_ids = {}
dict_of_exe_ids = {}
pipeline_locks = {}
lock_counts = defaultdict(int)
#lifespan used to prevent multiple loading and save time for visualization.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global dict_of_art_ids
    global dict_of_exe_ids
    if os.path.exists(server_store_path):
        # loaded execution ids with names into memory
        dict_of_exe_ids = await async_api(get_all_exe_ids, server_store_path)
        # loaded artifact ids into memory
        dict_of_art_ids = await async_api(get_all_artifact_ids, server_store_path, dict_of_exe_ids)
    yield
    dict_of_art_ids.clear()
    dict_of_exe_ids.clear()

app = FastAPI(title="cmf-server", lifespan=lifespan)

BASE_PATH = Path(__file__).resolve().parent
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")
server_store_path = "/cmf-server/data/mlmd"

my_ip = os.environ.get("MYIP", "127.0.0.1")
hostname = os.environ.get('HOSTNAME', "localhost")

#checking if IP or Hostname is provided,initializing url accordingly.
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
async def read_root(request: Request):
    return {"cmf-server"}


# api to post mlmd file to cmf-server
@app.post("/mlmd_push")
async def mlmd_push(info: MLMDPushRequest):
    print("mlmd push started")
    print("......................")
    req_info = info.model_dump()  # Serializing the input data into a dictionary using model_dump()
    pipeline_name = req_info["pipeline_name"]
    if pipeline_name not in pipeline_locks:    # create lock object for pipeline if it doesn't exists in lock
        pipeline_locks[pipeline_name] = asyncio.Lock()
    pipeline_lock = pipeline_locks[pipeline_name]   
    lock_counts[pipeline_name] += 1 # increment lock count by 1 if pipeline going to enter inside lock section
    async with pipeline_lock:
        try:
            status = await async_api(create_unique_executions, server_store_path, req_info)
            if status == "invalid_json_payload":
                # Invalid JSON payload, return 400 Bad Request
                raise HTTPException(status_code=400, detail="Invalid JSON payload. The pipeline name is missing.")           
            if status == "pipeline_not_exist":
                # Pipeline name does not exist in the server, return 404 Not Found
                raise HTTPException(status_code=404, detail=f"Pipeline name '{pipeline_name}' does not exist.")
            if status == "version_update":
                # Raise an HTTPException with status code 422
                raise HTTPException(status_code=422, detail="version_update")
            if status != "exists":
            # async function
                await update_global_exe_dict(pipeline_name)
                await update_global_art_dict(pipeline_name)
        finally:
            lock_counts[pipeline_name] -= 1  # Decrement the reference count after lock released
            if lock_counts[pipeline_name] == 0:   #if lock_counts of pipeline is zero means lock is release from it
                del pipeline_locks[pipeline_name]  # Remove the lock if it's no longer needed
                del lock_counts[pipeline_name]
    return {"status": status}


# api to get mlmd file from cmf-server
@app.get("/mlmd_pull/{pipeline_name}", response_class=HTMLResponse)
async def mlmd_pull(pipeline_name: str, exec_uuid: t.Optional[str]= None):
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    #json_payload values can be json data, NULL or no_exec_id.
    json_payload= await async_api(get_mlmd_from_server, server_store_path, pipeline_name, exec_uuid, dict_of_exe_ids)
    if json_payload == None:
            raise HTTPException(status_code=406, detail=f"Pipeline {pipeline_name} not found.")
    return json_payload


# api to display executions available in mlmd
@app.get("/executions/{pipeline_name}")
async def executions(
    request: Request,
    pipeline_name: str,
    query_params: ExecutionRequest = Depends()
    ):
    # Extract the query parameters from the query_params object
    page = query_params.page
    per_page = query_params.per_page
    sort_field = query_params.sort_field
    sort_order = query_params.sort_order
    filter_by = query_params.filter_by
    filter_value = query_params.filter_value
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    if pipeline_name in dict_of_exe_ids:
        try:
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
            executions_df = await async_api(get_executions, server_store_path, pipeline_name, exe_ids_list)
            temp = executions_df.to_json(orient="records")
            executions_parsed = json.loads(temp)
            return {
                "total_items": total_items,
                "items": executions_parsed
            }
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {"error": f"Failed to get executions available in mlmd: {e}"}
    else:
        print(f"Pipeline {pipeline_name} not found.")
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_name} not found.")


@app.get("/list-of-executions/{pipeline_name}")
async def list_of_executions(request: Request, pipeline_name: str):
    '''
      This api's returns list of execution types.

    '''
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await async_api(get_lineage_data, server_store_path, pipeline_name, "Execution", dict_of_art_ids, dict_of_exe_ids)
    return response

    
@app.get("/execution-lineage/tangled-tree/{uuid}/{pipeline_name}")
async def execution_lineage(request: Request, uuid: str, pipeline_name: str):
    '''
      returns dictionary of nodes and links for given execution_type.
      response = {
                   nodes: [{id:"",name:"",execution_uuid:""}],
                   links: [{source:1,target:4},{}],
                 } 
    '''
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await async_api(query_execution_lineage_d3tree, server_store_path, pipeline_name, dict_of_exe_ids,uuid)
    return response
    

# api to display artifacts available in mlmd
@app.get("/artifacts/{pipeline_name}/{type}")
async def artifacts(
    request: Request,
    pipeline_name: str,
    type: str,   # type = artifact type
    query_params: ArtifactRequest = Depends()
    ):
    # Extract the query parameters from the query_params object
    page = query_params.page
    per_page = query_params.per_page
    sort_field = query_params.sort_field
    sort_order = query_params.sort_order
    filter_by = query_params.filter_by
    filter_value = query_params.filter_value
    art_ids_dict = {}
    art_type = type
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    try:
        art_ids_dict = dict_of_art_ids[pipeline_name]
        if not art_ids_dict:
            return {               #return {items: None} so that GUI loads 
            "total_items": 0,      #empty page when art_ids_dict is {}
            "items": None
            }
        art_ids_initial = []
        if art_type in art_ids_dict:
            art_ids_initial = art_ids_dict[art_type]
        else:
            return {
            "total_items": 0,
            "items": None
        }
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
        artifact_df = await async_api(get_artifacts, server_store_path, pipeline_name, art_type, artifact_id_list)
        data_paginated = artifact_df
        #data_paginated is returned None if artifact df is None or {}
        #it will load empty page, without this condition it will load 
        #data of whichever artifact_type is loaded before this. 
        if artifact_df == None or artifact_df == {}:   
            data_paginated = None      
            total_items = 0
        return {
            "total_items": total_items,
            "items": data_paginated
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": f"Failed to get artifacts available in mlmd: {e}"}


@app.get("/artifact-lineage/tangled-tree/{pipeline_name}")
async def artifact_lineage(request: Request, pipeline_name: str) -> List[List[Dict[str, Any]]]:
    '''
      Returns:
      A nested list of dictionaries with 'id' and 'parents' keys.
      response = [
        [{'id': 'data.xml.gz:236d', 'parents': []}],
        [{'id': 'parsed/train.tsv:32b7', 'parents': ['data.xml.gz:236d']}, 
        ]
    '''
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await async_api(query_artifact_lineage_d3tree, server_store_path, pipeline_name, dict_of_art_ids)        
    return response


#This api's returns list of artifact types.
@app.get("/artifact_types")
async def artifact_types():
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    artifact_types = await async_api(get_artifact_types, server_store_path)
    if "Environment" in artifact_types:
            artifact_types.remove("Environment")
    return artifact_types


@app.get("/pipelines")
async def pipelines(request: Request):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        pipeline_names = query.get_pipeline_names()
        return pipeline_names
    else:
        print("No mlmd file submitted.")
        pipeline_names = []
        return pipeline_names


@app.post("/tensorboard")
async def upload_file(request:Request, pipeline_name: str = Query(..., description="Pipeline name"),
    file: UploadFile = File(..., description="The file to upload")):
    try:
        file_path = os.path.join("/cmf-server/data/tensorboard-logs", pipeline_name, file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"message": f"File '{file.filename}' uploaded successfully"}
    except Exception as e:
        return {"error": f"Failed to up load file: {e}"}


@app.get("/model-card")
async def model_card(request:Request, modelId: int, response_model=List[Dict[str, Any]]):
    json_payload_1 = ""
    json_payload_2 = ""
    json_payload_3 = ""
    json_payload_4 = ""
    model_data_df = pd.DataFrame()
    model_exe_df = pd.DataFrame()
    model_input_art_df = pd.DataFrame()
    model_output_art_df = pd.DataFrame()
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    model_data_df, model_exe_df, model_input_art_df, model_output_art_df  = await get_model_data(server_store_path, modelId)
    if not model_data_df.empty:
        result_1 = model_data_df.to_json(orient="records")
        json_payload_1 = json.loads(result_1)
    if not model_exe_df.empty:
        result_2 = model_exe_df.to_json(orient="records")
        json_payload_2 = json.loads(result_2)
    if not model_input_art_df.empty:
        result_3 =  model_input_art_df.to_json(orient="records")
        json_payload_3 = json.loads(result_3)
    if not model_output_art_df.empty:
        result_4 =  model_output_art_df.to_json(orient="records")
        json_payload_4 = json.loads(result_4)
    return [json_payload_1, json_payload_2, json_payload_3, json_payload_4]


@app.get("/artifact-execution-lineage/tangled-tree/{pipeline_name}")
async def artifact_execution_lineage(request: Request, pipeline_name: str):
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await query_visualization_artifact_execution(server_store_path, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
    return response

# Rest api is for pushing python env to upload python env
@app.post("/python-env")
async def upload_python_env(request:Request, file: UploadFile = File(..., description="The file to upload")):
    try:
        file_path = os.path.join("/cmf-server/data/env/",  os.path.basename(file.filename))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"message": f"File '{file.filename}' uploaded successfully"}
    except Exception as e:
        return {"error": f"Failed to up load file: {e}"}
    
# Rest api to fetch the env data from the /cmf-server/data/env folder
@app.get("/python-env", response_class=PlainTextResponse)
async def get_python_env(file_name: str) -> str:
    """
    API endpoint to fetch the content of a requirements file.

    Args:
        file_name (str): The name of the file to be fetched. Must end with .txt or .yaml.

    Returns:
        str: The content of the file as plain text.

    Raises:
        HTTPException: If the file does not exist or the extension is unsupported.
    """
    # Validate file extension
    if not (file_name.endswith(".txt") or file_name.endswith(".yaml")):
        raise HTTPException(
            status_code=400, detail="Unsupported file extension. Use .txt or .yaml"
        )
    
    # Check if the file exists
    file_path = os.path.join("/cmf-server/data/env/", os.path.basename(file_name))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Read and return the file content as plain text
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


async def update_global_art_dict(pipeline_name):
    global dict_of_art_ids
    output_dict = await async_api(get_all_artifact_ids, server_store_path, dict_of_exe_ids, pipeline_name)
    # type(dict_of_art_ids[pipeline_name]) = Dict[ <class 'pandas.core.frame.DataFrame'> ]
    dict_of_art_ids[pipeline_name]=output_dict[pipeline_name]
    return


async def update_global_exe_dict(pipeline_name):
    global dict_of_exe_ids
    output_dict = await async_api(get_all_exe_ids, server_store_path, pipeline_name)
    # type(dict_of_exe_ids[pipeline_name]) = <class 'pandas.core.frame.DataFrame'>
    dict_of_exe_ids[pipeline_name] = output_dict[pipeline_name]  
    return


# Function to checks if mlmd file exists on server
async def check_mlmd_file_exists():
    if not os.path.exists(server_store_path):
        print(f"{server_store_path} file doesn't exist.")
        raise HTTPException(status_code=404, detail=f"{server_store_path} file doesn't exist.")


# Function to check if the pipeline exists
async def check_pipeline_exists(pipeline_name):
    query = cmfquery.CmfQuery(server_store_path)
    if pipeline_name not in query.get_pipeline_names():
        print(f"Pipeline {pipeline_name} not found.")
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_name} not found.")


"""
This API is no longer in use within the project but is retained for reference or potential future use.
@app.get("/execution-lineage/force-directed-graph/{pipeline_name}/{uuid}")
async def execution_lineage(request: Request, pipeline_name: str, uuid: str):
    '''
      returns dictionary of nodes and links for given execution_type.
      response = {
                   nodes: [{id:"",name:"",execution_uuid:""}],
                   links: [{source:1,target:4},{}],
                 } 
    '''
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            response = await async_api(query_execution_lineage_d3force, server_store_path, pipeline_name, dict_of_exe_ids, uuid)
    else:
        response = None
    return response


@app.get("/artifact-lineage/force-directed-graph/{pipeline_name}")
async def artifact_lineage(request: Request, pipeline_name: str):
    '''
      This api returns dictionary of nodes and links for given pipeline.
      response = {
                   nodes: [{id:"",name:""}],
                   links: [{source:1,target:4},{}],
                 }

    '''
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
        query = cmfquery.CmfQuery(server_store_path)
        if (pipeline_name in query.get_pipeline_names()):
            response=await async_api(get_lineage_data, server_store_path, pipeline_name, "Artifacts", dict_of_art_ids, dict_of_exe_ids)
            return response
        else:
            return f"Pipeline name {pipeline_name} doesn't exist."

    else:
        return None
"""