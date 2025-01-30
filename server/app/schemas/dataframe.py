from pydantic import BaseModel, HttpUrl, Field, model_validator
import pandas as pd
from typing import Sequence, Optional


class ExecutionDataFrame(BaseModel):
    context_id: str
    context_type: str
    execution: str

class MLMDPushRequest(BaseModel):
    id: Optional[int] = Field(None, description="Optional execution id for the request")
    pipeline_name: str = Field(..., min_length=1, description="Name of the pipeline (cannot be empty)")
    json_payload: str = Field(..., description="JSON payload for the pipeline (cannot be empty)")

    @model_validator(mode="after")
    def validate_fields(cls, values):
        if not values.pipeline_name.strip():
            raise ValueError("Pipeline name must not be empty or whitespace")
        if not values.json_payload:
            raise ValueError("JSON payload must not be empty")
        return values

class MLMDRequest(BaseModel):
    exec_id: int | None = Field(
        ..., 
        description="Execution ID must be an integer. It is a required field but can be null."
    )

class ExecutionsQueryParams(BaseModel):
    page: int = Field(1, gt=0, description="Page number")  # Page must be > 0
    per_page: int = Field(5, le=100, description="Items per page, max 100")  # Limit per page to max 100
    sort_field: str = Field("Context_Type", description="Column to sort by")
    sort_order: str = Field("asc", description="Sort order (asc or desc)")
    filter_by: Optional[str] = Field(None, description="Filter by column")
    filter_value: Optional[str] = Field(None, description="Filter value")

class ArtifactsQueryParams(BaseModel):
    page: int = Field(1, gt=0, description="Page number")  # Page must be > 0
    per_page: int = Field(5, le=100, description="Items per page, max 100")  # Limit per page to max 100
    sort_field: str = Field("name", description="Column to sort by")
    sort_order: str = Field("asc", description="Sort order (asc or desc)")
    filter_by: Optional[str] = Field(None, description="Filter by column")
    filter_value: Optional[str] = Field(None, description="Filter value")