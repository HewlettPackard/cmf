from pydantic import BaseModel, Field, model_validator
from typing import Optional
import json


# Pydantic model for the request body in the MLMD push API.
class MLMDPushRequest(BaseModel): 
    # ... indicates required field
    exec_uuid: Optional[str] = Field(None, description="Optional execution uuid for the request")
    pipeline_name: str = Field(..., min_length=1, description="Name of the pipeline")
    json_payload: str = Field(..., description="JSON payload for the pipeline")

    # Custom validation for pipeline name and JSON payload
    @model_validator(mode="after")
    def validate_fields(cls, values):
        if not values.pipeline_name.strip():
            raise ValueError("Pipeline name must not be empty or whitespace")
        if not values.json_payload:
            raise ValueError("JSON payload must not be empty")
        # Attempt to parse the JSON payload to ensure it is valid JSON
        try:
            json.loads(values.json_payload)  # Try to load the JSON string
        except json.JSONDecodeError:
            raise ValueError("JSON payload is not valid JSON")  # Raise error if invalid JSON

        return values

# Base query parameters for pagination, sorting, and filtering.
class BaseRequest(BaseModel):
    page: int = Field(1, gt=0, description="Page number")  # Page must be > 0
    per_page: int = Field(5, le=100, description="Items per page, max 100")  # Limit per page to max 100
    sort_order: str = Field("asc", description="Sort order (asc or desc)")
    filter_by: Optional[str] = Field(None, description="Filter by column")
    filter_value: Optional[str] = Field(None, description="Filter value")

# Query parameters for execution.
class ExecutionRequest(BaseRequest):
    sort_field: str = Field("Context_Type", description="Column to sort by (default: Context_Type)")

# Query parameters for artifact.
class ArtifactRequest(BaseRequest):
    sort_field: str = Field("name", description="Column to sort by (default: name)")