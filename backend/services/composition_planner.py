from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import defaultdict

from backend.schemas.assets import Scene, ScenePlan
from backend.schemas.composition import (
    CameraIntent,
    ColorLanguage,
    CompositionPlan,
    CompositionStyle,
    ContinuityMotif,
    SceneComposition,
    SceneRelationship,
    SceneRelationType,
    ScenePurpose,
)
from backend.schemas.timeline import ScenePacing, TimelinePlan

# Bounded so motif detection never grows unbounded on a long script — five
# recurring threads is already more than enough visual continuity for an
# 8-scene video, and keeps the deterministic pass cheap and predictable.
_MAX_MOTIFS = 5

_STOPWORDS = frozenset(
    {
        "about", "above", "after", "again", "against", "around", "before", "below",
        "between", "camera", "during", "every", "field", "frame", "from", "having",
        "inside", "into", "medium", "moment", "narration", "near", "outside", "over",
        "scene", "shows", "slowly", "story", "subject", "their", "there", "these",
        "they", "this", "those", "through", "toward", "under", "using", "which",
        "while", "with", "within",
    }
)

_ATMOSPHERE_WORDS = frozenset({"fog", "mist", "haze", "dust", "smoke", "grain", "shadow", "shadows", "glow"})

_PURPOSE_BY_PACING: dict[ScenePacing, ScenePurpose] = {
    ScenePacing.FAST: ScenePurpose.CONTEXT,
    ScenePacing.STANDARD: ScenePurpose.DISCOVERY,
    ScenePacing.SLOW: ScenePurpose.CONFLICT,
    ScenePacing.DRAMATIC_PAUSE: ScenePurpose.ESCALATION,
    ScenePacing.CLIMAX: ScenePurpose.REVEAL,
    ScenePacing.BREATHING: ScenePurpose.RESOLUTION,
}

_STYLE_AND_INTENT_BY_PURPOSE: dict[ScenePurpose, tuple[CompositionStyle, CameraIntent]] = {
    ScenePurpose.INTRODUCTION: (CompositionStyle.ESTABLISHING_SHOT, CameraIntent.NEUTRAL_OBSERVATION),
    ScenePurpose.CONTEXT: (CompositionStyle.WIDE_SHOT, CameraIntent.INVESTIGATION),
    ScenePurpose.DISCOVERY: (CompositionStyle.DETAIL_SHOT, CameraIntent.INVESTIGATION),
    ScenePurpose.CONFLICT: (CompositionStyle.CLOSE_UP, CameraIntent.SUSPENSE),
    ScenePurpose.ESCALATION: (CompositionStyle.REACTION_SHOT, CameraIntent.SUSPENSE),
    ScenePurpose.REVEAL: (CompositionStyle.REVEAL_SHOT, CameraIntent.SLOW_REVEAL),
    ScenePurpose.RESOLUTION: (CompositionStyle.WIDE_SHOT, CameraIntent.EMOTIONAL_FOCUS),
}

_COLOR_BY_PURPOSE: dict[ScenePurpose, ColorLanguage] = {
    ScenePurpose.INTRODUCTION: ColorLanguage.NEUTRAL,
    ScenePurpose.CONTEXT: ColorLanguage.COLD_PROGRESSION,
    ScenePurpose.DISCOVERY: ColorLanguage.COLD_PROGRESSION,
    ScenePurpose.CONFLICT: ColorLanguage.TENSION,
    ScenePurpose.ESCALATION: ColorLanguage.TENSION,
    ScenePurpose.REVEAL: ColorLanguage.TENSION,
    ScenePurpose.RESOLUTION: ColorLanguage.WARM_PROGRESSION,
}

_WORD_PATTERN = re.compile(r"[a-zA-Z]{5,}")


def _significant_words(text: str) -> set[str]:
    return {word for word in _WORD_PATTERN.findall(text.lower()) if word not in _STOPWORDS}


def _detect_motifs(scenes: list[Scene]) -> tuple[list[ContinuityMotif], dict[int, list[str]]]:
    """Keyword-repetition heuristic: any significant word appearing in 2+ scenes
    becomes a recurring motif. Deterministic, bounded, zero added cost — the same
    discipline DeterministicShotPlanner already applies to camera-movement
    keyword matching, just applied across scenes instead of within one."""
    first_seen: dict[str, int] = {}
    occurrences: dict[str, list[int]] = defaultdict(list)
    word_source: dict[str, str] = {}

    for scene in scenes:
        location_words = _significant_words(scene.environment)
        atmosphere_words = _significant_words(f"{scene.lighting} {scene.environment}") & _ATMOSPHERE_WORDS
        object_words = _significant_words(f"{scene.narration} {scene.composition}") - location_words

        for word, source in [
            *((w, "atmosphere") for w in atmosphere_words),
            *((w, "location") for w in location_words),
            *((w, "object") for w in object_words),
        ]:
            word_source.setdefault(word, source)
            occurrences[word].append(scene.scene_number)
            first_seen.setdefault(word, scene.scene_number)

    recurring_words = sorted(
        (word for word, occ in occurrences.items() if len(set(occ)) >= 2),
        key=lambda word: (first_seen[word], word),
    )[:_MAX_MOTIFS]

    motifs: list[ContinuityMotif] = []
    tags_by_scene: dict[int, list[str]] = defaultdict(list)
    for word in recurring_words:
        established = first_seen[word]
        recurring = sorted({scene_number for scene_number in occurrences[word] if scene_number != established})
        motifs.append(
            ContinuityMotif(
                motif_type=word_source[word],  # type: ignore[arg-type]
                description=word,
                established_scene_number=established,
                recurring_scene_numbers=recurring,
            )
        )
        for scene_number in [established, *recurring]:
            tags_by_scene[scene_number].append(word)

    return motifs, tags_by_scene


