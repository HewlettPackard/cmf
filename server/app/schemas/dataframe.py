from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
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
# class ExecutionRequest(BaseRequest):
#     sort_field: str = Field("Context_Type", description="Column to sort by (default: Context_Type)")


class ExecutionByStageRequest(BaseRequest):
    stage_name: str = Field(..., description="Stage name (Context_Type value)")
    sort_order: str = Field("DESC", description="Sort order: ASC or DESC")


# Query parameters for artifact (legacy, non-stage).
# Deprecated: kept for reference during rollback.
# class ArtifactRequest(BaseRequest):
#     sort_field: str = Field("name", description="Column to sort by (default: name)")


class ArtifactByStageRequest(BaseRequest):
    sort_field: str = Field("name", description="Column to sort by (default: name)")
    stage_name: str = Field(..., description="Stage name (Context_Type value)")
    artifact_type: str = Field(..., description="Artifact type to filter")


# Define a Pydantic model for the request body
class ServerRegistrationRequest(BaseModel):
    server_name: str
    server_url: str
    last_sync_time: Optional[int] = Field(None, description="Epoch time in seconds")


class AcknowledgeRequest(BaseModel):
    server_name: str
    server_url: str


# Don't forget description
class MLMDPullRequest(BaseModel):
    pipeline_name:Optional[str] = Field(None, description="Name of the pipeline")
    exec_uuid: Optional[str] = Field(None, description="Execution UUID")
    last_sync_time: Optional[int] = Field(None, description="Epoch time in seconds")
    

class ScheduleCreateRequest(BaseModel):
    server_id: int = Field(..., description="Registered server id")
    timezone: str = Field("UTC", description="IANA timezone, e.g., UTC, America/New_York, Europe/London")
    start_time_local_iso: str = Field(..., description="Local ISO datetime, e.g., 2026-01-04T15:00")
    one_time: bool = Field(False, description="If true, run only once and deactivate")
    
    # New recurrence mode fields (only for periodic syncs)
    recurrence_mode: Optional[str] = Field(None, description="Recurrence mode: interval (every fixed gap, e.g., every 6 hours), daily (once per day at a specific time), or weekly (once per week on a specific day and time).")
    interval_unit: Optional[str] = Field(None, description="For interval mode: 'minutes' or 'hours'")
    interval_value: Optional[int] = Field(None, gt=0, description="For interval mode: number of units")
    daily_time: Optional[str] = Field(None, description="For daily mode: HH:MM time")
    weekly_day: Optional[str] = Field(None, description="For weekly mode: day of week (monday, tuesday, etc.)")
    weekly_time: Optional[str] = Field(None, description="For weekly mode: HH:MM time")

    @model_validator(mode='after')
    def apply_defaults_and_validate(self):
        """This validator is the safety gate for direct/standalone API usage.
        It ensures the payload is consistent even when clients call the API
        without UI-side checks.
        """
        # One-time schedules must not carry periodic recurrence fields.
        if self.one_time:
            self.recurrence_mode = None
            self.interval_unit = None
            self.interval_value = None
            self.daily_time = None
            self.weekly_day = None
            self.weekly_time = None
            return self

        # Default periodic mode for clients that omit recurrence_mode.
        if not self.recurrence_mode:
            self.recurrence_mode = 'interval'

        if self.recurrence_mode not in {'interval', 'daily', 'weekly'}:
            raise ValueError("recurrence_mode must be one of: interval, daily, weekly")

        # Parse once and reuse HH:MM when mode-specific time is missing.
        try:
            derived_time = datetime.strptime(self.start_time_local_iso, "%Y-%m-%dT%H:%M").strftime("%H:%M")
        except ValueError as exc:
            raise ValueError("start_time_local_iso must use YYYY-MM-DDTHH:MM") from exc

        if self.recurrence_mode == 'interval':
            if not self.interval_unit:
                self.interval_unit = 'hours'
            if not self.interval_value:
                self.interval_value = 6
            if self.interval_unit not in {'minutes', 'hours'}:
                raise ValueError("interval_unit must be 'minutes' or 'hours'")
            self.daily_time = None
            self.weekly_day = None
            self.weekly_time = None
        elif self.recurrence_mode == 'daily':
            self.daily_time = self.daily_time or derived_time
            self.interval_unit = None
            self.interval_value = None
            self.weekly_day = None
            self.weekly_time = None
        elif self.recurrence_mode == 'weekly':
            if not self.weekly_day:
                raise ValueError("weekly mode requires weekly_day")
            if self.weekly_day.lower() not in {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}:
                raise ValueError("weekly_day must be a valid day name")
            self.weekly_day = self.weekly_day.lower()
            self.weekly_time = self.weekly_time or derived_time
            self.interval_unit = None
            self.interval_value = None
            self.daily_time = None
        return self


class ScheduleUpdateRequest(BaseModel):
    schedule_id: int = Field(..., description="Schedule id to update")
    timezone: str = Field("UTC", description="IANA timezone")
    start_time_local_iso: Optional[str] = Field(None, description="Local ISO datetime")
    one_time: Optional[bool] = Field(None, description="Toggle one-time behavior")
