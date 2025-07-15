# cmf-server api's
import io
import time
import zipfile
from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import pandas as pd
from typing import List, Dict, Any, Optional
from cmflib.cmfquery import CmfQuery
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict
from server.app.get_data import (
    get_lineage_data,
    get_mlmd_from_server,
    get_artifact_types,
    get_all_artifact_ids,
    get_all_exe_ids,
    async_api,
    get_model_data

)
from server.app.query_execution_lineage_d3force import query_execution_lineage_d3force
from server.app.query_execution_lineage_d3tree import query_execution_lineage_d3tree
from server.app.query_artifact_lineage_d3tree import query_artifact_lineage_d3tree
from server.app.query_visualization_artifact_execution import query_visualization_artifact_execution
from server.app.db.dbconfig import get_db
from server.app.db.dbqueries import (
    fetch_artifacts,
    fetch_executions,
    register_server_details,
    get_registered_server_details,
    get_sync_status,
    update_sync_status
)
from pathlib import Path
import os
import json
import typing as t
from server.app.schemas.dataframe import (
    MLMDPushRequest,
    ServerRegistrationRequest, 
    AcknowledgeRequest,
    MLMDPullRequest,
    ArtifactRequest,
    ExecutionRequest,
)
import httpx
from jsonpath_ng.ext import parse
from cmflib.cmf_federation import update_mlmd

server_store_path = "/cmf-server/data/postgres_data"
query = CmfQuery(is_server=True)

#global variables
dict_of_art_ids = {}
dict_of_exe_ids = {}
pipeline_locks = {}
lock_counts: defaultdict[str, int] = defaultdict(int)
#lifespan used to prevent multiple loading and save time for visualization.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global dict_of_art_ids
    global dict_of_exe_ids
    
    if os.path.exists(server_store_path):
        # loaded execution ids with names into memory
        dict_of_exe_ids = await async_api(get_all_exe_ids, query)
        # loaded artifact ids into memory
        dict_of_art_ids = await async_api(get_all_artifact_ids, query, dict_of_exe_ids)
    yield
    dict_of_art_ids.clear()
    dict_of_exe_ids.clear()

app = FastAPI(title="cmf-server", lifespan=lifespan)

BASE_PATH = Path(__file__).resolve().parent
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")

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
    status = "unknown_error"
    req_info = info.model_dump()  # Serializing the input data into a dictionary using model_dump()
    pipeline_name = req_info.get("pipeline_name", "")
    if pipeline_name not in pipeline_locks:    # create lock object for pipeline if it doesn't exists in lock
        pipeline_locks[pipeline_name] = asyncio.Lock()
    pipeline_lock = pipeline_locks[pipeline_name]   
    lock_counts[pipeline_name] += 1 # increment lock count by 1 if pipeline going to enter inside lock section
    async with pipeline_lock:
        try:
            status = await async_api(update_mlmd, query, req_info["json_payload"], pipeline_name, "push", req_info["exec_uuid"])
            if status == "invalid_json_payload":
                # Invalid JSON payload, return 400 Bad Request
                raise HTTPException(status_code=400, detail="Invalid JSON payload. The pipeline name is missing.")           
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
@app.post("/mlmd_pull", response_class=HTMLResponse)
async def mlmd_pull(info: MLMDPullRequest):
    pipeline_name = info.pipeline_name
    exec_uuid = info.exec_uuid
    last_sync_time = info.last_sync_time
    print("mlmd pull started")
    print("......................")
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    if pipeline_name:
        # checks if pipeline exists
        await check_pipeline_exists(pipeline_name)
        #json_payload values can be json data, none or no_exec_id.
        json_payload= await async_api(get_mlmd_from_server, query, pipeline_name, exec_uuid, last_sync_time, dict_of_exe_ids)
    else:
        json_payload = await async_api(get_mlmd_from_server, query, None, None, last_sync_time)

    if json_payload == None:
        raise HTTPException(status_code=406, detail=f"Pipeline {pipeline_name} not found.")
    return json_payload


@app.get("/artifacts/{pipeline_name}/{artifact_type}")
async def get_artifacts(
    pipeline_name: str, 
    artifact_type: str, 
    query_params: ArtifactRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):

    filter_value = query_params.filter_value
    active_page = query_params.active_page
    sort_field = query_params.sort_field
    sort_order = query_params.sort_order
    record_per_page = query_params.record_per_page

    """Retrieve paginated artifacts with filtering, sorting, and full-text search."""
    return await fetch_artifacts(db, pipeline_name, artifact_type, filter_value, active_page, record_per_page, sort_field, sort_order)


