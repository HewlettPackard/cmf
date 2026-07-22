# cmf-server api's
import io
import time
import zipfile
from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd
from typing import List, Dict, Any, Optional
from cmflib.cmfquery import CmfQuery
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict
from server.app.utils import extract_hostname, get_fqdn, convert_to_stage_json
from server.app.get_data import (
    get_mlmd_from_server,
    get_artifact_types,
    get_all_artifact_ids,
    get_all_exe_ids,
    async_api,
    get_model_data,
    executions_list,
    server_mlmd_pull,
    log_sync_attempt,
    compute_next_run_from_recurrence,
    compute_initial_next_run_utc,
)
from server.app.query_execution_lineage_d3tree import query_execution_lineage_d3tree
from server.app.query_artifact_lineage_d3tree import query_artifact_lineage_d3tree
from server.app.query_visualization_artifact_execution import query_visualization_artifact_execution
from server.app.db.dbconfig import get_db, init_db, async_session
from server.app.db.dbqueries import (
    fetch_unique_execution_stages,
    fetch_executions_by_stage,
    fetch_artifacts_by_stage,
    fetch_artifact_types_by_stage,
    register_server_details,
    get_registered_server_details,
    get_sync_status,
    update_sync_status,
    create_schedule,
    list_schedules,
    due_schedules,
    update_next_run,
    log_sync_run,
    list_sync_logs,
    get_completed_logs_by_server,
    get_registered_server_by_id,
    update_schedule_fields,
    delete_schedule,
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
    ScheduleCreateRequest,
    ArtifactByStageRequest,
    ExecutionByStageRequest,
)
import httpx
import socket
import dotenv
from jsonpath_ng.ext import parse
from cmflib.cmf_federation import update_mlmd
from datetime import datetime
from zoneinfo import ZoneInfo

dotenv.load_dotenv()

# server_store_path = "/cmf-server/data/postgres_data"
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

    # Initialize the database schema
    await init_db()

    if query:
        # loaded execution ids with names into memory
        dict_of_exe_ids = await async_api(get_all_exe_ids, query)
        # loaded artifact ids into memory
        dict_of_art_ids = await async_api(get_all_artifact_ids, query, dict_of_exe_ids)
    # Start background scheduler task
    app.state.scheduler_task = asyncio.create_task(schedule_runner())
    yield
    # Cancel scheduler on shutdown
    # If FastAPI is down, no scheduled sync runs.
    # On restart, the scheduler resumes from DB state.
    # Missed schedules are not deleted or skipped automatically.
    # One-time schedules run once after restart if overdue.
    # Periodic schedules keep running and may attempt backlog catch-up.
    # There is no explicit restart cleanup/update pass for scheduled_syncs.
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
    dict_of_art_ids.clear()
    dict_of_exe_ids.clear()

app = FastAPI(title="cmf-server", lifespan=lifespan, root_path="/api")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

BASE_PATH = Path(__file__).resolve().parent
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")

REACT_APP_CMF_API_URL = os.getenv("REACT_APP_CMF_API_URL", "http://localhost:8080")

LOCAL_ADDRESSES = set()
LOCAL_ADDRESSES.update(["127.0.0.1", "localhost"])
hostname = extract_hostname(REACT_APP_CMF_API_URL)
LOCAL_ADDRESSES.add(hostname)
# Adding hostname if IP is given
LOCAL_ADDRESSES.add(get_fqdn(hostname))
print("Local addresses= ", LOCAL_ADDRESSES)


