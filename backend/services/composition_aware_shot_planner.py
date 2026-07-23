from __future__ import annotations

from backend.core.config import Settings
from backend.schemas.assets import Scene
from backend.schemas.composition import (
    CameraIntent,
    CompositionPlan,
    CompositionStyle,
    ImportanceLevel,
    SceneComposition,
    SceneRelationType,
    TransitionEnergy,
)
from backend.schemas.shots import AtmosphereOverlayType, CameraMovementType, Shot, ShotType, TransitionType
from backend.services.cinematic_shot_planner import DeterministicShotPlanner, ShotPlanner

# F29 Beat Duration Optimization: replaces F28B's equal split. Weights are
# relative, not absolute — only their ratio matters. Chosen to reproduce the
# architecture spec's own worked example (40s scene, beats weighted
# low/normal/critical/high -> 6/8/14/12s), and because every weight is a
# strictly positive number, a beat can never be allocated zero duration
# regardless of the importance mix in a scene.
_BEAT_IMPORTANCE_WEIGHT: dict[ImportanceLevel, float] = {
    ImportanceLevel.LOW: 3.0,
    ImportanceLevel.NORMAL: 4.0,
    ImportanceLevel.HIGH: 6.0,
    ImportanceLevel.CRITICAL: 7.0,
}

# F29 Transition Intelligence: retention-authored transition_energy is planning
# metadata only — RendererPipeline still only ever executes Shot.transition,
# which stays exactly the two F25 TransitionType values. Softer feels keep the
# existing DISSOLVE default; higher-energy/suspense feels use the harder cut.
_TRANSITION_BY_ENERGY: dict[TransitionEnergy, TransitionType] = {
    TransitionEnergy.SEAMLESS: TransitionType.DISSOLVE,
    TransitionEnergy.CALM: TransitionType.DISSOLVE,
    TransitionEnergy.EMOTIONAL: TransitionType.DISSOLVE,
    TransitionEnergy.ENERGETIC: TransitionType.FADEBLACK,
    TransitionEnergy.SUSPENSE: TransitionType.FADEBLACK,
    TransitionEnergy.DRAMATIC: TransitionType.FADEBLACK,
}

_SHOT_TYPE_BY_STYLE: dict[CompositionStyle, ShotType] = {
    CompositionStyle.ESTABLISHING_SHOT: ShotType.ESTABLISHING,
    CompositionStyle.WIDE_SHOT: ShotType.WIDE,
    CompositionStyle.CLOSE_UP: ShotType.CLOSE_UP,
    CompositionStyle.DETAIL_SHOT: ShotType.INSERT,
    CompositionStyle.REVEAL_SHOT: ShotType.CLOSE_UP,
    CompositionStyle.COMPARISON_SHOT: ShotType.WIDE,
    CompositionStyle.REACTION_SHOT: ShotType.CLOSE_UP,
    CompositionStyle.TRANSITION_SHOT: ShotType.MEDIUM,
}

_MOVEMENT_BY_INTENT: dict[CameraIntent, CameraMovementType] = {
    CameraIntent.SLOW_REVEAL: CameraMovementType.PUSH_IN,
    CameraIntent.DRAMATIC_ZOOM: CameraMovementType.CINEMATIC_ZOOM,
    CameraIntent.INVESTIGATION: CameraMovementType.PAN_LEFT,
    CameraIntent.SUSPENSE: CameraMovementType.HANDHELD,
    CameraIntent.EMOTIONAL_FOCUS: CameraMovementType.PULL_OUT,
    CameraIntent.NEUTRAL_OBSERVATION: CameraMovementType.TILT_UP,
}


def _expected_image_count(composition_plan: CompositionPlan) -> int:
    """Every scene contributes at least one image; more when it carries F28B
    visual beats. Must match SceneImageGenerationService's actual output count
    exactly for this planner to stay in play — see plan() below."""
    return sum(max(1, len(scene.visual_beats)) for scene in composition_plan.scenes)