# api to display executions available in mlmd file[from postgres]
@app.get("/executions/{pipeline_name}")
async def execution(request: Request,
                   pipeline_name: str,
                   query_params: ExecutionRequest = Depends(),
                   db: AsyncSession = Depends(get_db)
                   ):
    filter_value = query_params.filter_value
    active_page = query_params.active_page
    sort_order = query_params.sort_order
    sort_field = query_params.sort_field
    record_per_page = query_params.record_per_page

    """Retrieve paginated executions with filtering, sorting, and full-text search."""
    return await fetch_executions(db, pipeline_name, filter_value, active_page, record_per_page, sort_field, sort_order)
    

# api to display executions available in mlmd file[from postgres]
@app.get("/executions/{pipeline_name}")
async def execution(request: Request,
                   pipeline_name: str,
                   active_page: int = Query(1, description="Page number", gt=0),
                   filter_value: str = Query("", description="Search based on value"),  
                   sort_order: str = Query("asc", description="Sort by context_type(asc or desc)"),
                   db: AsyncSession = Depends(get_db)
                   ):
    """Retrieve paginated executions with filtering, sorting, and full-text search."""
    return await fetch_executions(db, pipeline_name, filter_value, active_page, 5, sort_order)
    

@app.get("/list-of-executions/{pipeline_name}")
async def list_of_executions(request: Request, pipeline_name: str):
    '''
      This api's returns list of execution types.

    '''
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await async_api(get_lineage_data, query, pipeline_name, "Execution", dict_of_art_ids, dict_of_exe_ids)
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
    response = await async_api(query_execution_lineage_d3tree, query, pipeline_name, dict_of_exe_ids, uuid)
    return response
    

@app.get("/artifact-lineage/tangled-tree/{pipeline_name}")
async def artifact_lineage_tangled(request: Request, pipeline_name: str) -> Optional[List[List[Dict[str, Any]]]]:
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
    response = await async_api(query_artifact_lineage_d3tree, query, pipeline_name, dict_of_art_ids)        
    return response


#This api's returns list of artifact types.
@app.get("/artifact_types")
async def artifact_types():
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    artifact_types = await async_api(get_artifact_types, query)
    if "Environment" in artifact_types:
            artifact_types.remove("Environment")
    return artifact_types


