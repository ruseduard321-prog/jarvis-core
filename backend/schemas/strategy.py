from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyPackage(BaseModel):
    """Content strategy output produced from a research package, guiding the Writer Agent."""

    topic: str = Field(description="Original topic")
    target_audience: str = Field(description="Who this content is made for")
    positioning: str = Field(description="How this content should be framed relative to similar content")
    hook: str = Field(description="Suggested opening hook direction")
    retention_strategy: list[str] = Field(default_factory=list, description="Tactics to sustain viewer retention")
    emotional_arc: list[str] = Field(default_factory=list, description="Intended emotional beats across the piece")
    pacing: str = Field(description="Recommended pacing guidance")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")
