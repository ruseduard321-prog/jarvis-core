from __future__ import annotations

from pydantic import BaseModel, Field


class MediaPackage(BaseModel):
    """Media production prompts and notes generated from a reviewed script."""

    thumbnail_prompt: str = Field(description="AI-image-ready thumbnail prompt")
    scene_prompts: list[str] = Field(default_factory=list, description="Image prompts per scene/section")
    b_roll_prompts: list[str] = Field(default_factory=list, description="B-roll footage suggestions")
    image_prompts: list[str] = Field(default_factory=list, description="Image prompts by major section")
    animation_prompts: list[str] = Field(default_factory=list, description="Animation/motion-graphics suggestions")
    voice_over_notes: list[str] = Field(default_factory=list, description="Voice-over delivery notes")
    music_direction: str = Field(default="", description="Suggested music mood/direction")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")
