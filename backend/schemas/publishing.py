from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PublishedVideo(BaseModel):
    """Final output returned after attempting YouTube publication."""

    video_id: str = Field(description="YouTube video id")
    video_url: str = Field(description="YouTube watch URL")
    title: str = Field(description="Published title")
    description: str = Field(description="Published description")
    visibility: str = Field(description="Requested visibility: private, unlisted, public, or scheduled")
    publish_time: datetime | None = Field(default=None, description="Publish timestamp when known")
    upload_status: str = Field(description="Upload outcome: success, failed, or partial")
    thumbnail_uploaded: bool = Field(description="Whether thumbnail upload succeeded")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata")
