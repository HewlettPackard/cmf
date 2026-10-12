"""CMFQuery execution REST API endpoints."""

from typing import Optional

from cmflib.cmfquery import CmfQuery
from fastapi import APIRouter
from server.app.get_data import async_api
from server.app.services.mlmd_state import mlmd_state
from server.app.schemas.requests import (
    ExecutionIdsRequest,
    ExecutionIdsWithPipelineRequest,
)
from server.app.schemas.responses import (
    ErrorDetail,
    APIResponse,
    error_response,
    success_response,
)

router = APIRouter(prefix="/v1", tags=["executions"])
query = mlmd_state.query


# ==================== API Endpoints For CMFQuery ====================

@router.get("/executions/stages/name/{stage_name:path}/list", response_model=APIResponse)
async def cmfquery_list_executions_in_pipelines_stages(stage_name: str):
    """Retrieve execution objects associated with a pipeline stage name."""
    executions = await async_api(list_executions_in_pipelines_stages, query, stage_name)
    if executions == []:
        return error_response(
            message="Executions associated with stage not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="stage_name",
                    message=f"Stage '{stage_name}' not found",
                )
            ],
        )

    return success_response(
        data={
            "stage_name": stage_name,
            "executions": [mlmd_state._execution_to_dict(execution) for execution in executions],
            "total_executions": len(executions),
        },
        message="Executions associated with pipeline stage retrieved successfully",
        code=200,
    )


@router.get("/executions/stages/name/{stage_name:path}", response_model=APIResponse)
async def cmfquery_get_executions_in_pipeline_stages(stage_name: str):
    """Retrieve execution details associated with a pipeline stage name."""
    executions = await async_api(get_executions_in_pipeline_stages, query, stage_name)
    if executions is None or executions.empty:
        return error_response(
            message="Executions associated with stage not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="stage_name",
                    message=f"Stage '{stage_name}' not found",
                )
            ],
        )

    return success_response(
        data={
            "stage_name": stage_name,
            "executions": mlmd_state._dataframe_records(executions),
            "total_executions": len(executions),
        },
        message="Executions associated with pipeline stage retrieved successfully",
        code=200,
    )


@router.post("/executions/batch-get", response_model=APIResponse)
async def cmfquery_get_all_executions_by_ids_list(
    request: ExecutionIdsRequest,
):
    """Retrieve execution records for a batch of execution identifiers."""
    executions = await async_api(get_all_executions_by_ids_list, query, request.exe_ids)
    if executions is None or executions.empty:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="exe_ids",
                    message=f"Executions not found for ids {request.exe_ids}",
                )
            ],
        )

    execution_records = mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "exe_ids": request.exe_ids,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Executions retrieved successfully",
        code=200,
    )


@router.get("/executions/pipeline/{pipeline_name}", response_model=APIResponse)
async def cmfquery_get_all_executions_in_pipeline(pipeline_name: str):
    """Retrieve all execution records associated with a pipeline."""
    executions = await async_api(get_all_executions_in_pipeline, query, pipeline_name)
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


@router.post("/executions/parents/batch-get", response_model=APIResponse)
async def cmfquery_get_one_hop_parent_executions(
    request: ExecutionIdsWithPipelineRequest,
):
    """Retrieve direct parent executions for execution identifiers."""
    executions = await async_api(get_one_hop_parent_executions, query, request.execution_id, request.pipeline_id)
    if not executions:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="execution_id",
                    message=f"Parent executions not found for execution ids {request.execution_id}",
                )
            ],
        )

    execution_records = [
        mlmd_state._execution_to_dict(execution) if hasattr(execution, "id") else execution
        for execution in executions
    ]
    return success_response(
        data={
            "execution_id": request.execution_id,
            "pipeline_id": request.pipeline_id,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="One-hop parent executions retrieved successfully",
        code=200,
    )


@router.get("/executions/id/{execution_id}/parents/ids", response_model=APIResponse)
async def cmfquery_get_one_hop_parent_execution_ids(
    execution_id: int,
    pipeline_id: Optional[int] = None,
):
    """Retrieve direct parent execution IDs for an execution identifier."""
    execution_ids = await async_api(get_one_hop_parent_execution_ids, query, execution_id, pipeline_id)
    if not execution_ids:
        return error_response(
            message="Parent execution ids not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="execution_id",
                    message=f"Parent execution ids not found for execution id {execution_id}",
                )
            ],
        )

    return success_response(
        data={
            "execution_id": execution_id,
            "pipeline_id": pipeline_id,
            "parent_execution_ids": execution_ids,
            "total_parent_execution_ids": len(execution_ids),
        },
        message="One-hop parent execution ids retrieved successfully",
        code=200,
    )


@router.post("/executions/ancestors/batch-get", response_model=APIResponse)
async def cmfquery_get_all_parent_executions_by_id(
    request: ExecutionIdsWithPipelineRequest,
):
    """Retrieve all parent executions and links for execution identifiers."""
    parent_executions = await async_api(get_all_parent_executions_by_id, query, request.execution_id, request.pipeline_id)
    parent_details = parent_executions[0] if parent_executions else []
    parent_links = parent_executions[1] if parent_executions and len(parent_executions) > 1 else []
    if not parent_details and not parent_links:
        return error_response(
            message="Parent executions not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="execution_id",
                    message=f"Parent executions not found for execution ids {request.execution_id}",
                )
            ],
        )

    return success_response(
        data={
            "execution_id": request.execution_id,
            "pipeline_id": request.pipeline_id,
            "parent_executions": parent_details,
            "links": parent_links,
            "total_parent_executions": len(parent_details),
        },
        message="All parent executions retrieved successfully",
        code=200,
    )


