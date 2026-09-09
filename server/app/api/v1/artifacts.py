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

Artifact API endpoints and business logic.
"""

import json
from typing import Optional

from cmflib.cmfquery import CmfQuery
from fastapi import APIRouter, HTTPException, Request
from server.app.get_data import async_api, get_artifact_types, get_model_data
from server.app.schemas.requests import ArtifactIdsRequest
from server.app.schemas.responses import APIResponse, ErrorDetail, error_response, success_response
from server.app.services.mlmd_state import MlmdState, mlmd_state

router = APIRouter(prefix="/v1", tags=["artifacts"])
query = mlmd_state.query


# ==================== REST API Endpoints For UI ====================

# GET /artifacts/types - used only by the MCP server.
@router.get("/artifacts/types")
async def get_artifacts_by_types(
    request: Request,
):
    """
    Get the list of artifact types present in the current MLMD store.

    Method: GET
    Path: /v1/artifacts/types

    Returns:
        JSONResponse: success_response wrapping the list of artifact type names.
    """
    state = request.app.state.mlmd
    result = await get_artifacts_types(state)

    return success_response(
        data=result,
        message="Artifact types retrieved successfully",
        code=200
    )


@router.get("/artifacts/models/{model_id}/card")
async def get_model_artifact_card(request: Request, model_id: int):
    """
    Get model card data for a model artifact.

    Method: GET
    Path: /v1/artifacts/models/{model_id}/card

    Args:
        model_id (int): Id of the Model artifact.

    Returns:
        JSONResponse: success_response wrapping model, execution, and artifact data.
    """
    state = request.app.state.mlmd
    result = await get_model_card_by_artifact_id(state, model_id)
    return success_response(
        data=result,
        message="Model card retrieved successfully",
        code=200
    )

# ==================== REST API Endpoints For CMFQuery ====================

@router.get("/artifacts", response_model=APIResponse)
async def cmfquery_get_all_artifacts():
    """Retrieve all artifact names available in the metadata store."""
    artifact_names = await async_api(get_all_artifacts, query)
    if artifact_names == []:
        return error_response(
            message="No artifacts found",
            code=404,
            errors=[ErrorDetail(field="artifacts", message="No artifacts found in the system")],
        )

    return success_response(
        data={"artifacts": artifact_names, "total_artifacts": len(artifact_names)},
        message="Artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/{pipeline_name}", response_model=APIResponse)
async def cmfquery_get_all_artifacts_by_context(pipeline_name: str):
    """Retrieve artifacts associated with a pipeline context."""
    artifacts = await async_api(get_all_artifacts_by_context, query, pipeline_name)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts associated with pipeline not found",
            code=404,
            errors=[
                ErrorDetail(
                    field="pipeline_name",
                    message=f"Pipeline '{pipeline_name}' not found or has no artifacts",
                )
            ],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "pipeline_name": pipeline_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifacts associated with pipeline retrieved successfully",
        code=200,
    )


@router.post("/artifacts/batch-get", response_model=APIResponse)
async def cmfquery_get_all_artifacts_by_ids_list(
    request: ArtifactIdsRequest,
):
    """Retrieve artifact records for a batch of artifact identifiers."""
    artifacts = await async_api(get_all_artifacts_by_ids_list, query, request.artifact_ids)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_ids", message=f"Artifacts not found for ids {request.artifact_ids}")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_ids": request.artifact_ids,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/dataframe", response_model=APIResponse)
async def cmfquery_get_artifact_df(artifact_name: str):
    """Retrieve dataframe-formatted metadata for an artifact name."""
    artifact = await async_api(get_artifact_df, query, artifact_name)
    if artifact is None or artifact.empty:
        return error_response(
            message="Artifact not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Artifact '{artifact_name}' not found")],
        )

    artifact_records = mlmd_state._dataframe_records(artifact)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifact dataframe retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/children", response_model=APIResponse)
async def cmfquery_get_one_hop_child_artifacts(
    artifact_name: str,
    pipeline_id: Optional[int] = None,
):
    """Retrieve direct child artifacts for an artifact name."""
    artifacts = await async_api(get_one_hop_child_artifacts, query, artifact_name, pipeline_id)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Child artifacts not found for artifact '{artifact_name}'")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "pipeline_id": pipeline_id,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="One-hop child artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/descendants", response_model=APIResponse)
async def cmfquery_get_all_child_artifacts(artifact_name: str):
    """Retrieve all downstream child artifacts for an artifact name."""
    artifacts = await async_api(get_all_child_artifacts, query, artifact_name)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Child artifacts not found for artifact '{artifact_name}'")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="All child artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/parents", response_model=APIResponse)
async def cmfquery_get_one_hop_parent_artifacts(artifact_name: str):
    """Retrieve direct parent artifacts for an artifact name."""
    artifacts = await async_api(get_one_hop_parent_artifacts, query, artifact_name)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Parent artifacts not found for artifact '{artifact_name}'")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="One-hop parent artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/id/{artifact_id}/parents", response_model=APIResponse)
async def cmfquery_get_one_hop_parent_artifacts_with_id(artifact_id: int):
    """Retrieve direct parent artifacts for an artifact identifier."""
    artifacts = await async_api(get_one_hop_parent_artifacts_with_id, query, artifact_id)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_id", message=f"Parent artifacts not found for artifact id {artifact_id}")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_id": artifact_id,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="One-hop parent artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/ancestors", response_model=APIResponse)
async def cmfquery_get_all_parent_artifacts(artifact_name: str):
    """Retrieve all upstream parent artifacts for an artifact name."""
    artifacts = await async_api(get_all_parent_artifacts, query, artifact_name)
    if artifacts is None or artifacts.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Parent artifacts not found for artifact '{artifact_name}'")],
        )

    artifact_records = mlmd_state._dataframe_records(artifacts)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="All parent artifacts retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/executions", response_model=APIResponse)
async def cmfquery_get_all_executions_for_artifact(artifact_name: str):
    """Retrieve executions associated with an artifact name."""
    executions = await async_api(get_all_executions_for_artifact, query, artifact_name)
    if executions is None or executions.empty:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Executions not found for artifact '{artifact_name}'")],
        )

    execution_records = mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Executions for artifact retrieved successfully",
        code=200,
    )


@router.get("/artifacts/id/{artifact_id}/executions", response_model=APIResponse)
async def cmfquery_get_all_executions_for_artifact_id(artifact_id: int):
    """Retrieve executions associated with an artifact identifier."""
    executions = await async_api(get_all_executions_for_artifact_id, query, artifact_id)
    if executions is None or executions.empty:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[ErrorDetail(field="artifact_id", message=f"Executions not found for artifact id {artifact_id}")],
        )

    execution_records = mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "artifact_id": artifact_id,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="Executions for artifact retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/parent-executions", response_model=APIResponse)
async def cmfquery_get_all_parent_executions(artifact_name: str):
    """Retrieve parent executions associated with an artifact name."""
    executions = await async_api(get_all_parent_executions, query, artifact_name)
    if executions is None or executions.empty:
        return error_response(
            message="Executions not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Parent executions not found for artifact '{artifact_name}'")],
        )

    execution_records = mlmd_state._dataframe_records(executions)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "executions": execution_records,
            "total_executions": len(execution_records),
        },
        message="All parent executions retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}/producer-execution", response_model=APIResponse)
async def cmfquery_find_producer_execution(artifact_name: str):
    """Retrieve the execution that produced an artifact."""
    execution = await async_api(find_producer_execution, query, artifact_name)
    if execution is None:
        return error_response(
            message="Producer execution not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Producer execution not found for artifact '{artifact_name}'")],
        )

    return success_response(
        data={
            "artifact_name": artifact_name,
            "execution": mlmd_state._execution_to_dict(execution),
        },
        message="Producer execution retrieved successfully",
        code=200,
    )


@router.get("/artifacts/name/{artifact_name:path}", response_model=APIResponse)
async def cmfquery_get_artifact(artifact_name: str):
    """Retrieve artifact metadata by artifact name."""
    artifact = await async_api(get_artifact, query, artifact_name)
    if artifact is None or artifact.empty:
        return error_response(
            message="Artifacts not found",
            code=404,
            errors=[ErrorDetail(field="artifact_name", message=f"Artifact '{artifact_name}' not found")],
        )

    artifact_records = mlmd_state._dataframe_records(artifact)
    return success_response(
        data={
            "artifact_name": artifact_name,
            "artifacts": artifact_records,
            "total_artifacts": len(artifact_records),
        },
        message="Artifact retrieved successfully",
        code=200,
    )


@router.get("/artifacts/metrics/{metrics_name:path}", response_model=APIResponse)
async def cmfquery_get_metrics(metrics_name: str):
    """Retrieve metrics metadata by metrics artifact name."""
    metrics = await async_api(get_metrics, query, metrics_name)
    if metrics is None or metrics.empty:
        return error_response(
            message="Metrics not found",
            code=404,
            errors=[ErrorDetail(field="metrics_name", message=f"Metrics '{metrics_name}' not found")],
        )

    metric_records = mlmd_state._dataframe_records(metrics)
    return success_response(
        data={
            "metrics_name": metrics_name,
            "metrics": metric_records,
            "total_metrics": len(metric_records),
        },
        message="Metrics retrieved successfully",
        code=200,
    )


# ==================== Business Logic Functions For UI ====================

async def get_artifacts_types(state: MlmdState):
    """
    Fetch artifact types from MLMD, excluding the internal 'Environment' type.

    Args:
        state (MlmdState): Shared MLMD query state for the request.

    Returns:
        list[str]: Artifact type names.
    """
    await state.check_mlmd_file_exists()

    artifact_types_list = await async_api(
        get_artifact_types,
        state.query
    )

    if "Environment" in artifact_types_list:
        artifact_types_list.remove("Environment")

    return artifact_types_list


async def get_model_card_by_artifact_id(state: MlmdState, model_id: int):
    """
    Get model card details (model, execution, input/output artifacts) for a model artifact id.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        model_id (int): Id of the artifact; must be of type 'Model'.

    Returns:
        list: [model_data, model_executions, input_artifacts, output_artifacts] as JSON records,
            with "" in place of any dataframe that was empty.

    Raises:
        HTTPException: 404 if the artifact id does not exist, 400 if it is not a Model artifact.
    """
    await state.check_mlmd_file_exists()

    model_artifact = await async_api(
        CmfQuery.get_all_artifacts_by_ids_list,
        state.query,
        [model_id]
    )
    if model_artifact.empty:
        raise HTTPException(status_code=404, detail=f"Model artifact with id {model_id} not found")

    artifact_type = model_artifact["type"].tolist()[0]
    if artifact_type != "Model":
        raise HTTPException(status_code=400, detail=f"Artifact id {model_id} is not a Model artifact")

    model_data_df, model_exe_df, model_input_art_df, model_output_art_df = await async_api(
        get_model_data,
        state.query,
        model_id
    )
    # Each element is JSON records for one dataframe, or "" when that dataframe is empty.
    return [
        json.loads(model_data_df.to_json(orient="records")) if not model_data_df.empty else "",
        json.loads(model_exe_df.to_json(orient="records")) if not model_exe_df.empty else "",
        json.loads(model_input_art_df.to_json(orient="records")) if not model_input_art_df.empty else "",
        json.loads(model_output_art_df.to_json(orient="records")) if not model_output_art_df.empty else "",
    ]


# ==================== Business Logic Functions For CMFQuery ====================

def get_all_artifacts(query: CmfQuery):
    """Return all artifact names from the CMFQuery backend."""
    return query.get_all_artifacts()


def get_all_artifacts_by_context(query: CmfQuery, pipeline_name: str):
    """Return artifacts associated with the requested pipeline context."""
    return query.get_all_artifacts_by_context(pipeline_name)


def get_all_artifacts_by_ids_list(query: CmfQuery, artifact_ids: list[int]):
    """Return artifacts matching the requested artifact identifiers."""
    return query.get_all_artifacts_by_ids_list(artifact_ids)


def get_artifact_df(query: CmfQuery, artifact_name: str):
    """Return dataframe-formatted metadata for the requested artifact."""
    artifact = query._get_artifact(artifact_name)
    if artifact is None:
        return None
    return query.get_artifact_df(artifact)


def get_artifact(query: CmfQuery, artifact_name: str):
    """Return metadata for the requested artifact name."""
    return query.get_artifact(artifact_name)


def get_all_executions_for_artifact(query: CmfQuery, artifact_name: str):
    """Return executions associated with the requested artifact name."""
    return query.get_all_executions_for_artifact(artifact_name)


def get_all_executions_for_artifact_id(query: CmfQuery, artifact_id: int):
    """Return executions associated with the requested artifact ID."""
    return query.get_all_executions_for_artifact_id(artifact_id)


def get_one_hop_child_artifacts(query: CmfQuery, artifact_name: str, pipeline_id: Optional[int]):
    """Return direct child artifacts for the requested artifact."""
    return query.get_one_hop_child_artifacts(artifact_name, pipeline_id)


def get_all_child_artifacts(query: CmfQuery, artifact_name: str):
    """Return all downstream child artifacts for the requested artifact."""
    return query.get_all_child_artifacts(artifact_name)


def get_one_hop_parent_artifacts(query: CmfQuery, artifact_name: str):
    """Return direct parent artifacts for the requested artifact."""
    return query.get_one_hop_parent_artifacts(artifact_name)


def get_one_hop_parent_artifacts_with_id(query: CmfQuery, artifact_id: int):
    """Return direct parent artifacts for the requested artifact ID."""
    return query.get_one_hop_parent_artifacts_with_id(artifact_id)


def get_all_parent_artifacts(query: CmfQuery, artifact_name: str):
    """Return all upstream parent artifacts for the requested artifact."""
    return query.get_all_parent_artifacts(artifact_name)


def get_all_parent_executions(query: CmfQuery, artifact_name: str):
    """Return parent executions associated with the requested artifact."""
    return query.get_all_parent_executions(artifact_name)


def find_producer_execution(query: CmfQuery, artifact_name: str):
    """Return the execution that produced the requested artifact."""
    return query.find_producer_execution(artifact_name)


def get_metrics(query: CmfQuery, metrics_name: str):
    """Return metrics metadata for the requested metrics artifact name."""
    return query.get_metrics(metrics_name)