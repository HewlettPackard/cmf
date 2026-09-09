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
Server API endpoints and business logic.

This module contains all server-related API endpoints and their business logic,
including server registration, sync, scheduling, and logging.
"""
import json
import time
import httpx
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.app.db.dbconfig import get_db
from server.app.db.dbqueries import (
    register_server_details,
    get_sync_status,
    get_registered_server_details,
    update_sync_status,
    get_completed_logs_by_server,
)
from server.app.schemas.requests import ServerRegistrationRequest, AcknowledgeRequest
from server.app.schemas.responses import success_response
from server.app.services.mlmd_state import MlmdState
from server.app.utils import extract_hostname
from server.app.get_data import (
    server_mlmd_pull,
    log_sync_attempt,
    async_api
)
from cmflib.cmf_federation import update_mlmd

router = APIRouter(prefix="/v1", tags=["servers"])

# ==================== API Endpoints ====================
@router.post("/acknowledge")
async def acknowledge_server(info: AcknowledgeRequest):
    """
    Compatibility endpoint used by peer servers during registration and liveness checks.

    Method: POST
    Path: /v1/acknowledge

    Args:
        info (AcknowledgeRequest): Calling server's name and url.

    Returns:
        JSONResponse: success_response confirming acknowledgement.
    """
    return success_response(
        data={
            "server_name": info.server_name,
            "server_url": info.server_url,
            "status": "ok"
        },
        message="Server acknowledged successfully",
        code=200
    )


@router.post("/servers/register")
async def register_server_route(request: Request, info: ServerRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a reachable peer server for metadata synchronization.

    Method: POST
    Path: /v1/servers/register

    Args:
        info (ServerRegistrationRequest): Peer server name and url.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the stored server record.
    """
    state = request.app.state.mlmd
    result = await register_server(
        state=state,
        server_name=info.server_name,
        server_url=info.server_url,
        db=db
    )
    return success_response(
        data=result,
        message="Server registered successfully",
        code=201
    )


@router.post("/servers/sync")
async def sync_server(request: Request, info: ServerRegistrationRequest, db: AsyncSession = Depends(get_db), skip_logging: bool = False):
    """
    Synchronize metadata from a registered peer server.

    Method: POST
    Path: /v1/servers/sync

    Args:
        info (ServerRegistrationRequest): Peer server name and url to sync with.
        db (AsyncSession): Database session dependency.
        skip_logging (bool): Skip writing an immediate sync log entry (used by the scheduler).

    Returns:
        JSONResponse: success_response wrapping the sync status and last sync time.
    """
    state = request.app.state.mlmd
    result = await sync_metadata(
        state=state,
        server_name=info.server_name,
        server_url=info.server_url,
        db=db,
        skip_logging=skip_logging
    )
    return success_response(
        data=result,
        message="Server synced successfully",
        code=200
    )


@router.get("/servers")
async def list_servers(db: AsyncSession = Depends(get_db)):
    """
    Get all servers registered for metadata synchronization.

    Method: GET
    Path: /v1/servers

    Args:
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the list of registered servers.
    """
    result = await server_list(db)
    return success_response(
        data=result,
        message="Servers retrieved successfully",
        code=200,
    )


@router.get("/servers/{server_id}/completed-logs")
async def server_completed_logs(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all completed sync logs for a specific server.

    Method: GET
    Path: /v1/servers/{server_id}/completed-logs

    Args:
        server_id (int): The ID of the server to get logs for.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping a list of completed sync logs
            with sync_type, status, message, and timestamp.
    """
    result = await get_server_completed_logs(server_id, db)
    return success_response(
        data=result,
        message="Server completed logs retrieved successfully",
        code=200,
    )


# ==================== Business Logic Functions ====================

# Server registration API.
async def register_server(
    state: MlmdState,
    server_name: str,
    server_url: str,
    db: AsyncSession,
):
    """
    Register a new peer server after confirming it is reachable and acknowledges the request.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        server_name (str): Name of the server to register.
        server_url (str): Base URL of the server to register.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: The stored server record.

    Raises:
        HTTPException: 400 if registering the server's own details, 500 if the
            target server does not acknowledge or is unreachable.
    """
    try:
        server = extract_hostname(server_url)

        # Check that the user isn't registering the server with its own details.
        if server in state.LOCAL_ADDRESSES:
            raise HTTPException(status_code=400,detail="Cannot register the server with its own details.")

        # Step 1: Send a request to the target server for acknowledgement
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{server_url}/api/v1/acknowledge",
                    json={
                        "server_name": server_name,
                        "server_url": server_url
                    }
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=500,detail="Target server did not respond successfully")
                target_server_data = response.json()
            except httpx.RequestError :
                raise HTTPException(status_code=500,detail="Target server is not reachable")
        # Save server details in the database
        return await register_server_details(db,server_name,server_url)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to register server: {e}") 


# Metadata synchronization API.
async def sync_metadata(
    state: MlmdState,
    server_name: str,
    server_url: str,
    db: AsyncSession,
    skip_logging: bool = False
):
    """
    Synchronize metadata for a registered server.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        server_name (str): Name of the registered server to sync with.
        server_url (str): Base URL of the registered server.
        db (AsyncSession): Database session dependency.
        skip_logging (bool): If True, prevents duplicate log entries in the database.
            When the background scheduler calls this function, it creates its own 
            schedule and log entries, so we skip the immediate sync logging to avoid 
            duplicate records. Set to False for manual/API-triggered syncs.

    Returns:
        dict: A response containing the sync status and last sync time.

    Raises:
        HTTPException: If the server is not found or an error occurs during synchronization.
    """
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
        status = await async_api(update_mlmd, state.query,  json_data["json_payload"], None, "push", None)
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
                await state.update_global_exe_dict(pipeline_name)
                await state.update_global_art_dict(pipeline_name)

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


async def server_list(db: AsyncSession):
    """
    Get the list of all registered servers.

    Args:
        db (AsyncSession): Database session dependency.

    Returns:
        list: Registered server records.
    """
    rows = await get_registered_server_details(db)
    return rows


async def get_server_completed_logs(server_id: int, db: AsyncSession):
    """
    Get all completed sync logs for a specific server.

    Args:
        server_id (int): The ID of the server to get logs for.
        db (AsyncSession): Database session dependency.

    Returns:
        list: A list of completed sync logs with sync_type, status, message, and timestamp.

    Raises:
        HTTPException: 500 if the logs cannot be fetched.
    """
    try:
        logs = await get_completed_logs_by_server(db, server_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch completed logs: {e}")
