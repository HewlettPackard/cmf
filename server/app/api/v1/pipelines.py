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

Pipeline API endpoints and business logic.

This module contains API endpoints for pipeline discovery, stage queries,
executions, artifacts, and execution/artifact lineage.
"""

import json

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.app.db.dbconfig import get_db
from server.app.db.dbqueries import (
    fetch_unique_execution_stages,
    fetch_artifact_types_by_stage,
    fetch_artifacts_by_stage,
    fetch_executions_by_stage,
    fetch_unique_execution_stages
)
from server.app.schemas.responses import success_response
from server.app.services.mlmd_state import MlmdState
from typing import List, Dict, Any, Optional
from server.app.get_data import async_api
from server.app.query_execution_lineage_d3tree import (query_execution_lineage_d3tree)
from server.app.query_artifact_lineage_d3tree import (query_artifact_lineage_d3tree)
from server.app.query_visualization_artifact_execution import (query_visualization_artifact_execution)
from server.app.schemas.requests import (
    ArtifactByStageRequest,
    ExecutionByStageRequest
)
from cmflib.cmfquery import CmfQuery
from server.app.get_data import (
    async_api,
    executions_list,
    get_mlmd_from_server,
    convert_mlmd_to_hierarchical_lineage_json,
)
from server.app.api.v1.env import get_python_env as read_python_env

router = APIRouter(prefix="/v1", tags=["pipelines"])

# ==================== API Endpoints ====================

@router.get("/pipelines")
async def list_pipelines(request: Request):
    """
    Get the pipeline names available in the current MLMD store.

    Method: GET
    Path: /v1/pipelines

    Returns:
        JSONResponse: success_response wrapping the list of pipeline names.
    """
    state = request.app.state.mlmd
    result = await pipelines(state)
    return success_response(
        data=result,
        message="Pipelines retrieved successfully",
        code=200,
    )


@router.get("/pipelines/{pipeline_name}/stages")
async def pipeline_stages(pipeline_name: str, db: AsyncSession = Depends(get_db)):
    """
    Get the unique execution stages for a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/stages

    Args:
        pipeline_name (str): Name of the pipeline.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the list of stage names.
    """
    result = await get_pipeline_stages(pipeline_name, db)
    return success_response(
        data=result,
        message="Pipeline stages retrieved successfully",
        code=200,
    )


@router.get("/pipelines/{pipeline_name}/executions/{uuid}/lineage")
async def get_execution_lineage(
    request: Request,
    uuid: str,
    pipeline_name: str
):
    """
    Get the tangled-tree execution lineage for an execution in a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/executions/{uuid}/lineage

    Args:
        uuid (str): Execution uuid to build the lineage from.
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping nodes/links for the lineage graph.
    """
    state = request.app.state.mlmd
    result = await execution_lineage_tangled(
        state=state,
        uuid=uuid,
        pipeline_name=pipeline_name
    )

    return success_response(
        data=result,
        message="Execution lineage retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/artifacts/lineage")
async def get_artifact_lineage(
    request: Request,
    pipeline_name: str
):
    """
    Get the tangled-tree artifact lineage for a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/artifacts/lineage

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping the nested artifact lineage list.
    """
    state = request.app.state.mlmd
    result = await artifact_lineage_tangled(
        state=state,
        pipeline_name=pipeline_name
    )

    return success_response(
        data=result,
        message="Artifact lineage retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/hierarchical-lineage")
async def get_hierarchical_lineage(
    request: Request,
    pipeline_name: str
):
    """
    Get the hierarchical lineage graph for a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/hierarchical-lineage

    Returns:
        JSONResponse: success_response wrapping the React Flow lineage data.
    """
    state = request.app.state.mlmd
    json_payload = await async_api(
        get_mlmd_from_server,
        state.query,
        pipeline_name,
        None,
        None,
        state.dict_of_exe_ids,
    )

    if json_payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_name}' not found or contains no MLMD data."
        )

    if isinstance(json_payload, str):
        try:
            json_payload = json.loads(json_payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse the MLMD response as JSON: {error}"
            )

    try:
        result = convert_mlmd_to_hierarchical_lineage_json(json_payload, pipeline_name)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert the MLMD payload to hierarchical lineage JSON: {error}"
        )

    return success_response(
        data=result,
        message="Hierarchical lineage retrieved successfully",
        code=200,
    )


@router.get("/pipelines/{pipeline_name}/artifact-executions/lineage")
async def get_artifact_execution_lineage(
    request: Request,
    pipeline_name: str
):
    """
    Get the lineage graph connecting artifacts and executions in a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/artifact-executions/lineage

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping the combined lineage visualization data.
    """
    state = request.app.state.mlmd
    result = await artifact_execution_lineage(
        state=state,
        pipeline_name=pipeline_name
    )

    return success_response(
        data=result,
        message="Artifact-execution lineage retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/artifacts")
async def get_artifacts(request: Request, pipeline_name: str):
    """
    Get all artifacts for a pipeline without pagination or filtering.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/artifacts

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping the list of artifacts.
    """
    state = request.app.state.mlmd
    result = await get_all_artifacts(state, pipeline_name)
    return success_response(
        data=result,
        message="Pipeline artifacts retrieved successfully",
        code=200
    )


@router.post("/pipelines/{pipeline_name}/stages/{stage:path}/artifacts/types")
async def get_artifact_types_by_stage_route(
    pipeline_name: str,
    stage: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get artifact types available in a pipeline stage.

    Method: POST
    Path: /v1/pipelines/{pipeline_name}/stages/{stage}/artifacts/types

    Args:
        pipeline_name (str): Name of the pipeline.
        stage (str): Stage name (Context_Type value) to filter by.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping the list of artifact type names.
    """
    result = await get_artifact_types_by_stage(
        pipeline_name,
        stage,
        db
    )
    return success_response(
        data=result,
        message="Artifact types retrieved successfully",
        code=200
    )


