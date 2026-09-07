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
Artifact API endpoints and business logic.

This module contains artifact-related API endpoints and their business logic,
including artifact types.
"""
from fastapi import APIRouter, HTTPException, Request
from server.app.schemas.responses import success_response
from server.app.services.mlmd_state import MlmdState
from server.app.get_data import (
    get_artifact_types,
    async_api,
    get_model_data
)
import json
from cmflib.cmfquery import CmfQuery

router = APIRouter(prefix="/v1", tags=["artifacts"])

# ==================== API Endpoints ====================

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

# ==================== Business Logic Functions ====================

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