@app.get("/pipelines")
async def pipelines(request: Request):
    # checks if mlmd file exists on server
    if os.path.exists(server_store_path):
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
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded")
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
    model_data_df, model_exe_df, model_input_art_df, model_output_art_df  = await get_model_data(query, modelId)
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
    response = await query_visualization_artifact_execution(query, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
    return response


# Rest api is for pushing python env to upload python env
@app.post("/python-env")
async def upload_python_env(request:Request, file: UploadFile = File(..., description="The file to upload")):
    try:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded")
        file_path = os.path.join("/cmf-server/data/env/", os.path.basename(file.filename))
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

# Rest api to push the label to /cmf-server/data/labels dir.
@app.post("/label")
async def upload_label(request:Request, file: UploadFile = File(..., description="The file to upload")):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided.")
        
        # Construct the full file path in /server/data/labels
        labels_dir = "/cmf-server/data/labels"
        file_path = os.path.join(labels_dir, os.path.basename(file.filename))
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Check if the file already exists
        if os.path.exists(file_path):
            return {"message": f"File '{file.filename}' already exists at {labels_dir}. Skipping upload."}


        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return {"message": f"File '{file.filename}' uploaded successfully to {labels_dir}."}
    
    except Exception as e:
        return {"error": f"Failed to up load file: {e}"}
    

# Rest api to fetch the label data from the /cmf-server/data/labels folder
@app.get("/label-data", response_class=PlainTextResponse)
async def get_label_data(file_name: str) -> str:
    """
    API endpoint to fetch the content of a requirements file.

    Args:
        file_name (str): The name of the file to be fetched. Must end with .csv.

    Returns:
        str: The content of the file as plain text.

    Raises:
        HTTPException: If the file does not exist or the extension is unsupported.
    """
    
    # Check if the file exists
    file_path = os.path.join("/cmf-server/data/labels/", os.path.basename(file_name))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Read and return the file content as plain text
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.post("/register-server")
async def register_server(request: ServerRegistrationRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Access the data from the Pydantic model
        server_name = request.server_name
        host_info = request.host_info

        # Step 1: Send a request to the target server
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"http://{host_info}:8080/acknowledge",
                    json={"server_name": server_name, "host_info": host_info}
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Target server did not respond successfully")
                target_server_data = response.json()
            except httpx.RequestError:
                raise HTTPException(status_code=500, detail="Target server is not reachable")

        # Check user is registring with own details
        if host_info in [my_ip, hostname, "127.0.0.1", "localhost"]:
            # Restrict the user from registering with own details
            return {"message": "Registration failed: Cannot register the server with its own details."}

        return await register_server_details(db, server_name, host_info)
    
    except HTTPException as e:
        # Re-raise known error without wrapping
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register server: {e}")
    

@app.post("/acknowledge")
async def acknowledge(request: AcknowledgeRequest):
    # Acknowledge the connection setup
    return {
        "message": f"Hi, I acknowledge your request.",
    }


async def server_mlmd_pull(host_info, last_sync_time):
    """
    Fetch mlmd data from a specified server.

    Args:
        host_info (str): The host information (IP or hostname) of the target server.
        last_sync_time (int): The last sync time in milliseconds since epoch.

    Returns:
        dict: The mlmd data fetched from the specified server.

    Raises:
        HTTPException: If the server is not reachable or an error occurs during the request.
    """
    try:
        # Step 1: Send a request to the target server to fetch mlmd data
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(f"http://{host_info}:8080/mlmd_pull", json={'last_sync_time': last_sync_time})

                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Target server did not respond successfully")

                json_payload = response.json()
                python_env_store_path = "/cmf-server/data/env"

                if last_sync_time:
                    # Extract the Environment file names from the JSON payload
                    data = json_payload
                    jsonpath_expr = parse('$..events[?(@.artifact.type == "Environment")].artifact.name')
                    environment_names = {match.value.split(":")[0].split("/")[-1] for match in jsonpath_expr.find(data)}

                    # Check if the list is empty or not
                    # if list is empty then no need to download the zip file
                    if len(environment_names) == 0: 
                        print("No Environment files are found inside json payload.")
                        return json_payload

                    list_of_files = list(environment_names)
                    # Added list_of_files to the request as a optional query parameter 
                    python_env_zip = await client.get(f"http://{host_info}:8080/download-python-env", params=list_of_files)
                else:
                    python_env_zip = await client.get(f"http://{host_info}:8080/download-python-env", params=None)

                if python_env_zip.status_code == 200:
                    try:
                        # Create the directory if it doesn't exist
                        os.makedirs(python_env_store_path, exist_ok=True)

                        # Unzip the zip file content
                        with zipfile.ZipFile(io.BytesIO(python_env_zip.content)) as zf:
                            # Extract all files to a temporary directory
                            temp_dir = os.path.join(python_env_store_path, "temp_extracted")
                            os.makedirs(temp_dir, exist_ok=True)
                            zf.extractall(temp_dir)

                            # Move all extracted files to the target directory
                            for root, dirs, files in os.walk(temp_dir):
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dest_file = os.path.join(python_env_store_path, file)
                                    try:
                                        os.rename(src_file, dest_file)
                                        print(f"Moved {src_file} to {dest_file}")
                                    except Exception as e:
                                        print(f"Failed to move {src_file} to {dest_file}: {e}")

                            # Clean up the temporary directory
                            os.rmdir(temp_dir)
                        # print("Storing at:", os.path.abspath(python_env_store_path))
                        # print("Files in target directory:", os.listdir(python_env_store_path))
                        print("All files stored successfully.")
                    except Exception as e:
                        print(f"Error during file extraction or storage: {e}")
                else:
                    print(f"Failed to download ZIP file. Status code: {python_env_zip.status_code}")
            except httpx.RequestError:
                raise HTTPException(status_code=500, detail="Target server is not reachable")
        return json_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch mlmd data: {e}")


@app.post("/sync")
async def sync_metadata(request: ServerRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """
    Synchronize metadata for a registered server.

    Args:
        request (ServerRegistrationRequest): The request containing server details.

    Returns:
        dict: A response containing the sync status and last sync time.

    Raises:
        HTTPException: If the server is not found or an error occurs during synchronization.
    """
    try:
        # Access the data from the Pydantic model
        server_name = request.server_name
        host_info = request.host_info

        # Fetch the server details from the database
        row = await get_sync_status(db, server_name, host_info)

        if not row:
            raise HTTPException(status_code=404, detail="Server not found in the registered servers list")

        last_sync_time = row[0]['last_sync_time']
        current_utc_epoch_time = int(time.time() * 1000)

        # Call the function to fetch the JSON payload
        json_payload = await server_mlmd_pull(host_info, last_sync_time)      


        # Use the JSON payload in json_data
        json_data = {
            "exec_uuid": None,
            "json_payload": json.dumps(json_payload),
            "pipeline_name": None
        }

        # Ensure the pipeline name in req_info matches the one in the JSON payload to maintain data integrity
        pipelines = json_payload.get("Pipeline", []) # Extract "Pipeline" list, default to empty list if missing
        # pipelines contain full mlmd data with the tag - 'Pipeline'
        # print("type of pipelines = ", type(pipelines))
        # tell us number of pipelines
        len_pipelines = len(pipelines)
        pipeline_names = []

        if not pipelines:
            return {
                "message": "Nothing to sync",
                "status": "success",
                "last_sync_time": current_utc_epoch_time
            }

        # in case of push check pipeline name exists inside mlmd_data
        pipeline_names = [pipeline.get("name") for pipeline in pipelines]

        # Push the JSON payload to the host server
        status = await async_api(update_mlmd, query, json_data["json_payload"], None, "push", None)
        if status == "invalid_json_payload":
            # Invalid JSON payload, return 400 Bad Request
            raise HTTPException(status_code=400, detail="Invalid JSON payload. The pipeline name is missing.")           
        if status == "version_update":
            # Raise an HTTPException with status code 422
            raise HTTPException(status_code=422, detail="version_update")
        global dict_of_art_ids
        global dict_of_exe_ids
        message = "Nothing to sync."
        if status != "exists":
            if not last_sync_time:
                # this is not completely correct 
                # as before we do the sync first time, it is entirely possible that there exists a 
                # pipeline on the server 1  - test this scenario
                message = f"Host server is syncing with the selected server '{server_name}' at address '{host_info}' for the first time."
                for pipeline_name in pipeline_names:
                    dict_of_exe_ids = get_all_exe_ids(query)
                    dict_of_art_ids = get_all_artifact_ids(query, dict_of_exe_ids)
            else:
                message = f"Host server is being synced with the selected server '{server_name}' at address '{host_info}'."
                for pipeline_name in pipeline_names:
                    update_global_exe_dict(pipeline_name)
                    update_global_art_dict(pipeline_name)

        # Update the last_sync_time in the database only if sync status is successful
        if status == "success":
            await update_sync_status(db, current_utc_epoch_time, server_name, host_info)
        return {
            "message": message,
            "status": status,
            "last_sync_time": current_utc_epoch_time
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to sync metadata: {e}")


@app.get("/server-list")
async def server_list(db: AsyncSession = Depends(get_db)):
    rows = await get_registered_server_details(db)
    return rows


@app.get("/download-python-env")
def download_python_env(request: Request, list_of_files: Optional[list[str]] = Query(None)):
    """
    API endpoint to compress and download the entire folder as a ZIP file.
    """
    try:
        DIRECTORY = "/cmf-server/data/env/"  # Directory to be compressed
        # Check if the directory exists
        if not os.path.exists(DIRECTORY):
            return {"error": "Directory does not exist"}

        # Determine files to include in the ZIP
        files_to_zip = []
        # if list_of_files is provided, include only those files
        # else include all files in the directory
        if list_of_files:
            for file_name in list_of_files:
                file_path = os.path.join(DIRECTORY, file_name)
                if os.path.exists(file_path):
                    files_to_zip.append((file_path, file_name))
                else:
                    return {"error": f"File {file_name} does not exist"}
        else:
            if not os.listdir(DIRECTORY):
                return {"error": "Directory is empty"}
            for root, _, files in os.walk(DIRECTORY):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, DIRECTORY)
                    files_to_zip.append((file_path, arcname))

        # Create and send the ZIP file 
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, arcname in files_to_zip:
                zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={'python_env_files.zip' if list_of_files else 'python_env_folder.zip'}"
            }
        )
    except Exception as e:
        return {"error": str(e)}


async def update_global_art_dict(pipeline_name):
    global dict_of_art_ids
    output_dict = await async_api(get_all_artifact_ids, query, dict_of_exe_ids, pipeline_name)
    dict_of_art_ids[pipeline_name]=output_dict[pipeline_name]
    return


async def update_global_exe_dict(pipeline_name):
    global dict_of_exe_ids
    output_dict = await async_api(get_all_exe_ids, query, pipeline_name)
    dict_of_exe_ids[pipeline_name] = output_dict[pipeline_name]  
    return


# Function to checks if mlmd file exists on server
async def check_mlmd_file_exists():
    if not os.path.exists(server_store_path):
        print(f"{server_store_path} file doesn't exist.")
        raise HTTPException(status_code=404, detail=f"{server_store_path} file doesn't exist.")


# Function to check if the pipeline exists
async def check_pipeline_exists(pipeline_name):
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
