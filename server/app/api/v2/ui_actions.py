"""
UI Actions API endpoints for v2.

This module contains v2 endpoints backing UI-triggered actions.
"""

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.db.dbconfig import get_db
from server.app.db.dbqueries import get_artifact_id_by_filename, insert_label_content
from server.app.schemas.responses import success_response
from server.app.utils import extract_csv_text_content

router = APIRouter(prefix="/v2", tags=["ui-actions"])


@router.post("/label")
async def upload_label_file(
    file: UploadFile = File(..., description="The file to upload"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV label file and index its content for artifact search.

    Method: POST
    Path: /v2/label

    Returns:
        JSONResponse: success_response wrapping upload and indexing details.
    """
    result = await upload_label(file, db)
    return success_response(
        data=result,
        message="Label uploaded successfully",
        code=201,
    )


async def upload_label(file: UploadFile, db: AsyncSession):
    """
    Save an uploaded label CSV file and index its searchable text content.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided.")

        labels_dir = "/cmf-server/data/labels"
        file_path = os.path.join(labels_dir, os.path.basename(file.filename))

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

        try:
            full_text_content, is_truncated = extract_csv_text_content(file_path)
            if is_truncated:
                print(f"Warning: CSV content was truncated for file: {file.filename}")
        except Exception as error:
            print(f"Error extracting CSV content for {file.filename}: {error}")
            return {
                "message": f"File '{file.filename}' uploaded successfully to {labels_dir}.",
                "warning": f"Could not extract searchable content: {error}",
            }

        artifact_id = await get_artifact_id_by_filename(db, file.filename)
        if artifact_id is None:
            print(f"Warning: Could not find artifact_id for file: {file.filename}")
            return {
                "message": f"File '{file.filename}' uploaded successfully to {labels_dir}.",
                "warning": "Artifact not found in database. Content not indexed for search.",
            }

        result = await insert_label_content(db, artifact_id, file.filename, full_text_content)
        if result["status"] == "success":
            return {
                "message": f"File '{file.filename}' uploaded successfully to {labels_dir}.",
                "indexed": True,
                "artifact_id": artifact_id,
                "truncated": is_truncated,
            }

        return {
            "message": f"File '{file.filename}' uploaded successfully to {labels_dir}.",
            "warning": f"Content indexing failed: {result['message']}",
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {error}") from error