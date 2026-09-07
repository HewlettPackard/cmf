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
Schedule API endpoints and business logic.

This module contains all schedule-related API endpoints and their business logic,
including creation, listing, and deletion of sync schedules.
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import time
from server.app.db.dbqueries import (
    create_schedule,
    list_schedules,
    get_registered_server_by_id,
    list_sync_logs,
    delete_schedule
)
from server.app.schemas.responses import success_response
from server.app.get_data import (compute_initial_next_run_utc)
from server.app.schemas.requests import ScheduleCreateRequest
from server.app.db.dbconfig import get_db

router = APIRouter(prefix="/v1", tags=["schedules"])


# ==================== API Endpoints ====================

@router.post("/schedules")
async def create_schedule(schedule_info: ScheduleCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a one-time or recurring metadata synchronization schedule.

    Method: POST
    Path: /v1/schedules

    Args:
        schedule_info (ScheduleCreateRequest): Server id, timezone, start time, and recurrence options.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the created schedule id and next run time.
    """
    result = await schedule_sync(
        server_id=schedule_info.server_id,
        timezone=schedule_info.timezone,
        start_time_local_iso=schedule_info.start_time_local_iso,
        one_time=schedule_info.one_time,
        recurrence_mode=schedule_info.recurrence_mode,
        interval_unit=schedule_info.interval_unit,
        interval_value=schedule_info.interval_value,
        weekly_day=schedule_info.weekly_day,
        db=db,
    )
    return success_response(
        data=result,
        message="Schedule created successfully",
        code=201,
    )


@router.get("/schedules")
async def get_schedules_route(server_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """
    Retrieve active schedules, optionally filtered by server id.

    Method: GET
    Path: /v1/schedules

    Args:
        server_id (Optional[int]): Optional server id filter.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the list of active schedule rows.
    """
    result = await get_schedules(server_id, db)
    return success_response(
        data=result,
        message="Schedules retrieved successfully",
        code=200,
    )


@router.get("/schedules/{schedule_id}/logs")
async def get_schedule_logs_route(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve run history logs for a schedule id.

    Method: GET
    Path: /v1/schedules/{schedule_id}/logs

    Args:
        schedule_id (int): Schedule id.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the sync log rows, latest first.
    """
    result = await get_schedule_logs(schedule_id, db)
    return success_response(
        data=result,
        message="Schedule logs retrieved successfully",
        code=200,
    )


@router.delete("/schedules/{schedule_id}")
async def delete_sync_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deactivate a schedule so future runs stop.

    Method: DELETE
    Path: /v1/schedules/{schedule_id}

    Args:
        schedule_id (int): Schedule id to deactivate.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the deactivation status message.
    """
    result = await delete_schedule_route(schedule_id, db)
    return success_response(
        data=result,
        message="Schedule deleted successfully",
        code=200,
    )


# ==================== Business Logic Functions ====================

async def schedule_sync(
    server_id: int,
    timezone: str,
    start_time_local_iso: str,
    one_time: bool,
    recurrence_mode: str | None,
    interval_unit: str | None,
    interval_value: int | None,
    weekly_day: str | None,
    db: AsyncSession
):
    """
    Create a one-time or periodic sync schedule for a registered server.

    NOTE: the route handler below is also named `create_schedule`, which shadows
    the `create_schedule` persistence function imported from db.dbqueries at module
    scope. The call further down therefore resolves to whichever definition is last
    bound to that name at import time - rename one of the two to avoid ambiguity.

    Args:
        server_id (int): Id of the registered server to sync with.
        timezone (str): IANA timezone name for start_time_local_iso.
        start_time_local_iso (str): Local start datetime, e.g. "2026-01-04T15:00".
        one_time (bool): True for a single run, False for a recurring schedule.
        recurrence_mode (str | None): "daily" or "weekly" when not one_time.
        interval_unit (str | None): Interval unit for periodic recurrence.
        interval_value (int | None): Interval value for periodic recurrence.
        weekly_day (str | None): Day of week when recurrence_mode is "weekly".
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Created schedule id and computed next run time.

    Raises:
        HTTPException: 404 if the server is not registered, 400 for invalid
            timezone/datetime or a past one-time start time.
    """
    try:
        # Validate that target server exists before creating a schedule.
        server = await get_registered_server_by_id(db, server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Registered server not found")

        # Parse local ISO datetime and convert to UTC epoch ms
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid timezone")

        try:
            # Accepts e.g. 2026-01-04T15:00
            local_dt = datetime.strptime(start_time_local_iso, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use YYYY-MM-DDTHH:MM")

        # Convert local datetime with timezone info to UTC epoch milliseconds
        local_dt = local_dt.replace(tzinfo=tz)
        start_utc_ms = int(local_dt.astimezone(ZoneInfo("UTC")).timestamp() * 1000)

        # Derive recurrence fields from the selected start datetime.
        derived_time = local_dt.strftime("%H:%M")
        recurrence_mode = None if one_time else recurrence_mode
        daily_time = derived_time if recurrence_mode == "daily" else None
        weekly_day = weekly_day if recurrence_mode == "weekly" else None
        weekly_time = derived_time if recurrence_mode == "weekly" else None

        now_ms = int(time.time() * 1000)
        if one_time:
            # One-time schedules must be strictly in the future.
            if start_utc_ms <= now_ms:
                raise HTTPException(status_code=400, detail="Start time must be in the future for one-time schedules")
            next_ms = start_utc_ms
        else:
            # Compute first due run for periodic schedules based on recurrence settings.
            next_ms = await compute_initial_next_run_utc(
                start_utc_ms,
                now_ms,
                timezone,
                recurrence_mode,
                interval_unit=interval_unit,
                interval_value=interval_value,
                daily_time=daily_time,
                weekly_day=weekly_day,
                weekly_time=weekly_time
            )

        # Persist schedule details and return created id plus first next-run timestamp.
        created = await create_schedule(
            db,
            server_id=server_id,
            timezone=timezone,
            start_time_utc=start_utc_ms,
            next_run_time_utc=next_ms,
            created_at=now_ms,
            one_time=one_time,
            recurrence_mode=recurrence_mode,
            interval_unit=interval_unit,
            interval_value=interval_value,
            daily_time=daily_time,
            weekly_day=weekly_day,
            weekly_time=weekly_time
        )
        return {"message": "Schedule created", "schedule_id": created["id"], "next_run_time_utc": next_ms}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {e}")



async def get_schedules(server_id: Optional[int], db: AsyncSession):
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


async def get_schedule_logs(schedule_id: int, db: AsyncSession):
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



async def delete_schedule_route(schedule_id: int, db: AsyncSession):
    """
    Deactivate a schedule so future runs stop.

    Args:
        schedule_id (int): Schedule id to deactivate.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Deactivation status message.
    """
    return await delete_schedule(db, schedule_id)
