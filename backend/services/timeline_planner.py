from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.config import Settings
from backend.schemas.assets import ScenePlan
from backend.schemas.timeline import ScenePacing, SceneTiming, TimelinePlan

# Relative weight applied to each scene's proportional share of the real narration
# duration before the whole set is rescaled back to sum to that exact duration.
# Values close to 1.0 by design — this creates rhythm without ever starving a scene
# of screen time or ballooning the total runtime.
_PACING_MULTIPLIERS: dict[ScenePacing, float] = {
    ScenePacing.FAST: 0.75,
    ScenePacing.STANDARD: 1.0,
    ScenePacing.SLOW: 1.25,
    ScenePacing.DRAMATIC_PAUSE: 1.4,
    ScenePacing.CLIMAX: 1.3,
    ScenePacing.BREATHING: 1.15,
}


def _pacing_for_position(index: int, count: int) -> ScenePacing:
    """Assigns a rhythm category from a scene's position only — deliberately
    independent of any purpose/style decision, since CompositionPlan consumes
    TimelinePlan and never the other way around. Produces a generic rising-action
    arc: brisk setup, steady development, a slow build, a dramatic pause, a climax,
    and a breathing resolution — genre-agnostic, driven by position alone."""
    if count == 1:
        return ScenePacing.STANDARD
    if index == 0:
        return ScenePacing.STANDARD
    if index == count - 1:
        return ScenePacing.BREATHING
    if index == count - 2:
        return ScenePacing.CLIMAX

    ratio = index / (count - 1)
    if ratio < 0.3:
        return ScenePacing.FAST
    if ratio < 0.6:
        return ScenePacing.STANDARD
    if ratio < 0.85:
        return ScenePacing.SLOW
    return ScenePacing.DRAMATIC_PAUSE


class TimelinePlanner(ABC):
    """Resolves the authoritative TimelinePlan for a production — the single seam
    where scene ordering, duration, start/end time, and pacing are ever computed.
    F28 (AI Director) is expected to add an LLM-driven implementation of this
    interface later; every downstream consumer (CompositionPlanner,
    AudioTimelinePlanner, CompositionAwareShotPlanner) only ever reads timing from
    the TimelinePlan it's given, so none of them need to change when that happens."""

    @abstractmethod
    def plan(self, *, scene_plan: ScenePlan, total_duration_seconds: float) -> TimelinePlan:
        """Returns the TimelinePlan covering every scene in scene_plan, with
        per-scene durations summing to exactly total_duration_seconds."""


class DeterministicTimelinePlanner(TimelinePlanner):
    """F27 implementation: assigns each scene a pacing category from its position
    in the sequence (see _pacing_for_position), converts pacing to a duration
    multiplier, and normalizes so the sum of all scene durations equals the real
    measured narration duration exactly. No LLM call — zero added cost. This is
    the one place per-scene duration is ever computed in the whole pipeline."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(self, *, scene_plan: ScenePlan, total_duration_seconds: float) -> TimelinePlan:
        scenes = sorted(scene_plan.scenes, key=lambda scene: scene.scene_number)
        count = len(scenes)
        if count == 0 or total_duration_seconds <= 0:
            return TimelinePlan(
                total_duration_seconds=max(total_duration_seconds, 0.0),
                scenes=[],
                metadata={"status": "skipped", "reason": "No scenes or no measurable duration to allocate"},
            )

        pacings = [_pacing_for_position(index, count) for index in range(count)]
        base_share = total_duration_seconds / count
        raw_durations = [base_share * _PACING_MULTIPLIERS[pacing] for pacing in pacings]
        raw_total = sum(raw_durations)
        scale = total_duration_seconds / raw_total if raw_total > 0 else 1.0
        durations = [raw * scale for raw in raw_durations]

        timings: list[SceneTiming] = []
        cursor = 0.0
        for order, (scene, pacing, duration) in enumerate(zip(scenes, pacings, durations), start=1):
            start = cursor
            end = start + duration
            timings.append(
                SceneTiming(
                    scene_number=scene.scene_number,
                    order=order,
                    start_seconds=start,
                    end_seconds=end,
                    duration_seconds=duration,
                    pacing=pacing,
                )
            )
            cursor = end

        return TimelinePlan(
            total_duration_seconds=total_duration_seconds,
            scenes=timings,
            metadata={"status": "success"},
        )
