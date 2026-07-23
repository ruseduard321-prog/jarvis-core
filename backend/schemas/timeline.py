from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ScenePacing(str, Enum):
    """Rhythm category assigned to one scene's position in the production.

    Assigned purely from a scene's position in the sequence (see
    DeterministicTimelinePlanner) — never from CompositionPlan, since
    CompositionPlan consumes TimelinePlan and not the other way around.
    """

    FAST = "fast"
    STANDARD = "standard"
    SLOW = "slow"
    DRAMATIC_PAUSE = "dramatic_pause"
    CLIMAX = "climax"
    BREATHING = "breathing"


class SceneTiming(BaseModel):
    """One scene's authoritative position on the production timeline."""

    scene_number: int = Field(description="Matching Scene.scene_number")
    order: int = Field(description="1-based position in the final sequence; TimelinePlan owns ordering, not scene_number")
    start_seconds: float = Field(default=0.0, description="Scene start on the shared production timeline")
    end_seconds: float = Field(default=0.0, description="Scene end on the shared production timeline")
    duration_seconds: float = Field(default=0.0, description="end_seconds - start_seconds")
    pacing: ScenePacing = Field(default=ScenePacing.STANDARD, description="Rhythm category driving the duration multiplier")


class TimelinePlan(BaseModel):
    """The single source of truth for WHEN things happen in the production: scene
    ordering, scene duration, start/end time, and pacing. Produced once, right
    after Scene Planning, by TimelinePlanner. CompositionPlan consumes this
    (carrying each scene's SceneTiming forward) and AudioTimelinePlanner consumes
    this directly — neither is allowed to compute timing independently.
    DeterministicTimelinePlanner resolves this today from ScenePlan plus the real
    measured narration duration; F28's AI Director is expected to produce
    TimelinePlans directly later, with no change to any consumer."""

    total_duration_seconds: float = Field(default=0.0, description="Total real (measured) production duration")
    scenes: list[SceneTiming] = Field(default_factory=list, description="Ordered per-scene timing, one entry per planned scene")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")

    def timing_for(self, scene_number: int) -> SceneTiming | None:
        """Convenience lookup used by every consumer instead of re-deriving timing."""
        for timing in self.scenes:
            if timing.scene_number == scene_number:
                return timing
        return None