class CompositionAwareShotPlanner(ShotPlanner):
    """F27 implementation: derives each Shot entirely from a CompositionPlan
    (which already carries TimelinePlan-sourced duration via SceneComposition.timing)
    instead of keyword-matching Scene text or rotating blindly. Falls back to
    DeterministicShotPlanner's behavior whenever composition_plan is absent, or
    when its expected image count doesn't match the images actually being
    rendered (e.g. some scene images failed generation after CompositionPlan was
    built) — the same automatic-fallback discipline as cinematic rendering
    falling back to the legacy slideshow, guaranteeing video timing never
    disagrees with the real narration length it must fit.

    F28B: a scene with visual_beats emits one Shot per beat instead of one Shot
    for the whole scene, dividing the scene's TimelinePlan-fixed duration across
    its beats — the scene's total screen time is unchanged, only how many images
    it's divided across. A scene with no visual_beats emits exactly the one Shot
    it always did, identical to pre-F28B output.

    F29: that division is now importance-weighted (see _BEAT_IMPORTANCE_WEIGHT)
    instead of equal — a CRITICAL beat is held longer than a LOW one. A scene
    where every beat is NORMAL (including every pre-F29 plan, since
    VisualBeat.beat_importance defaults to NORMAL) still splits evenly, so this
    is a pure extension with no behavior change for existing plans. Transition
    selection also becomes retention-aware via SceneComposition.retention."""

    def __init__(self, settings: Settings, fallback: ShotPlanner | None = None) -> None:
        self._settings = settings
        self._fallback = fallback or DeterministicShotPlanner(settings)

    def plan(
        self,
        *,
        scenes: list[Scene] | None,
        image_count: int,
        scene_seconds: float,
        composition_plan: CompositionPlan | None = None,
    ) -> list[Shot]:
        if composition_plan is None or _expected_image_count(composition_plan) != image_count:
            return self._fallback.plan(scenes=scenes, image_count=image_count, scene_seconds=scene_seconds)

        transition = TransitionType(self._settings.cinematic_transition_style)
        default_atmosphere = (
            AtmosphereOverlayType(self._settings.cinematic_default_atmosphere_overlay)
            if self._settings.cinematic_default_atmosphere_overlay
            else None
        )
        atmosphere_words = {motif.description for motif in composition_plan.motifs if motif.motif_type == "atmosphere"}

        shots: list[Shot] = []
        for composition in composition_plan.scenes:
            beat_durations = self._beat_durations(composition)
            for position, duration in enumerate(beat_durations):
                shots.append(
                    Shot(
                        scene_number=composition.scene_number,
                        shot_type=_SHOT_TYPE_BY_STYLE.get(composition.composition_style, ShotType.MEDIUM),
                        camera_movement=_MOVEMENT_BY_INTENT.get(composition.camera_intent, CameraMovementType.PUSH_IN),
                        transition=(
                            self._transition_for(composition, transition) if position == 0 else TransitionType.DISSOLVE
                        ),
                        duration_seconds=duration,
                        atmosphere=self._atmosphere_for(composition, default_atmosphere, atmosphere_words),
                        color_profile=composition.color_language.value,
                    )
                )
        return shots

    def _beat_durations(self, composition: SceneComposition) -> list[float]:
        """F29 Beat Duration Optimization: distributes the scene's fixed total
        duration across its beats in proportion to each beat's beat_importance,
        instead of F28B's equal split. Weights are always strictly positive, so
        no beat can ever receive zero duration, and the result always sums back
        to the scene's exact TimelinePlan-sourced duration."""
        beats = composition.visual_beats
        total_duration = composition.timing.duration_seconds
        if not beats:
            return [total_duration]

        weights = [_BEAT_IMPORTANCE_WEIGHT[beat.beat_importance] for beat in beats]
        weight_sum = sum(weights)
        return [total_duration * weight / weight_sum for weight in weights]

    def _transition_for(self, composition: SceneComposition, default: TransitionType) -> TransitionType:
        if composition.retention is not None:
            return _TRANSITION_BY_ENERGY.get(composition.retention.transition_energy, default)
        if any(relationship.relation_type == SceneRelationType.CONTRAST for relationship in composition.relationships):
            return TransitionType.FADEBLACK
        return default

    def _atmosphere_for(
        self,
        composition: SceneComposition,
        default: AtmosphereOverlayType | None,
        atmosphere_words: set[str],
    ) -> AtmosphereOverlayType | None:
        has_atmosphere_motif = any(tag in atmosphere_words for tag in composition.continuity_tags)
        return default if has_atmosphere_motif else None