async def schedule_runner():
    """Input: none
    Output: none (runs continuously)
    Description: Background loop that executes due schedules using 3-stage server validation.
    Step 1: Query all due schedules using current UTC epoch milliseconds.
    Step 2: Check if server record exists in DB (registration check).
            - If NOT registered: permanent config issue -> deactivate ALL schedule types.
    Step 3: Check if the registered server is currently reachable (liveness check).
            - If NOT alive: transient outage:
                one-time  -> deactivate (missed its window, cannot retry)
                periodic  -> log failure, compute next run, keep active for retry
    Step 4: Server is registered AND alive -> perform sync, log result, advance schedule.
    Step 5: Sleep 30 seconds and repeat.
    Example: periodic schedule with unreachable server logs failure and reschedules."""
    while True:
        try:
            async with async_session() as db:
                now_ms = int(time.time() * 1000)
                schedules = await due_schedules(db, now_ms)
                for sch in schedules:
                    sync_type = "schedule_once" if sch.get("one_time") else "periodic"

                    # Stage 1: Registration check
                    # Checks whether the server record still exists in the registered_servers
                    # table. A missing record is a permanent configuration issue (server was
                    # deleted/deregistered), not a temporary outage. Deactivate all schedule
                    # types so we do not keep polling a server that no longer exists.
                    server = await get_registered_server_by_id(db, sch["server_id"])
                    if not server:
                        await log_sync_run(
                            db, sch["id"], now_ms, "failed",
                            "Server record not found in registered servers. Schedule deactivated.",
                            sync_type,
                        )
                        await update_schedule_fields(db, schedule_id=sch["id"], active=False, status="failed")
                        continue

                    # Stage 2: Liveness check
                    # Server is registered. Now check if it is currently reachable by sending
                    # a lightweight ping to /api/acknowledge (5-second timeout).
                    # This distinguishes transient network/outage failures from config errors.
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.post(
                                f"{server['host_info']}/api/acknowledge",
                                json={"server_name": server["server_name"], "server_url": server["host_info"]}
                            )
                        server_alive = response.status_code == 200
                    except Exception:
                        server_alive = False
                    if not server_alive:
                        if sch.get("one_time"):
                            # One-time sync missed its scheduled window during outage.
                            # It will not retry automatically -> deactivate.
                            await log_sync_run(
                                db, sch["id"], now_ms, "failed",
                                "Server is not reachable. One-time sync deactivated.",
                                sync_type,
                            )
                            await update_schedule_fields(db, schedule_id=sch["id"], active=False, status="failed")
                        else:
                            # Periodic sync: transient outage, keep schedule alive and
                            # advance next_run_time_utc so it retries at the next interval.
                            await log_sync_run(
                                db, sch["id"], now_ms, "failed",
                                "Server is not reachable. Will retry at next scheduled run.",
                                sync_type,
                            )
                            next_ms = await compute_next_run_from_recurrence(
                                sch["next_run_time_utc"],
                                sch["timezone"],
                                sch["recurrence_mode"],
                                interval_unit=sch.get("interval_unit"),
                                interval_value=sch.get("interval_value"),
                                daily_time=sch.get("daily_time"),
                                weekly_day=sch.get("weekly_day"),
                                weekly_time=sch.get("weekly_time"),
                            )
                            await update_next_run(db, sch["id"], next_ms)
                            await update_schedule_fields(db, schedule_id=sch["id"], status="active")
                        continue

                    # Stage 3: Server is registered and alive -> perform sync
                    req = ServerRegistrationRequest(server_name=server["server_name"], server_url=server["host_info"])
                    status_msg = ""
                    status = "failed"
                    await update_schedule_fields(db, schedule_id=sch["id"], status="running")
                    try:
                        result = await sync_metadata(request=req, db=db, skip_logging=True)
                        status = result.get("status", "unknown")
                        status_msg = result.get("message", "")
                    except HTTPException as he:
                        status = "failed"
                        status_msg = he.detail if isinstance(he.detail, str) else str(he.detail)
                    except Exception as e:
                        status = "failed"
                        status_msg = f"Unexpected error: {e}"

                    await log_sync_run(db, sch["id"], now_ms, status, status_msg, sync_type)
                    if sch.get("one_time"):
                        # One-time schedules always deactivate after their single attempt.
                        await update_schedule_fields(db, schedule_id=sch["id"], active=False, status="completed")
                    else:
                        # Periodic: advance to next run time and keep active.
                        next_ms = await compute_next_run_from_recurrence(
                            sch["next_run_time_utc"],
                            sch["timezone"],
                            sch["recurrence_mode"],
                            interval_unit=sch.get("interval_unit"),
                            interval_value=sch.get("interval_value"),
                            daily_time=sch.get("daily_time"),
                            weekly_day=sch.get("weekly_day"),
                            weekly_time=sch.get("weekly_time"),
                        )
                        await update_next_run(db, sch["id"], next_ms)
                        await update_schedule_fields(db, schedule_id=sch["id"], status="active")
        except Exception as e:
            # Prevent scheduler from crashing; log to stdout
            print(f"Scheduler error: {e}")

        await asyncio.sleep(30)


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


