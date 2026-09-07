import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from server.app.schemas.responses import success_response
from fastapi.responses import StreamingResponse
import zipfile
import io
import os
from typing import Optional

router = APIRouter(prefix="/v1", tags=["environment"])

# ==================== API Endpoints ====================

@router.post("/python-env")
async def upload_python_environment(file: UploadFile = File(..., description="The Python environment file to upload")):
    """
    Upload a Python environment file to the server environment directory.

    Method: POST
    Path: /v1/python-env

    Args:
        file (UploadFile): The Python environment file (.txt or .yaml) to store.

    Returns:
        JSONResponse: success_response wrapping the upload confirmation message.
    """
    result = await upload_python_env(file)

    return success_response(
        data=result,
        message="Python environment uploaded successfully",
        code=201
    )


@router.get("/python-env")
async def get_python_environment(file_name: str):
    """
    Retrieve the contents of a stored Python environment file.

    Method: GET
    Path: /v1/python-env

    Args:
        file_name (str): Name of the file to fetch. Must end with .txt or .yaml.

    Returns:
        JSONResponse: success_response wrapping the file content as plain text.
    """
    result = await get_python_env(file_name)

    return success_response(
        data=result,
        message="Python environment retrieved successfully",
        code=200
    )


@router.get("/python-env/download")
async def download_python_env_route(list_of_files: Optional[list[str]] = Query(None)):
    """
    Download one or more Python environment files as a ZIP archive.

    Method: GET
    Path: /v1/python-env/download

    Args:
        list_of_files (Optional[list[str]]): File names to include; all files if omitted.

    Returns:
        StreamingResponse: The ZIP archive as an application/zip download.
    """
    return download_python_env(list_of_files)


# ==================== Business Logic Functions ====================

async def upload_python_env(file: UploadFile):
    """
    Save an uploaded Python environment file to /cmf-server/data/env/.

    Args:
        file (UploadFile): The uploaded file.

    Returns:
        dict: Confirmation message with the stored file name.

    Raises:
        HTTPException: 400 if no filename is provided, 500 on write failure.
    """
    try:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded")

        file_path = os.path.join("/cmf-server/data/env/", os.path.basename(file.filename))

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return {
            "message": f"File '{file.filename}' uploaded successfully"
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}") from e


async def get_python_env(file_name: str) -> str:
    """
    Fetch the content of a stored requirements file from /cmf-server/data/env/.

    Args:
        file_name (str): The name of the file to be fetched. Must end with .txt or .yaml.

    Returns:
        str: The content of the file as plain text.

    Raises:
        HTTPException: If the file does not exist or the extension is unsupported.
    """
    # Validate file extension
    if not (file_name.endswith(".txt") or file_name.endswith(".yaml")):
        raise HTTPException(status_code=400, detail="Unsupported file extension. Use .txt or .yaml")
    # Check if the file exists
    file_path = os.path.join("/cmf-server/data/env/", os.path.basename(file_name))

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
     # Read and return the file content as plain text
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def download_python_env(list_of_files: Optional[list[str]] = None):
    """
    Compress the requested (or all) files under /cmf-server/data/env/ into a ZIP and stream it back.

    Args:
        list_of_files (Optional[list[str]]): File names to include; all files if omitted.

    Returns:
        StreamingResponse: The ZIP archive as an application/zip download.

    Raises:
        HTTPException: 404 if the directory or a requested file does not exist.
    """
    try:
        DIRECTORY = "/cmf-server/data/env/" # Directory to be compressed
        #  Check if the directory exists
        if not os.path.exists(DIRECTORY):
            raise HTTPException(status_code=404, detail="Directory does not exist")
        # Determine files to include in the ZIP
        files_to_zip = []
        # if list_of_files is provided, include only those files
        # else include all files in the directory
        if list_of_files:
            for file_name in list_of_files:
                file_path = os.path.join(DIRECTORY, file_name)
                if os.path.exists(file_path):
                    files_to_zip.append((file_path, file_name))
                else:
                    raise HTTPException(status_code=404, detail=f"File {file_name} does not exist")
        else:
            if not os.listdir(DIRECTORY):
                raise HTTPException(status_code=404, detail="Directory is empty")
            for root, _, files in os.walk(DIRECTORY):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, DIRECTORY)
                    files_to_zip.append((file_path, arcname))

        # Create and send the ZIP file 
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer,"w",zipfile.ZIP_DEFLATED,) as zip_file:
            for file_path, arcname in files_to_zip:
                zip_file.write(file_path, arcname)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={'python_env_files.zip' if list_of_files else 'python_env_folder.zip'}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