def _relationships_for(
    *,
    scene_number: int,
    purpose: ScenePurpose,
    tags: list[str],
    motifs_by_word: dict[str, ContinuityMotif],
    previous_scene_number: int | None,
    previous_purpose: ScenePurpose | None,
) -> list[SceneRelationship]:
    relationships: list[SceneRelationship] = []

    for word in tags:
        motif = motifs_by_word[word]
        if motif.established_scene_number != scene_number:
            relationships.append(
                SceneRelationship(
                    relation_type=SceneRelationType.CALLBACK,
                    reference_scene_number=motif.established_scene_number,
                    note=f"recurring {motif.motif_type}: {motif.description}",
                )
            )

    if previous_scene_number is not None and previous_purpose is not None:
        if previous_purpose == purpose:
            relationships.append(
                SceneRelationship(
                    relation_type=SceneRelationType.CONTINUATION,
                    reference_scene_number=previous_scene_number,
                    note="same narrative purpose as the previous scene",
                )
            )
        elif previous_purpose in (ScenePurpose.CONFLICT, ScenePurpose.ESCALATION) and purpose == ScenePurpose.RESOLUTION:
            relationships.append(
                SceneRelationship(
                    relation_type=SceneRelationType.CONTRAST,
                    reference_scene_number=previous_scene_number,
                    note="tension resolving into calm",
                )
            )
        elif previous_purpose == ScenePurpose.CONFLICT and purpose == ScenePurpose.ESCALATION:
            relationships.append(
                SceneRelationship(
                    relation_type=SceneRelationType.ESCALATION,
                    reference_scene_number=previous_scene_number,
                    note="conflict intensifies",
                )
            )

    return relationships


class CompositionPlanner(ABC):
    """Resolves a ScenePlan + TimelinePlan into a CompositionPlan — the single
    seam between scene planning and Shot/prompt production. Never calculates
    timing itself; every SceneComposition.timing value is carried verbatim from
    the TimelinePlan it's given. F28 (AI Director) is expected to add an
    LLM-driven implementation later; downstream consumers only ever read
    CompositionPlan, so they need no changes when that happens."""

    @abstractmethod
    def plan(self, *, scene_plan: ScenePlan, timeline_plan: TimelinePlan) -> CompositionPlan: ...


class DeterministicCompositionPlanner(CompositionPlanner):
    """F27 implementation: assigns purpose/style/camera-intent/color from each
    scene's TimelinePlan-provided pacing and position (no LLM call), and detects
    continuity motifs/relationships via keyword repetition across scenes. Zero
    added cost — pure Python over data already produced upstream."""

    def plan(self, *, scene_plan: ScenePlan, timeline_plan: TimelinePlan) -> CompositionPlan:
        timed_scenes = [scene for scene in scene_plan.scenes if timeline_plan.timing_for(scene.scene_number) is not None]

        if not timed_scenes:
            return CompositionPlan(
                topic=scene_plan.topic,
                timeline_total_duration_seconds=timeline_plan.total_duration_seconds,
                scenes=[],
                motifs=[],
                metadata={"status": "skipped", "reason": "TimelinePlan has no timing for any planned scene"},
            )

        timed_scenes = sorted(timed_scenes, key=lambda scene: timeline_plan.timing_for(scene.scene_number).order)  # type: ignore[union-attr]
        motifs, tags_by_scene = _detect_motifs(timed_scenes)
        motifs_by_word = {motif.description: motif for motif in motifs}

        compositions: list[SceneComposition] = []
        previous_scene_number: int | None = None
        previous_purpose: ScenePurpose | None = None

        for scene in timed_scenes:
            timing = timeline_plan.timing_for(scene.scene_number)
            assert timing is not None  # filtered above

            purpose = ScenePurpose.INTRODUCTION if timing.order == 1 else _PURPOSE_BY_PACING[timing.pacing]
            composition_style, camera_intent = _STYLE_AND_INTENT_BY_PURPOSE[purpose]
            color_language = _COLOR_BY_PURPOSE[purpose]
            tags = tags_by_scene.get(scene.scene_number, [])
            relationships = _relationships_for(
                scene_number=scene.scene_number,
                purpose=purpose,
                tags=tags,
                motifs_by_word=motifs_by_word,
                previous_scene_number=previous_scene_number,
                previous_purpose=previous_purpose,
            )

            compositions.append(
                SceneComposition(
                    scene_number=scene.scene_number,
                    timing=timing,
                    purpose=purpose,
                    composition_style=composition_style,
                    camera_intent=camera_intent,
                    color_language=color_language,
                    relationships=relationships,
                    continuity_tags=tags,
                    emphasis_note=f"{purpose.value} ({timing.pacing.value} pacing)",
                )
            )
            previous_scene_number = scene.scene_number
            previous_purpose = purpose

        return CompositionPlan(
            topic=scene_plan.topic,
            timeline_total_duration_seconds=timeline_plan.total_duration_seconds,
            scenes=compositions,
            motifs=motifs,
            metadata={"status": "success"},
        )