# Deprecated legacy endpoint (unused by current grid UI).
# Stage-based endpoint replacement: /artifacts-by-stage/{pipeline_name}
# @app.get("/artifacts/{pipeline_name}/{artifact_type}")
# async def get_artifacts(
#     pipeline_name: str,
#     artifact_type: str,
#     query_params: ArtifactRequest = Depends(),
#     db: AsyncSession = Depends(get_db)
# ):
#
#     filter_value = query_params.filter_value
#     active_page = query_params.active_page
#     sort_field = query_params.sort_field
#     sort_order = query_params.sort_order
#     record_per_page = query_params.record_per_page
#
#     """Retrieve paginated artifacts with filtering, sorting, and full-text search."""
#     return await fetch_artifacts(db, pipeline_name, artifact_type, filter_value, active_page, record_per_page, sort_field, sort_order)


# Deprecated legacy endpoint (unused by current grid UI).
# Stage-based endpoint replacement: /executions-by-stage/{pipeline_name}
# @app.get("/executions/{pipeline_name}")
# async def execution(request: Request,
#                    pipeline_name: str,
#                    query_params: ExecutionRequest = Depends(),
#                    db: AsyncSession = Depends(get_db)
#                    ):
#     filter_value = query_params.filter_value
#     active_page = query_params.active_page
#     sort_order = query_params.sort_order
#     sort_field = query_params.sort_field
#     record_per_page = query_params.record_per_page
#
#     """Retrieve paginated executions with filtering, sorting, and full-text search."""
#     return await fetch_executions(db, pipeline_name, filter_value, active_page, record_per_page, sort_field, sort_order)
    