@router.post("/pipelines/{pipeline_name}/stages/{stage:path}/artifacts")
async def get_artifacts_by_stage_route(
    query_params: ArtifactByStageRequest,
    pipeline_name: str,
    stage: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated artifacts filtered by pipeline stage and artifact type.

    Method: POST
    Path: /v1/pipelines/{pipeline_name}/stages/{stage}/artifacts

    Args:
        query_params (ArtifactByStageRequest): Artifact type, filter, sort, and pagination options.
        pipeline_name (str): Name of the pipeline.
        stage (str): Stage name (Context_Type value) to filter by.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping total_items and the page of artifacts.
    """
    result = await get_artifacts_by_stage(
        pipeline_name,
        stage,
        query_params.artifact_type,
        query_params.filter_value,
        query_params.active_page,
        query_params.record_per_page,
        query_params.sort_field,
        query_params.sort_order,
        db
    )
    return success_response(
        data=result,
        message="Artifacts retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/executions")
async def get_all_pipeline_executions(request: Request, pipeline_name: str):
    """
    Get all executions for a pipeline without pagination or filtering.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/executions

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping the list of executions.
    """
    state = request.app.state.mlmd
    result = await get_all_executions(state, pipeline_name)
    return success_response(
        data=result,
        message="Pipeline executions retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/executions/list")
async def get_executions(request: Request, pipeline_name: str):
    """
    Get the execution list for a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/executions/list

    Args:
        pipeline_name (str): Name of the pipeline.

    Returns:
        JSONResponse: success_response wrapping the list of execution types.
    """
    state = request.app.state.mlmd
    result = await list_of_executions(
        state=state,
        pipeline_name=pipeline_name
    )
    return success_response(
        data=result,
        message="Executions retrieved successfully",
        code=200
    )


@router.post("/pipelines/{pipeline_name}/stages/{stage:path}/executions")
async def pipeline_executions(
    query_params: ExecutionByStageRequest,
    pipeline_name: str,
    stage: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get executions filtered by pipeline and stage name.

    Method: POST
    Path: /v1/pipelines/{pipeline_name}/stages/{stage}/executions

    Args:
        query_params (ExecutionByStageRequest): Filter, sort, and pagination options.
        pipeline_name (str): Name of the pipeline.
        stage (str): Stage name (Context_Type value) to filter by.
        db (AsyncSession): Database session dependency.

    Returns:
        JSONResponse: success_response wrapping total_items and the page of executions.
    """
    result = await get_executions_by_stage(
        pipeline_name=pipeline_name,
        stage_name= stage,
        active_page=query_params.active_page,
        record_per_page=query_params.record_per_page,
        sort_order=query_params.sort_order,
        filter_value=query_params.filter_value,
        db=db
    )
    return success_response(
        data=result,
        message="Pipeline executions retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/executions/{execution_uuid}/python-env")
async def get_execution_python_env(
    request: Request,
    pipeline_name: str,
    execution_uuid: str
):
    """
    Get the Python environment file associated with an execution.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/executions/{execution_uuid}/python-env

    Args:
        pipeline_name (str): Name of the pipeline.
        execution_uuid (str): Execution uuid (or prefix) to resolve.

    Returns:
        JSONResponse: success_response wrapping the environment file content.
    """
    state = request.app.state.mlmd
    result = await get_python_env_by_execution(state, pipeline_name, execution_uuid)
    return success_response(
        data=result,
        message="Python environment retrieved successfully",
        code=200
    )


@router.get("/pipelines/{pipeline_name}/hierarchical-lineage")
async def get_hierarchical_lineage_route(
    request: Request,
    pipeline_name: str
):
    state = request.app.state.mlmd
    result = await get_hierarchical_lineage(
        state=state,
        pipeline_name=pipeline_name,
    )
    return success_response(
        data=result,
        message="Hierarchical lineage retrieved successfully",
        code=200,
    )


# ==================== Business Logic Functions ====================

async def pipelines(state: MlmdState):
    """
    Get the list of pipeline names present in the current MLMD store.

    Args:
        state (MlmdState): Shared MLMD query state for the request.

    Returns:
        list[str]: Pipeline names, or [] if no MLMD file has been submitted.
    """
    if state.query:
        pipeline_names = state.query.get_pipeline_names()
        return pipeline_names
    else:
        print("No mlmd file submitted.")
        pipeline_names = []
        return pipeline_names


async def get_pipeline_stages(
    pipeline_name: str,
    db: AsyncSession,
):
    """
    Retrieve unique pipeline stages (Context_Type values) for a given pipeline.
    
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
    result = await fetch_unique_execution_stages(db, pipeline_name)
    return result


async def execution_lineage_tangled(
    state: MlmdState,
    uuid: str,
    pipeline_name: str
):
    """
    Build the tangled-tree execution lineage graph for a selected execution UUID.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        uuid (str): Execution uuid to build the lineage from.
        pipeline_name (str): Name of the pipeline the execution belongs to.

    Returns:
        dict: {"nodes": [{"id":"","name":"","execution_uuid":""}], "links": [{"source":1,"target":4}]}
    """
    # checks if mlmd file exists on server
    await state.check_mlmd_file_exists()
    # checks if pipeline exists
    await state.check_pipeline_exists(pipeline_name)

    response = await async_api(
        query_execution_lineage_d3tree,
        state.query,
        pipeline_name,
        state.dict_of_exe_ids,
        uuid
    )

    return response


# This API returns artifact lineage in a nested structure used by the tangled-tree visualization.
async def artifact_lineage_tangled(
    state: MlmdState,
    pipeline_name: str
) -> Optional[List[List[Dict[str, Any]]]]:
    """
    Build the tangled-tree artifact lineage graph for a pipeline.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline.

    Returns:
        A nested list of dictionaries with 'id' and 'parents' keys, e.g.:
        [[{'id': 'data.xml.gz:236d', 'parents': []}],
         [{'id': 'parsed/train.tsv:32b7', 'parents': ['data.xml.gz:236d']}]]
    """
    # checks if mlmd file exists on server
    await state.check_mlmd_file_exists()
    # checks if pipeline exists
    await state.check_pipeline_exists(pipeline_name)

    response = await async_api(
        query_artifact_lineage_d3tree,
        state.query,
        pipeline_name,
        state.dict_of_art_ids
    )

    return response


# Builds the combined artifact + execution lineage graph for the visualization view.
async def artifact_execution_lineage(
    state: MlmdState,
    pipeline_name: str
):
    """
    Get the artifact-execution lineage visualization graph for a pipeline.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline.

    Returns:
        The combined artifact/execution lineage graph used by the visualization view.
    """
    # checks if mlmd file exists on server
    await state.check_mlmd_file_exists()
    # checks if pipeline exists
    await state.check_pipeline_exists(pipeline_name)

    response = await async_api(
        query_visualization_artifact_execution,
        state.query,
        pipeline_name,
        state.dict_of_art_ids,
        state.dict_of_exe_ids
    )

    return response


# Used by the MCP client to retrieve all pipeline artifacts.
async def get_all_artifacts(state: MlmdState, pipeline_name: str):
    """
    Retrieve all artifacts for a pipeline without pagination or filtering.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline.

    Returns:
        list[dict]: Artifact records, or [] if none exist.
    """
    await state.check_mlmd_file_exists()
    await state.check_pipeline_exists(pipeline_name)

    artifacts = await async_api(
        CmfQuery.get_all_artifacts_by_context,
        state.query,
        pipeline_name
    )
    if artifacts.empty:
        return []
    return artifacts.to_dict(orient="records")


async def get_artifact_types_by_stage(
    pipeline_name: str,
    stage_name: str,
    db: AsyncSession
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

async def get_artifacts_by_stage(
    pipeline_name: str,
    stage_name: str,
    artifact_type: str,
    filter_value: str,
    active_page: int,
    record_per_page: int,
    sort_field: str,
    sort_order: str,
    db: AsyncSession
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


# Used by the MCP client to retrieve all pipeline executions.
async def get_all_executions(state: MlmdState, pipeline_name: str):
    """
    Retrieve all executions for a pipeline without pagination or filtering.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline.

    Returns:
        list[dict]: Execution records, or [] if none exist.
    """
    await state.check_mlmd_file_exists()
    await state.check_pipeline_exists(pipeline_name)

    executions = await async_api(
        CmfQuery.get_all_executions_in_pipeline,
        state.query,
        pipeline_name
    )
    if executions.empty:
        return []
    return executions.to_dict(orient="records")


async def list_of_executions(state: MlmdState, pipeline_name: str):
    """
    Get the list of execution types for a pipeline.

    Args:
        state (MlmdState): Shared MLMD query state for the request.
        pipeline_name (str): Name of the pipeline.

    Returns:
        list: Execution type entries for the pipeline.
    """
    # checks if mlmd file exists on server
    await state.check_mlmd_file_exists()
    # checks if pipeline exists
    await state.check_pipeline_exists(pipeline_name)

    response = await async_api(
        executions_list,
        state.query,
        pipeline_name,
        state.dict_of_exe_ids
    )

    return response


async def get_executions_by_stage(
    pipeline_name: str,
    stage_name: str,
    active_page: int,
    record_per_page: int,
    sort_order: str,
    filter_value: str,
    db: AsyncSession
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
    return await fetch_executions_by_stage(db, pipeline_name, stage_name, active_page, record_per_page, sort_order, filter_value)


async def get_pipeline_stages(
    pipeline_name: str,
    db: AsyncSession
):
    """
    NOTE: this redefines `get_pipeline_stages` above and is the version actually
    invoked by the "/pipelines/{pipeline_name}/stages" route, since Python resolves
    the call by name at call time and this later definition overwrites the first.
    Consider renaming or removing one of the two to avoid confusion.

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
    print("DEBUG: get_pipeline_stages called with:", pipeline_name)
    result = await fetch_unique_execution_stages(db, pipeline_name)

    print("DEBUG: result =", result)

    return result


async def get_python_env_by_execution(
    state: MlmdState,
    pipeline_name: str,
    execution_uuid: str
):
    """
    Resolve an execution's Python_Env custom property and return the referenced file's content.

    Args:
        pipeline_name: Name of the pipeline the execution belongs to
        execution_uuid: Execution UUID (or UUID prefix) to match

    Returns:
        str: Content of the associated Python environment file

    Raises:
        HTTPException: If the execution or its Python environment file cannot be found
    """
    await state.check_mlmd_file_exists()
    await state.check_pipeline_exists(pipeline_name)

    executions = await async_api(
        CmfQuery.get_all_executions_in_pipeline,
        state.query,
        pipeline_name
    )
    if executions.empty or "Execution_uuid" not in executions.columns:
        raise HTTPException(status_code=404, detail="Execution not found")

    matching_execution = executions[
        executions["Execution_uuid"].astype(str).apply(
            lambda value: any(
                uuid.strip() == execution_uuid or uuid.strip().startswith(execution_uuid)
                for uuid in value.split(",")
            )
        )
    ]
    if matching_execution.empty:
        raise HTTPException(status_code=404, detail="Execution not found")

    python_env_column = "custom_properties_Python_Env"
    if python_env_column not in matching_execution.columns:
        raise HTTPException(status_code=404, detail="Python environment is not available for this execution")

    python_env_file = matching_execution.iloc[0][python_env_column]
    if not python_env_file:
        raise HTTPException(status_code=404, detail="Python environment is not available for this execution")

    return await read_python_env(str(python_env_file))


async def get_hierarchical_lineage(
    state: MlmdState,
    pipeline_name: str,
):
    """
    Get the hierarchical lineage graph for a pipeline.

    Method: GET
    Path: /v1/pipelines/{pipeline_name}/hierarchical-lineage

    Returns:
        JSONResponse: success_response wrapping the React Flow lineage data.
    """
    json_payload = await async_api(
        get_mlmd_from_server,
        state.query,
        pipeline_name,
        None,
        None,
        state.dict_of_exe_ids,
    )

    if json_payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline '{pipeline_name}' not found or contains no MLMD data."
        )

    if isinstance(json_payload, str):
        try:
            json_payload = json.loads(json_payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse the MLMD response as JSON: {error}"
            )

    try:
        result = convert_mlmd_to_hierarchical_lineage_json(json_payload, pipeline_name)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert the MLMD payload to hierarchical lineage JSON: {error}"
        )
