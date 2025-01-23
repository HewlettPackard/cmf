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