@app.get("/executions-by-stage/{pipeline_name}")
async def get_executions_by_stage(
    pipeline_name: str,
    query_params: ExecutionByStageRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve executions filtered by pipeline and stage name (Context_Type).
    
    Args:
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter executions
        active_page: Page number for pagination
        record_per_page: Number of records per page
        
    Returns:
        Dictionary with total_items and list of executions with their properties
        
    Example response:
    {
        "total_items": 10,
        "items": [
            {
                "execution_id": 2,
                "execution_properties": [...]
            }
        ]
    }
    """
    stage_name = query_params.stage_name
    active_page = query_params.active_page
    record_per_page = query_params.record_per_page
    sort_order = query_params.sort_order
    filter_value = query_params.filter_value

    return await fetch_executions_by_stage(db, pipeline_name, stage_name, active_page, record_per_page, sort_order, filter_value)


@app.get("/pipeline-stages/{pipeline_name}")
async def get_pipeline_stages(
    pipeline_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve unique artifact stages (Context_Type values) for a given pipeline.
    Since artifacts inherit stages from executions, this uses the same query as execution stages.
    
    Args:
        pipeline_name: Name of the pipeline to get stages from
        
    Returns:
        Dictionary with pipeline_name, list of unique stages, and total count
        
    Example response:
    {
        "stages": ["Test-env/Prepare", "Test-env/Train", "Test-env/Evaluate"],
        "total_stages": 3
    }
    """
    return await fetch_unique_execution_stages(db, pipeline_name)


@app.get("/artifact-types-by-stage/{pipeline_name}")
async def get_artifact_types_by_stage(
    pipeline_name: str,
    stage_name: str = Query(..., description="Stage name (Context_Type value)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve unique artifact types available in a specific stage of a pipeline.
    
    Args:
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter by
        
    Returns:
        List of unique artifact type names
        
    Example response:
    ["Dataset", "Metrics", "Model"]
    """
    return await fetch_artifact_types_by_stage(db, pipeline_name, stage_name)


@app.get("/artifacts-by-stage/{pipeline_name}")
async def get_artifacts_by_stage(
    pipeline_name: str,
    query_params: ArtifactByStageRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve artifacts filtered by pipeline, stage, and artifact type.
    
    Args:
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter artifacts
        artifact_type: Type of artifacts to retrieve
        sort_order: Sort order (asc or desc)
        active_page: Page number for pagination
        record_per_page: Number of records per page
        filter_value: Search filter value
        sort_field: Field to sort by
        
    Returns:
        Dictionary with total_items and list of artifacts with their properties
        
    Example response:
    {
        "total_items": 10,
        "items": [
            {
                "artifact_id": 5,
                "name": "dataset.csv",
                "create_time_since_epoch": 1234567890,
                "artifact_properties": [...]
            }
        ]
    }
    """
    stage_name = query_params.stage_name
    artifact_type = query_params.artifact_type
    filter_value = query_params.filter_value
    active_page = query_params.active_page
    record_per_page = query_params.record_per_page
    sort_field = query_params.sort_field
    sort_order = query_params.sort_order

    return await fetch_artifacts_by_stage(
        db=db,
        pipeline_name=pipeline_name,
        stage_name=stage_name,
        artifact_type=artifact_type,
        filter_value=filter_value,
        active_page=active_page,
        record_per_page=record_per_page,
        sort_column=sort_field,
        sort_order=sort_order
    )


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
    if query:
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
    model_data_df, model_exe_df, model_input_art_df, model_output_art_df  = await async_api(get_model_data, query, modelId)
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
    response = await async_api(query_visualization_artifact_execution, query, pipeline_name, dict_of_art_ids, dict_of_exe_ids)
    return response


@app.get("/hierarchical-lineage/tangled-tree/{pipeline_name}")
async def hierarchical_lineage(request: Request, pipeline_name: str):
    """
    Return MLMD data for the given pipeline converted into the UI `stage.json` schema.
    """
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)

    # Pull MLMD JSON for the pipeline
    json_payload = await async_api(get_mlmd_from_server, query, pipeline_name, None, None, dict_of_exe_ids)

    if json_payload is None:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_name} not found or has no MLMD data.")

    try:
        if isinstance(json_payload, str):
            json_payload = json.loads(json_payload)
        converted = convert_to_stage_json(json_payload, pipeline_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert MLMD to stage JSON: {e}")

    return converted


@app.get("/list-of-executions/{pipeline_name}")
async def list_of_executions(request: Request, pipeline_name: str):
    '''
      This api's returns list of execution types.

    '''
    # checks if mlmd file exists on server
    await check_mlmd_file_exists()
    # checks if pipeline exists
    await check_pipeline_exists(pipeline_name)
    response = await async_api(executions_list, query, pipeline_name, dict_of_exe_ids)
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
        server_url = request.server_url
        server = extract_hostname(server_url)


        # Check user is registering with own details
        if server in LOCAL_ADDRESSES:
            return {"message": "Registration failed: Cannot register the server with its own details."}

        # Step 1: Send a request to the target server for acknowledgement
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{server_url}/api/acknowledge",
                    json={"server_name": server_name, "server_url": server_url}
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Target server did not respond successfully")
                target_server_data = response.json()
            except httpx.RequestError:
                raise HTTPException(status_code=500, detail="Target server is not reachable")

        # Save server details in the database
        return await register_server_details(db, server_name, server_url)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register server: {e}")
    

@app.post("/acknowledge")
async def acknowledge(request: AcknowledgeRequest):
    # Acknowledge the connection setup
    return {
        "message": f"Hi, I acknowledge your request.",
    }


@app.post("/sync")
async def sync_metadata(request: ServerRegistrationRequest, db: AsyncSession = Depends(get_db), skip_logging: bool = False):
    """
    Synchronize metadata for a registered server.

    Args:
        request (ServerRegistrationRequest): The request containing server details.
        skip_logging (bool): If True, prevents duplicate log entries in the database.
            When the background scheduler calls this function, it creates its own 
            schedule and log entries, so we skip the immediate sync logging to avoid 
            duplicate records. Set to False for manual/API-triggered syncs.

    Returns:
        dict: A response containing the sync status and last sync time.

    Raises:
        HTTPException: If the server is not found or an error occurs during synchronization.
    """
    server_name = request.server_name
    server_url = request.server_url
    current_utc_epoch_time = int(time.time() * 1000)
    
    try:
        # Verify the server exists in the registered servers list and get last sync time
        row = await get_sync_status(db, server_name, server_url)

        if not row:
            # Log the failed sync attempt before raising the exception
            await log_sync_attempt("failed", "Server not found in the registered servers list", db, server_name, server_url, current_utc_epoch_time, skip_logging)
            raise HTTPException(status_code=404, detail="Server not found in the registered servers list")

        last_sync_time = row[0]['last_sync_time']

        # Pull MLMD data from the target server using the /mlmd_pull endpoint
        json_payload = await server_mlmd_pull(server_url, last_sync_time)

        json_data = {
            "exec_uuid": None,
            "json_payload": json.dumps(json_payload),
            "pipeline_name": None
        }

        # Ensure the pipeline name in req_info matches the one in the JSON payload
        # to maintain data integrity
        pipelines = json_payload.get("Pipeline", [])
        len_pipelines = len(pipelines)
        pipeline_names = []

        if not pipelines:
            await log_sync_attempt("success", "Nothing to sync", db, server_name, server_url, current_utc_epoch_time, skip_logging)
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
            await log_sync_attempt("failed", "Invalid JSON payload. The pipeline name is missing.", db, server_name, server_url, current_utc_epoch_time, skip_logging)
            raise HTTPException(status_code=400, detail="Invalid JSON payload. The pipeline name is missing.")           
        if status == "version_update":
            # Raise an HTTPException with status code 422
            await log_sync_attempt("failed", "Version update required", db, server_name, server_url, current_utc_epoch_time, skip_logging)
            raise HTTPException(status_code=422, detail="version_update")
        message = "Nothing to sync."
        if status != "exists":
            if not last_sync_time:
                message = f"Host server is syncing with the selected server '{server_name}' at address '{server_url}' for the first time."
            else:
                message = f"Host server is being synced with the selected server '{server_name}' at address '{server_url}'."
            for pipeline_name in pipeline_names:
                await update_global_exe_dict(pipeline_name)
                await update_global_art_dict(pipeline_name)

        # Update the last_sync_time in the database only if sync status is successful
        if status == "success":
            await update_sync_status(db, current_utc_epoch_time, server_name, server_url)

        # Log this immediate sync
        await log_sync_attempt(status, message, db, server_name, server_url, current_utc_epoch_time, skip_logging)

        return {
            "message": message,
            "status": status,
            "last_sync_time": current_utc_epoch_time
        }

    except HTTPException:
        # Re-raise HTTPExceptions (already logged above)
        raise
    except Exception as e:
        print(e)
        # Log unexpected errors
        await log_sync_attempt("failed", f"Failed to sync metadata: {str(e)}", db, server_name, server_url, current_utc_epoch_time, skip_logging)
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


# ---- Scheduling APIs ----
@app.post("/schedule-sync")
async def schedule_sync(request: ScheduleCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a one-time or periodic sync schedule for a registered server.

    Args:
        request (ScheduleCreateRequest): Schedule configuration payload.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Created schedule id and computed next run time.
    """
    try:
        # Validate that target server exists before creating a schedule.
        server = await get_registered_server_by_id(db, request.server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Registered server not found")

        # Parse local ISO datetime and convert to UTC epoch ms
        try:
            tz = ZoneInfo(request.timezone)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid timezone")

        try:
            # Accepts e.g. 2026-01-04T15:00
            local_dt = datetime.strptime(request.start_time_local_iso, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use YYYY-MM-DDTHH:MM")

        # Convert local datetime with timezone info to UTC epoch milliseconds
        local_dt = local_dt.replace(tzinfo=tz)
        start_utc_ms = int(local_dt.astimezone(ZoneInfo("UTC")).timestamp() * 1000)

        # Derive recurrence fields from the selected start datetime.
        derived_time = local_dt.strftime("%H:%M")
        recurrence_mode = None if request.one_time else request.recurrence_mode
        daily_time = derived_time if recurrence_mode == "daily" else None
        weekly_day = request.weekly_day if recurrence_mode == "weekly" else None
        weekly_time = derived_time if recurrence_mode == "weekly" else None

        now_ms = int(time.time() * 1000)
        if request.one_time:
            # One-time schedules must be strictly in the future.
            if start_utc_ms <= now_ms:
                raise HTTPException(status_code=400, detail="Start time must be in the future for one-time schedules")
            next_ms = start_utc_ms
        else:
            # Compute first due run for periodic schedules based on recurrence settings.
            next_ms = await compute_initial_next_run_utc(
                start_utc_ms,
                now_ms,
                request.timezone,
                recurrence_mode,
                interval_unit=request.interval_unit,
                interval_value=request.interval_value,
                daily_time=daily_time,
                weekly_day=weekly_day,
                weekly_time=weekly_time,
            )

        # Persist schedule details and return created id plus first next-run timestamp.
        created = await create_schedule(
            db,
            server_id=request.server_id,
            timezone=request.timezone,
            start_time_utc=start_utc_ms,
            next_run_time_utc=next_ms,
            created_at=now_ms,
            one_time=request.one_time,
            recurrence_mode=recurrence_mode,
            interval_unit=request.interval_unit,
            interval_value=request.interval_value,
            daily_time=daily_time,
            weekly_day=weekly_day,
            weekly_time=weekly_time,
        )
        return {"message": "Schedule created", "schedule_id": created["id"], "next_run_time_utc": next_ms}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {e}")


@app.get("/schedules")
async def get_schedules(server_id: Optional[int] = Query(None), db: AsyncSession = Depends(get_db)):
    """
    Retrieve active schedules, optionally filtered by server id.

    Args:
        server_id (Optional[int]): Optional server id filter.
        db (AsyncSession): Database session dependency.

    Returns:
        list: Active schedule rows.
    """
    rows = await list_schedules(db, server_id)
    return rows


@app.get("/schedule-sync/logs/{schedule_id}")
async def get_schedule_logs(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve run history logs for a schedule id.

    Args:
        schedule_id (int): Schedule id.
        db (AsyncSession): Database session dependency.

    Returns:
        list: Sync log rows ordered by latest first.
    """
    rows = await list_sync_logs(db, schedule_id)
    return rows


@app.get("/server/{server_id}/completed-logs")
async def get_server_completed_logs(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all completed sync logs for a specific server.
    
    Args:
        server_id (int): The ID of the server to get logs for.
    
    Returns:
        list: A list of completed sync logs with sync_type, status, message, and timestamp.
    """
    try:
        logs = await get_completed_logs_by_server(db, server_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch completed logs: {e}")


@app.delete("/schedule-sync/{schedule_id}")
async def delete_schedule_route(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deactivate a schedule so future runs stop.

    Args:
        schedule_id (int): Schedule id to deactivate.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Deactivation status message.
    """
    return await delete_schedule(db, schedule_id)


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
    if not query:
        print(f"DB doesn't exist.")
        raise HTTPException(status_code=404, detail="Database doesn't exist.")


# Function to check if the pipeline exists
async def check_pipeline_exists(pipeline_name):
    if pipeline_name not in query.get_pipeline_names():
        print(f"Pipeline {pipeline_name} not found.")
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_name} not found.")


"""
following APIs are no longer in use within the project but is retained for reference or potential future use.

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
