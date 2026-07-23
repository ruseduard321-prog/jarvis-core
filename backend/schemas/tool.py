from __future__ import annotations

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """Read-only tool metadata."""

    slug: str = Field(description="Stable tool slug")
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    capabilities: list[str] = Field(default_factory=list, description="Stable tool capabilities")
