"""CMFQuery pipeline REST API endpoints."""

import json
from typing import Optional

from cmflib.cmfquery import CmfQuery
from fastapi import APIRouter
from server.app.get_data import async_api
from server.app.services.mlmd_state import mlmd_state
from server.app.schemas.responses import (
    ErrorDetail,
    APIResponse,
    error_response,
    success_response,
)

router = APIRouter(prefix="/v1", tags=["pipelines"])
query = mlmd_state.query


# ==================== API Endpoints For CMFQuery ====================

@router.get("/pipelines/{pipeline_name}/stages", response_model=APIResponse)
async def cmfquery_get_pipeline_stages(pipeline_name: str):
    """Retrieve all stage names associated with a pipeline."""
    stages = await async_api(list_pipeline_stages, query, pipeline_name)
    if stages == []:
        return error_response(
            message=f"Stages for '{pipeline_name}' not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="pipeline_name",
                    message=f"Stages for pipeline '{pipeline_name}' not found",
                )
            ],
        )

    return success_response(
        data={
            "pipeline_name": pipeline_name,
            "stages": stages,
            "total_stages": len(stages),
        },
        message="Pipeline stages retrieved successfully",
        code=200,
    )


@router.get("/pipelines/names", response_model=APIResponse)
async def cmfquery_list_pipelines():
    """Retrieve all pipeline names available in the metadata store."""
    pipeline_names = await async_api(list_pipeline_names, query)
    if pipeline_names:
        return success_response(
            data={
                "pipelines": pipeline_names,
                "total_pipelines": len(pipeline_names),
            },
            message="Pipeline names retrieved successfully",
            code=200,
        )
    return error_response(
        message="No pipelines found",
        code=404,
        errors=[
            ErrorDetail(
                field="pipelines",
                message="No pipelines found",
            )
        ],
    )


@router.get("/pipelines/{pipeline_name}/id", response_model=APIResponse)
async def cmfquery_get_pipeline_id(pipeline_name: str):
    """Retrieve the metadata store identifier for a pipeline name."""
    pipeline_id = await async_api(return_pipeline_id, query, pipeline_name)
    if pipeline_id == -1:
        return error_response(
            message="Pipeline not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="pipeline_name",
                    message=f"Pipeline '{pipeline_name}' not found",
                )
            ],
        )

    return success_response(
        data={
            "pipeline_name": pipeline_name,
            "pipeline_id": pipeline_id,
        },
        message="Pipeline ID retrieved successfully",
        code=200,
    )


@router.get("/pipelines/{pipeline_name}/executions", response_model=APIResponse)
async def cmfquery_get_pipeline_executions(pipeline_name: str):
    """Retrieve execution records associated with a pipeline."""
    executions = await async_api(get_pipeline_executions, query, pipeline_name)
    execution_records = [] if executions is None or executions.empty else mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "pipeline_name": pipeline_name,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Pipeline executions retrieved successfully",
        code=200,
    )


@router.get("/pipelines/{pipeline_name}/json", response_model=APIResponse)
async def cmfquery_dump_pipeline_to_json(
    pipeline_name: str,
    exec_uuid: Optional[str] = None,
):
    """Export metadata for a pipeline, optionally scoped to an execution UUID."""
    pipeline_id = await async_api(return_pipeline_id, query, pipeline_name)
    if pipeline_id == -1:
        return error_response(
            message="Pipeline not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="pipeline_name",
                    message=f"Pipeline '{pipeline_name}' not found",
                )
            ],
        )

    pipeline_json = await async_api(get_pipeline_json, query, pipeline_name, exec_uuid)
    return success_response(
        data=json.loads(pipeline_json) if pipeline_json else {"Pipeline": []},
        message="Pipeline JSON retrieved successfully",
        code=200,
    )


@router.get("/pipelines/sync/{last_sync_time}/json", response_model=APIResponse)
async def cmfquery_extract_pipelines_to_json(last_sync_time: int):
    """Export pipeline metadata changed after the given sync timestamp."""
    pipeline_json = await async_api(extract_pipelines_to_json, query, last_sync_time)
    return success_response(
        data=json.loads(pipeline_json),
        message="Pipelines JSON extracted successfully",
        code=200,
    )


# ==================== Business Logic Functions For CMFQuery ====================

def list_pipeline_names(query: CmfQuery):
    """Return all pipeline names from the CMFQuery backend."""
    return query.get_pipeline_names()


def return_pipeline_id(query: CmfQuery, pipeline_name: str):
    """Return the metadata store identifier for the requested pipeline."""
    return query.get_pipeline_id(pipeline_name)


def list_pipeline_stages(query: CmfQuery, pipeline_name: str):
    """Return all stages recorded for the requested pipeline."""
    return query.get_pipeline_stages(pipeline_name)


def get_pipeline_executions(query: CmfQuery, pipeline_name: str):
    """Return all execution records recorded for the requested pipeline."""
    return query.get_all_executions_in_pipeline(pipeline_name)


def get_pipeline_json(query: CmfQuery, pipeline_name: str, exec_uuid: Optional[str]):
    """Return serialized pipeline metadata for the requested pipeline."""
    return query.dumptojson(pipeline_name, exec_uuid)


def extract_pipelines_to_json(query: CmfQuery, last_sync_time: int):
    """Return serialized pipeline metadata changed after a sync timestamp."""
    return query.extract_to_json(last_sync_time)
