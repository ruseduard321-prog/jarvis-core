from __future__ import annotations

from backend.schemas.ai_director import AIDirectorPlan
from backend.schemas.assets import ScenePlan
from backend.schemas.composition import CompositionPlan, SceneComposition, VisualBeat
from backend.schemas.timeline import SceneTiming, TimelinePlan
from backend.services.ai_director_provider import AIDirectorValidationError

# Defensive bound on AI-authored motif count — the AI Director is the creative
# authority so this is not a creative restriction, only a sanity ceiling against
# pathological output (mirrors DeterministicCompositionPlanner's own _MAX_MOTIFS,
# doubled since a real creative pass may legitimately track more threads).
_MAX_MOTIFS = 10


def build_timeline_plan(ai_plan: AIDirectorPlan, *, scene_plan: ScenePlan, total_duration_seconds: float) -> TimelinePlan:
    """Validates and normalizes the AI Director's raw per-scene durations into the
    authoritative TimelinePlan. Never reinterprets the AI's relative pacing
    decisions — only rescales them so the sum matches the real measured narration
    duration exactly, which remains the one invariant nothing may violate."""
    expected_numbers = {scene.scene_number for scene in scene_plan.scenes}
    directions = sorted(ai_plan.scenes, key=lambda direction: direction.scene_number)
    actual_numbers = {direction.scene_number for direction in directions}

    if not directions:
        raise AIDirectorValidationError("AI Director returned no scenes")
    if actual_numbers != expected_numbers:
        raise AIDirectorValidationError(
            f"AI Director scene coverage {sorted(actual_numbers)} does not match ScenePlan {sorted(expected_numbers)}"
        )
    if any(direction.duration_seconds <= 0 for direction in directions):
        raise AIDirectorValidationError("AI Director returned a non-positive scene duration")
    if total_duration_seconds <= 0:
        raise AIDirectorValidationError("No measurable total duration to allocate")

    raw_total = sum(direction.duration_seconds for direction in directions)
    scale = total_duration_seconds / raw_total

    timings: list[SceneTiming] = []
    cursor = 0.0
    for order, direction in enumerate(directions, start=1):
        duration = direction.duration_seconds * scale
        start = cursor
        end = start + duration
        timings.append(
            SceneTiming(
                scene_number=direction.scene_number,
                order=order,
                start_seconds=start,
                end_seconds=end,
                duration_seconds=duration,
                pacing=direction.pacing,
            )
        )
        cursor = end

    return TimelinePlan(
        total_duration_seconds=total_duration_seconds,
        scenes=timings,
        metadata={"status": "success", "source": "ai_director"},
    )


def build_composition_plan(ai_plan: AIDirectorPlan, *, timeline_plan: TimelinePlan, topic: str) -> CompositionPlan:
    """Validates and normalizes the AI Director's per-scene creative direction into
    the authoritative CompositionPlan, carrying each scene's TimelinePlan-sourced
    timing verbatim (never recalculating it) and dropping — never rejecting the
    whole plan for — any relationship/motif that references a scene number outside
    the production. This is the 'validation and normalization layer' role
    CompositionPlanner keeps when the AI Director is the creative authority."""
    valid_scene_numbers = {timing.scene_number for timing in timeline_plan.scenes}

    directions_by_scene = {direction.scene_number: direction for direction in ai_plan.scenes}
    ordered_scene_numbers = sorted(valid_scene_numbers, key=lambda number: timeline_plan.timing_for(number).order)  # type: ignore[union-attr]

    compositions: list[SceneComposition] = []
    for scene_number in ordered_scene_numbers:
        direction = directions_by_scene.get(scene_number)
        timing = timeline_plan.timing_for(scene_number)
        if direction is None or timing is None:
            continue

        relationships = [
            relationship for relationship in direction.relationships if relationship.reference_scene_number in valid_scene_numbers
        ]
        compositions.append(
            SceneComposition(
                scene_number=scene_number,
                timing=timing,
                purpose=direction.purpose,
                composition_style=direction.composition_style,
                camera_intent=direction.camera_intent,
                color_language=direction.color_language,
                relationships=relationships,
                continuity_tags=list(direction.continuity_tags),
                emphasis_note=direction.emphasis_note,
                visual_beats=_normalized_visual_beats(direction.visual_beats),
                retention=direction.retention,
            )
        )

    if not compositions:
        raise AIDirectorValidationError("No scenes could be composed from the AI Director's plan")

    motifs = []
    for motif in ai_plan.motifs[:_MAX_MOTIFS]:
        if motif.established_scene_number not in valid_scene_numbers:
            continue
        recurring = [number for number in motif.recurring_scene_numbers if number in valid_scene_numbers]
        motifs.append(motif.model_copy(update={"recurring_scene_numbers": recurring}))

    return CompositionPlan(
        topic=topic,
        timeline_total_duration_seconds=timeline_plan.total_duration_seconds,
        scenes=compositions,
        motifs=motifs,
        metadata={"status": "success", "source": "ai_director"},
    )


def _normalized_visual_beats(beats: list[VisualBeat]) -> list[VisualBeat]:
    """Drops any beat with an empty description and renumbers the rest 1..N in the
    AI's own order — the same 'drop the invalid piece, never hard-fail the whole
    plan' discipline this module already applies to relationships/motifs."""
    described = [beat for beat in beats if beat.description.strip()]
    return [beat.model_copy(update={"beat_number": index}) for index, beat in enumerate(described, start=1)]


def clamp_visual_beats_per_scene(composition_plan: CompositionPlan, *, maximum_per_scene: int) -> CompositionPlan:
    """Hard per-scene ceiling on visual beats (F28B), mirroring max_scenes_per_video's
    guardrail role for scene count one layer deeper: the AI Director's own beat
    count must never be the thing that decides final image spend. Only ever trims
    (keeps the AI's own first N beats, in its own order) — never pads a scene up
    to the ceiling with invented content."""
    ceiling = max(1, maximum_per_scene)
    scenes = [
        scene.model_copy(update={"visual_beats": scene.visual_beats[:ceiling]})
        if len(scene.visual_beats) > ceiling
        else scene
        for scene in composition_plan.scenes
    ]
    return composition_plan.model_copy(update={"scenes": scenes})


def count_planned_images(composition_plan: CompositionPlan) -> int:
    """Total images the current plan would generate: every scene contributes at
    least one image (the pre-F28B baseline), more when it carries visual beats."""
    return sum(max(1, len(scene.visual_beats)) for scene in composition_plan.scenes)


def enforce_visual_beat_budget(composition_plan: CompositionPlan, *, max_total_images: int) -> CompositionPlan:
    """Cost Validation (F28B): trims visual beats — always from whichever scene
    currently has the most, removing its own last beat first — until the plan's
    total projected image count fits max_total_images. Never removes a scene's
    last beat/image: the 'Scene -> at least one image' backward-compatibility
    guarantee holds regardless of budget pressure."""
    scenes = list(composition_plan.scenes)

    while sum(max(1, len(scene.visual_beats)) for scene in scenes) > max_total_images:
        index = max(
            (i for i, scene in enumerate(scenes) if len(scene.visual_beats) > 1),
            key=lambda i: len(scenes[i].visual_beats),
            default=None,
        )
        if index is None:
            break  # every scene is already at its 1-image floor; can't trim further
        scenes[index] = scenes[index].model_copy(update={"visual_beats": scenes[index].visual_beats[:-1]})

    return composition_plan.model_copy(update={"scenes": scenes})
