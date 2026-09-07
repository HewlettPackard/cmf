"""
Copyright (2023) Hewlett Packard Enterprise Development LP

Licensed under the Apache License, Version 2.0 (the "License");
You may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
Metadata API endpoints and business logic.

This module contains all metadata-related API endpoints and their business logic,
including MLMD push/pull, 
"""


import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from server.app.schemas.requests import MLMDPullRequest, MLMDPushRequest
from server.app.schemas.responses import success_response
from server.app.services.mlmd_state import MlmdState
from server.app.get_data import (
    get_mlmd_from_server,
    async_api, 
)
from cmflib.cmf_federation import update_mlmd

router = APIRouter(prefix="/v1", tags=["metadata"])

# ==================== API Endpoints ====================

@router.post("/mlmd/push")
async def metadata_push(request: Request, info: MLMDPushRequest):
    """
    Push MLMD metadata into the server's current metadata store.

    Method: POST
    Path: /v1/mlmd/push

    Args:
        info (MLMDPushRequest): Pipeline name, MLMD JSON payload, and optional execution uuid.

    Returns:
        JSONResponse: success_response wrapping the push status.
    """
    state = request.app.state.mlmd
    result = await mlmd_push(
        state=state,
        pipeline_name=info.pipeline_name,
        json_payload=info.json_payload,
        exec_uuid=info.exec_uuid,
    )
    return success_response(
        data=result,
        message="MLMD pushed successfully",
        code=200,
    )


@router.post("/mlmd/pull", response_class=HTMLResponse)
async def metadata_pull(request: Request, info: MLMDPullRequest):
    """
    Pull MLMD metadata for a pipeline, execution, or synchronization point.

    Method: POST
    Path: /v1/mlmd/pull

    Args:
        info (MLMDPullRequest): Optional pipeline name, execution uuid, and last sync time.

    Returns:
        HTMLResponse: Raw MLMD JSON payload for the requested scope.
    """
    state = request.app.state.mlmd
    return await mlmd_pull(
        state=state,
        pipeline_name=info.pipeline_name,
        exec_uuid=info.exec_uuid,
        last_sync_time=info.last_sync_time,
    )



# ==================== Business Logic Functions ====================

async def mlmd_push(
    state: MlmdState,
    pipeline_name: str,
    json_payload: str,
    exec_uuid: str | None,
):
    """
    Merge an incoming MLMD JSON payload into the server's metadata store, guarded by a per-pipeline lock.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline the payload belongs to.
        json_payload (str): MLMD data serialized as a JSON string.
        exec_uuid (str | None): Execution uuid to scope the push, if provided.

    Returns:
        dict: {"status": str} - one of the update_mlmd status codes (e.g. "success", "exists").

    Raises:
        HTTPException: 400 for an invalid JSON payload, 422 if a version update is required.
    """
    print("mlmd push started")
    print("......................")
    status = "unknown_error"
    if pipeline_name not in state.pipeline_locks: # create lock object for pipeline if it doesn't exists in lock
        state.pipeline_locks[pipeline_name] = asyncio.Lock()
    pipeline_lock = state.pipeline_locks[pipeline_name]
    state.lock_counts[pipeline_name] += 1  # increment lock count by 1 if pipeline going to enter inside lock section
    async with pipeline_lock:
        try:
            status = await async_api(
                update_mlmd,
                state.query,
                json_payload,
                pipeline_name,
                "push",
                exec_uuid,
            )
            # Invalid JSON payload, return 400 Bad Request
            if status == "invalid_json_payload":
                raise HTTPException(status_code=400, detail="Invalid JSON payload. The pipeline name is missing.")
            if status == "version_update":
                # Raise an HTTPException with status code 422
                raise HTTPException(status_code=422, detail="version_update")
            if status != "exists":
                 # async function
                await state.update_global_exe_dict(pipeline_name)
                await state.update_global_art_dict(pipeline_name)
        finally:
            state.lock_counts[pipeline_name] -= 1 # Decrement the reference count after lock released
            if state.lock_counts[pipeline_name] == 0:  #if lock_counts of pipeline is zero means lock is release from it
                del state.pipeline_locks[pipeline_name] # Remove the lock if it's no longer needed
                del state.lock_counts[pipeline_name]
    return {"status": status}


# API to get MLMD file from cmf-server.
async def mlmd_pull(
    state: MlmdState,
    pipeline_name: str | None,
    exec_uuid: str | None,
    last_sync_time: int | None,
):
    """
    Read MLMD metadata for a pipeline (or all pipelines) since an optional last sync time.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str | None): Pipeline to pull; all pipelines if None.
        exec_uuid (str | None): Execution uuid to scope the pull, if provided.
        last_sync_time (int | None): Only return data changed after this epoch time.

    Returns:
        The MLMD JSON payload for the requested scope.

    Raises:
        HTTPException: 406 if the pipeline does not exist.
    """
    print("mlmd pull started")
    print("......................")
    # checks if mlmd file exists on server
    await state.check_mlmd_file_exists()
    if pipeline_name:
        # checks if pipeline exists
        await state.check_pipeline_exists(pipeline_name)
        #json_payload values can be json data, none or no_exec_id.
        json_payload = await async_api(
            get_mlmd_from_server,
            state.query,
            pipeline_name,
            exec_uuid,
            last_sync_time,
            state.dict_of_exe_ids
        )
    else:
        json_payload = await async_api(get_mlmd_from_server, state.query, None, None, last_sync_time)

    if json_payload is None:
        raise HTTPException(status_code=406, detail=f"Pipeline {pipeline_name} not found.")
    return json_payload
