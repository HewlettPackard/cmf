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

"""Unified API response wrapper for all endpoints"""
from datetime import datetime, timezone
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = 1
    per_page: int = 10
    total: int = 0
    has_next: bool = False
    has_prev: bool = False


class ErrorDetail(BaseModel):
    """Field-level or request-level error details"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ResponseMeta(BaseModel):
    """Response metadata"""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    pagination: Optional[PaginationMeta] = None


class APIResponse(BaseModel):
    """Standard response wrapper for all API endpoints"""
    status: Literal["success", "error", "partial"]
    code: int
    data: Any = None
    message: str = ""
    errors: list[ErrorDetail] = Field(default_factory=list)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None,
        }


def success_response(
    data: Any = None,
    message: str = "Success",
    code: int = 200,
    pagination: Optional[PaginationMeta] = None,
) -> APIResponse:
    """
    Build a standardized success APIResponse.

    Args:
        data (Any): Payload to return to the client.
        message (str): Human-readable success message.
        code (int): HTTP status code to embed in the response body.
        pagination (Optional[PaginationMeta]): Pagination metadata, if applicable.

    Returns:
        APIResponse: status="success" response wrapping data and metadata.
    """
    return APIResponse(
        status="success",
        code=code,
        data=data,
        message=message,
        meta=ResponseMeta(
            pagination=pagination,
        ),
    )


def error_response(
    message: str = "Error",
    code: int = 400,
    errors: Optional[list[ErrorDetail | dict[str, Any]]] = None,
    data: Any = None,
) -> APIResponse:
    """
    Build a standardized error APIResponse.

    Args:
        message (str): Human-readable error message.
        code (int): HTTP status code to embed in the response body.
        errors (Optional[list[ErrorDetail | dict]]): Field-level or request-level error details.
        data (Any): Optional partial payload to return alongside the error.

    Returns:
        APIResponse: status="error" response wrapping the message and errors.
    """
    return APIResponse(
        status="error",
        code=code,
        data=data,
        message=message,
        errors=errors or [],
    )


def partial_response(
    data: Any = None,
    message: str = "Partial success",
    code: int = 206,
    errors: Optional[list[ErrorDetail | dict[str, Any]]] = None,
    pagination: Optional[PaginationMeta] = None,
) -> APIResponse:
    """Create a partial success response"""
    return APIResponse(
        status="partial",
        code=code,
        data=data,
        message=message,
        errors=errors or [],
        meta=ResponseMeta(
            pagination=pagination,
        ),
    )