@router.post("/executions/batch-summary", response_model=APIResponse)
async def cmfquery_get_executions_with_execution_ids(
    request: ExecutionIdsRequest,
):
    """Retrieve execution summaries for a batch of execution identifiers."""
    executions = await async_api(get_executions_with_execution_ids, query, request.exe_ids)
    if executions is None or executions.empty:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="exe_ids",
                    message=f"Executions not found for ids {request.exe_ids}",
                )
            ],
        )

    execution_records = mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "exe_ids": request.exe_ids,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Execution summary retrieved successfully",
        code=200,
    )


@router.get("/executions/stages/id/{stage_id}", response_model=APIResponse)
async def cmfquery_get_all_executions_by_stage(
    stage_id: int,
    execution_uuid: Optional[str] = None,
):
    """Retrieve executions associated with a stage ID and optional UUID."""
    executions = await async_api(get_all_executions_by_stage, query, stage_id, execution_uuid)
    if not executions:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="stage_id",
                    message=f"Executions not found for stage id {stage_id}",
                )
            ],
        )

    execution_records = [
        mlmd_state._execution_to_dict(execution) if hasattr(execution, "id") else execution
        for execution in executions
    ]
    return success_response(
        data={
            "stage_id": stage_id,
            "execution_uuid": execution_uuid,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Executions for stage retrieved successfully",
        code=200,
    )


@router.get("/executions/id/{execution_id}/artifacts", response_model=APIResponse)
async def cmfquery_get_all_artifacts_for_execution(execution_id: int):
    """Retrieve artifacts associated with one execution identifier."""
    artifacts = await async_api(get_all_artifacts_for_execution, query, execution_id)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="execution_id", message=f"Artifacts not found for execution id {execution_id}")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "execution_id": execution_id,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifacts for execution retrieved successfully",
        code=200,
    )


@router.post("/executions/artifacts/batch-get", response_model=APIResponse)
async def cmfquery_get_all_artifacts_for_executions(
    request: ExecutionIdsRequest,
):
    """Retrieve artifacts associated with a batch of execution identifiers."""
    artifacts = await async_api(get_all_artifacts_for_executions, query, request.exe_ids)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="exe_ids",
                    message=f"Artifacts not found for execution ids {request.exe_ids}",
                )
            ],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "exe_ids": request.exe_ids,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifacts for executions retrieved successfully",
        code=200,
    )

# ==================== Business Logic Functions For CMFQuery ====================

def list_executions_in_pipelines_stages(query: CmfQuery, stage_name: str):
    """Return execution objects recorded for the requested stage name."""
    return query.get_all_exe_in_stage(stage_name)


def get_executions_in_pipeline_stages(query: CmfQuery, stage_name: str):
    """Return execution details recorded for the requested stage name."""
    return query.get_all_executions_in_stage(stage_name)


def get_all_executions_by_ids_list(query: CmfQuery, exe_ids: list[int]):
    """Return execution records matching the requested execution IDs."""
    return query.get_all_executions_by_ids_list(exe_ids)


def get_all_executions_in_pipeline(query: CmfQuery, pipeline_name: str):
    """Return execution records associated with the requested pipeline."""
    return query.get_all_executions_in_pipeline(pipeline_name)


def get_one_hop_parent_executions(query: CmfQuery, execution_id: list[int], pipeline_id: Optional[int]):
    """Return direct parent executions for the requested execution IDs."""
    return query.get_one_hop_parent_executions(execution_id, pipeline_id)


def get_one_hop_parent_execution_ids(query: CmfQuery, execution_id: int, pipeline_id: Optional[int]):
    """Return direct parent execution IDs for the requested execution ID."""
    return query.get_one_hop_parent_execution_ids(execution_id, pipeline_id)


def get_all_parent_executions_by_id(query: CmfQuery, execution_id: list[int], pipeline_id: Optional[int]):
    """Return all parent execution details and links for execution IDs."""
    return query.get_all_parent_executions_by_id(execution_id, pipeline_id)


def get_executions_with_execution_ids(query: CmfQuery, exe_ids: list[int]):
    """Return execution summaries matching the requested execution IDs."""
    return query.get_executions_with_execution_ids(exe_ids)


def get_all_executions_by_stage(query: CmfQuery, stage_id: int, execution_uuid: Optional[str]):
    """Return executions for the requested stage ID and optional UUID."""
    return query.get_all_executions_by_stage(stage_id, execution_uuid)


def get_all_artifacts_for_execution(query: CmfQuery, execution_id: int):
    """Return artifacts associated with the requested execution ID."""
    return query.get_all_artifacts_for_execution(execution_id)


def get_all_artifacts_for_executions(query: CmfQuery, execution_ids: list[int]):
    """Return artifacts associated with the requested execution IDs."""
    return query.get_all_artifacts_for_executions(execution_ids)
