from pydantic import BaseModel, Field, model_validator
from typing import Optional
import json


# Pydantic model for the request body in the MLMD push API.
class MLMDPushRequest(BaseModel): 
    # ... indicates required field
    exec_uuid: Optional[str] = Field(None, description="Optional execution uuid for the request")
    pipeline_name: Optional[str] = Field(..., min_length=1, description="Name of the pipeline")
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
    active_page: int = Field(1, gt=0, description="Page number")  # Page must be > 0
    sort_order: str = Field("asc", description="Sort order (asc or desc)")
    record_per_page: int = Field(5, gt=0, description="Number of records per page")  # Records per page must be > 0
    filter_value: str = Field("", description="Search based on value")

# Query parameters for execution.
class ExecutionRequest(BaseRequest):
    sort_field: str = Field("Context_Type", description="Column to sort by (default: Context_Type)")

# Query parameters for artifact.
class ArtifactRequest(BaseRequest):
    sort_field: str = Field("name", description="Column to sort by (default: name)")


# Define a Pydantic model for the request body
class ServerRegistrationRequest(BaseModel):
    server_name: str
    host_info: str
    last_sync_time: Optional[int] = Field(None, description="Epoch time in seconds")


class AcknowledgeRequest(BaseModel):
    server_name: str
    host_info: str

# Don't forget description
class MLMDPullRequest(BaseModel):
    pipeline_name:Optional[str] = Field(None, description="")
    exec_uuid: Optional[str] = Field(None, description="")
    last_sync_time: Optional[int] = Field(None, description="Epoch time in seconds")
    

    