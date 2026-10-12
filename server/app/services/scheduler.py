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

This Module contains scheduler logic for executing due schedules in the background. It performs server registration and liveness checks before executing scheduled syncs, and handles logging and rescheduling based on the outcome of each sync attempt.
"""

import asyncio
import time
from fastapi import HTTPException
from server.app.api.v1.servers import sync_metadata
from server.app.get_data import compute_next_run_from_recurrence
from server.app.schemas.requests import ServerRegistrationRequest
from server.app.services.mlmd_state import mlmd_state
import httpx
from server.app.db.dbconfig import async_session
from server.app.db.dbqueries import (
    due_schedules,
    update_next_run,
    log_sync_run,
    get_registered_server_by_id,
    update_schedule_fields,
)

async def schedule_runner():
    """
    Background loop that polls and executes due sync schedules every 30 seconds.

    For each due schedule, runs a 3-stage check before syncing:
      1. Registration check - if the server record no longer exists, deactivate
         the schedule (permanent config issue, not a transient outage).
      2. Liveness check - ping the server; if unreachable, deactivate one-time
         schedules (missed their window) or reschedule periodic ones for retry.
      3. Sync - if registered and alive, perform the sync, log the result, and
         either deactivate (one-time) or advance to the next run time (periodic).

    Returns:
        None. Runs indefinitely until the process is stopped.
    """
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
                                f"{server['host_info']}/api/v1/acknowledge",
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
                        result = await sync_metadata(
                            state=mlmd_state,
                            server_name=req.server_name,
                            server_url=req.server_url,
                            db=db,
                            skip_logging=True,
                        )
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