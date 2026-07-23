from __future__ import annotations

from pydantic import BaseModel, Field


class ProductionRunRequest(BaseModel):
    """Request to trigger a full YouTube production pipeline run."""

    topic: str = Field(description="Topic to produce a video about")


class ProductionRunResponse(BaseModel):
    """F1: status/outcome of a YouTube production pipeline run, retrievable at any
    point in its lifecycle — not only once it finishes. Returned immediately (with
    status="pending") by POST /production/runs, and again by GET
    /production/runs/{execution_id} as it progresses through "running" and finally
    "success"/"failed"."""

    execution_id: str = Field(description="Unique id of this workflow run")
    status: str = Field(description="Run status: pending, running, success, or failed")
    output_folder: str | None = Field(default=None, description="Folder the run artifacts were exported to, when successful")
    files_written: list[str] = Field(default_factory=list, description="Artifact filenames written, when successful")
    step_statuses: dict[str, str] = Field(default_factory=dict, description="Per-step status keyed by step name")
    failed_step: str | None = Field(default=None, description="Name of the step that failed, when status is failed")
    error: str | None = Field(default=None, description="Failure reason, when status is failed")
