from __future__ import annotations

import re
from abc import ABC, abstractmethod

from backend.core.config import Settings
from backend.schemas.assets import Scene
from backend.schemas.composition import CompositionPlan
from backend.schemas.shots import AtmosphereOverlayType, CameraMovementType, Shot, ShotType, TransitionType

# Ordered so more specific phrases are checked before the generic ones they'd otherwise
# be swallowed by (e.g. "zoom(s/ing) out" must be checked before the bare "zoom" fallback).
# Patterns use \w* / [a-z]* stems so verb conjugations in LLM-authored prose ("zooms out",
# "pushing in", "panning left") still match, not just the bare infinitive.
_MOVEMENT_KEYWORDS: list[tuple[re.Pattern[str], CameraMovementType]] = [
    (re.compile(r"zoom[a-z]*\s+out"), CameraMovementType.PULL_OUT),
    (re.compile(r"pull[a-z]*\s+(out|back)"), CameraMovementType.PULL_OUT),
    (re.compile(r"push[a-z]*[\s-]+in"), CameraMovementType.PUSH_IN),
    (re.compile(r"pan[a-z]*\s+left"), CameraMovementType.PAN_LEFT),
    (re.compile(r"pan[a-z]*\s+right"), CameraMovementType.PAN_RIGHT),
    (re.compile(r"tilt[a-z]*\s+up"), CameraMovementType.TILT_UP),
    (re.compile(r"tilt[a-z]*\s+down"), CameraMovementType.TILT_DOWN),
    (re.compile(r"hand-?held"), CameraMovementType.HANDHELD),
    (re.compile(r"shaky"), CameraMovementType.HANDHELD),
    (re.compile(r"cinematic\s+zoom"), CameraMovementType.CINEMATIC_ZOOM),
    (re.compile(r"push"), CameraMovementType.PUSH_IN),
    (re.compile(r"zoom"), CameraMovementType.CINEMATIC_ZOOM),
]

_SHOT_TYPE_KEYWORDS: list[tuple[str, ShotType]] = [
    ("establishing", ShotType.ESTABLISHING),
    ("close-up", ShotType.CLOSE_UP),
    ("close up", ShotType.CLOSE_UP),
    ("closeup", ShotType.CLOSE_UP),
    ("insert", ShotType.INSERT),
    ("wide", ShotType.WIDE),
    ("medium", ShotType.MEDIUM),
]

# Deterministic fallback rotation used whenever a scene's free-text camera/animation notes
# don't match a keyword above, so movement still varies across a video without any LLM call.
_MOVEMENT_ROTATION: list[CameraMovementType] = [
    CameraMovementType.PUSH_IN,
    CameraMovementType.PAN_LEFT,
    CameraMovementType.PAN_RIGHT,
    CameraMovementType.TILT_UP,
    CameraMovementType.TILT_DOWN,
    CameraMovementType.PULL_OUT,
    CameraMovementType.HANDHELD,
    CameraMovementType.CINEMATIC_ZOOM,
]

_SHOT_TYPE_ROTATION: list[ShotType] = [
    ShotType.WIDE,
    ShotType.MEDIUM,
    ShotType.CLOSE_UP,
    ShotType.ESTABLISHING,
    ShotType.INSERT,
]


def _match_pattern(text: str, table: list[tuple[re.Pattern[str], object]]) -> object | None:
    lowered = text.lower()
    for pattern, value in table:
        if pattern.search(lowered):
            return value
    return None


def _match_phrase(text: str, table: list[tuple[str, object]]) -> object | None:
    lowered = text.lower()
    for phrase, value in table:
        if phrase in lowered:
            return value
    return None


class ShotPlanner(ABC):
    """Resolves each scene to a Shot — the single seam between planning ('what should this
    scene look like') and rendering ('how do we render that'). F28 (AI Director) is
    expected to add an LLM-driven implementation of this interface later; RendererPipeline
    only ever executes Shots, so it needs no changes when that happens."""

    @abstractmethod
    def plan(
        self,
        *,
        scenes: list[Scene] | None,
        image_count: int,
        scene_seconds: float,
        composition_plan: CompositionPlan | None = None,
    ) -> list[Shot]:
        """Returns exactly `image_count` Shots, ordered by scene_number starting at 1.

        `composition_plan` is additive (F27): implementations that don't use
        CompositionPlan (this one) simply ignore it, preserving backward
        compatibility for every existing caller/test."""


class DeterministicShotPlanner(ShotPlanner):
    """F25 implementation: keyword-matches each Scene's free-text `camera`/`animation`
    notes where available, falling back to a deterministic round-robin over the supported
    movement/shot-type sets so every video still gets varied shots without a text match.
    Transition/atmosphere/color_profile are uniform across the video, read from Settings.
    No LLM calls — zero added cost."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(
        self,
        *,
        scenes: list[Scene] | None,
        image_count: int,
        scene_seconds: float,
        composition_plan: CompositionPlan | None = None,
    ) -> list[Shot]:
        transition = TransitionType(self._settings.cinematic_transition_style)
        atmosphere = (
            AtmosphereOverlayType(self._settings.cinematic_default_atmosphere_overlay)
            if self._settings.cinematic_default_atmosphere_overlay
            else None
        )
        scenes_by_number = {scene.scene_number: scene for scene in (scenes or [])}

        shots: list[Shot] = []
        for index in range(image_count):
            scene_number = index + 1
            scene = scenes_by_number.get(scene_number)
            combined_text = f"{scene.camera} {scene.animation}" if scene else ""
            composition_text = f"{combined_text} {scene.composition}" if scene else ""

            movement = _match_pattern(combined_text, _MOVEMENT_KEYWORDS)
            if movement is None:
                movement = _MOVEMENT_ROTATION[index % len(_MOVEMENT_ROTATION)]

            shot_type = _match_phrase(composition_text, _SHOT_TYPE_KEYWORDS)
            if shot_type is None:
                shot_type = _SHOT_TYPE_ROTATION[index % len(_SHOT_TYPE_ROTATION)]

            shots.append(
                Shot(
                    scene_number=scene_number,
                    shot_type=shot_type,
                    camera_movement=movement,
                    transition=transition,
                    duration_seconds=scene_seconds,
                    atmosphere=atmosphere,
                    color_profile=None,
                )
            )
        return shots
