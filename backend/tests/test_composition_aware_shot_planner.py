from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.schemas.composition import (
    CameraIntent,
    ColorLanguage,
    CompositionPlan,
    CompositionStyle,
    ContinuityMotif,
    ImportanceLevel,
    SceneComposition,
    SceneRelationship,
    SceneRelationType,
    ScenePurpose,
    SceneRetention,
    TransitionEnergy,
    VisualBeat,
)
from backend.schemas.shots import AtmosphereOverlayType, CameraMovementType, ShotType, TransitionType
from backend.schemas.timeline import ScenePacing, SceneTiming
from backend.services.composition_aware_shot_planner import CompositionAwareShotPlanner


def _timing(scene_number: int, duration: float, pacing: ScenePacing = ScenePacing.STANDARD) -> SceneTiming:
    return SceneTiming(
        scene_number=scene_number,
        order=scene_number,
        start_seconds=0.0,
        end_seconds=duration,
        duration_seconds=duration,
        pacing=pacing,
    )


def _composition(
    scene_number: int,
    *,
    duration: float = 3.0,
    purpose: ScenePurpose = ScenePurpose.DISCOVERY,
    style: CompositionStyle = CompositionStyle.DETAIL_SHOT,
    intent: CameraIntent = CameraIntent.INVESTIGATION,
    color: ColorLanguage = ColorLanguage.NEUTRAL,
    relationships: list[SceneRelationship] | None = None,
    tags: list[str] | None = None,
    visual_beats: list[VisualBeat] | None = None,
    retention: SceneRetention | None = None,
) -> SceneComposition:
    return SceneComposition(
        scene_number=scene_number,
        timing=_timing(scene_number, duration),
        purpose=purpose,
        composition_style=style,
        camera_intent=intent,
        color_language=color,
        relationships=relationships or [],
        continuity_tags=tags or [],
        visual_beats=visual_beats or [],
        retention=retention,
    )


def test_plan_falls_back_when_composition_plan_is_none():
    planner = CompositionAwareShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=3, scene_seconds=3.0, composition_plan=None)

    assert len(shots) == 3
    assert all(shot.duration_seconds == 3.0 for shot in shots)


def test_plan_falls_back_when_composition_plan_scene_count_mismatches_image_count():
    composition_plan = CompositionPlan(
        topic="Test", timeline_total_duration_seconds=6.0, scenes=[_composition(1), _composition(2)]
    )
    planner = CompositionAwareShotPlanner(Settings())
    # image_count (3) does not match composition_plan.scenes (2) — e.g. a scene image failed
    shots = planner.plan(scenes=None, image_count=3, scene_seconds=2.0, composition_plan=composition_plan)

    assert len(shots) == 3
    assert all(shot.duration_seconds == 2.0 for shot in shots)


def test_plan_uses_composition_plans_duration_not_uniform_scene_seconds():
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=10.0,
        scenes=[_composition(1, duration=2.0), _composition(2, duration=8.0)],
    )
    planner = CompositionAwareShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=5.0, composition_plan=composition_plan)

    assert [shot.duration_seconds for shot in shots] == [2.0, 8.0]


def test_plan_maps_composition_style_and_camera_intent_to_shot_fields():
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=3.0,
        scenes=[
            _composition(
                1,
                style=CompositionStyle.REVEAL_SHOT,
                intent=CameraIntent.SLOW_REVEAL,
            )
        ],
    )
    planner = CompositionAwareShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=1, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[0].shot_type == ShotType.CLOSE_UP
    assert shots[0].camera_movement == CameraMovementType.PUSH_IN


def test_plan_uses_fadeblack_transition_when_scene_has_contrast_relationship():
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=6.0,
        scenes=[
            _composition(1),
            _composition(
                2,
                relationships=[
                    SceneRelationship(relation_type=SceneRelationType.CONTRAST, reference_scene_number=1, note="calm after tension")
                ],
            ),
        ],
    )
    settings = Settings(cinematic_transition_style="dissolve")
    planner = CompositionAwareShotPlanner(settings)
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[0].transition == TransitionType.DISSOLVE
    assert shots[1].transition == TransitionType.FADEBLACK


def test_plan_applies_default_atmosphere_only_to_scenes_with_atmosphere_motif():
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=6.0,
        scenes=[_composition(1, tags=["fog"]), _composition(2, tags=[])],
        motifs=[ContinuityMotif(motif_type="atmosphere", description="fog", established_scene_number=1, recurring_scene_numbers=[])],
    )
    settings = Settings(cinematic_default_atmosphere_overlay="light_rays")
    planner = CompositionAwareShotPlanner(settings)
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[0].atmosphere == AtmosphereOverlayType.LIGHT_RAYS
    assert shots[1].atmosphere is None


def test_plan_sets_color_profile_from_color_language():
    composition_plan = CompositionPlan(
        topic="Test", timeline_total_duration_seconds=3.0, scenes=[_composition(1, color=ColorLanguage.TENSION)]
    )
    planner = CompositionAwareShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=1, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[0].color_profile == "tension"


def test_plan_splits_scene_duration_evenly_across_visual_beats():
    beats = [VisualBeat(beat_number=1, description="a"), VisualBeat(beat_number=2, description="b"), VisualBeat(beat_number=3, description="c")]
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=9.0,
        scenes=[_composition(1, duration=9.0, visual_beats=beats)],
    )
    planner = CompositionAwareShotPlanner(Settings())

    shots = planner.plan(scenes=None, image_count=3, scene_seconds=9.0, composition_plan=composition_plan)

    assert len(shots) == 3
    assert all(shot.scene_number == 1 for shot in shots)
    assert all(shot.duration_seconds == pytest.approx(3.0) for shot in shots)
    assert sum(shot.duration_seconds for shot in shots) == pytest.approx(9.0)


def test_plan_expected_image_count_accounts_for_visual_beats_across_scenes():
    beats = [VisualBeat(beat_number=1, description="a"), VisualBeat(beat_number=2, description="b")]
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=5.0,
        scenes=[_composition(1, duration=2.0, visual_beats=beats), _composition(2, duration=3.0)],
    )
    planner = CompositionAwareShotPlanner(Settings())

    # 2 beats (scene 1) + 1 implicit beat (scene 2) == 3 images total.
    shots = planner.plan(scenes=None, image_count=3, scene_seconds=5.0, composition_plan=composition_plan)

    assert [shot.scene_number for shot in shots] == [1, 1, 2]
    assert shots[0].duration_seconds == pytest.approx(1.0)
    assert shots[1].duration_seconds == pytest.approx(1.0)
    assert shots[2].duration_seconds == pytest.approx(3.0)


def test_plan_falls_back_when_expected_image_count_from_beats_mismatches():
    beats = [VisualBeat(beat_number=1, description="a"), VisualBeat(beat_number=2, description="b")]
    composition_plan = CompositionPlan(
        topic="Test", timeline_total_duration_seconds=2.0, scenes=[_composition(1, duration=2.0, visual_beats=beats)]
    )
    planner = CompositionAwareShotPlanner(Settings())

    # Plan expects 2 images (one scene, 2 beats) but only 1 image actually exists
    # (e.g. one beat's generation failed) — must fall back rather than mis-assign.
    shots = planner.plan(scenes=None, image_count=1, scene_seconds=2.0, composition_plan=composition_plan)

    assert len(shots) == 1
    assert shots[0].duration_seconds == 2.0


def test_plan_splits_scene_duration_by_beat_importance():
    # F29: a 40s scene with weights low(3)/normal(4)/critical(7)/high(6) -> 6/8/14/12,
    # the architecture spec's own worked example.
    beats = [
        VisualBeat(beat_number=1, description="a", beat_importance=ImportanceLevel.LOW),
        VisualBeat(beat_number=2, description="b", beat_importance=ImportanceLevel.NORMAL),
        VisualBeat(beat_number=3, description="c", beat_importance=ImportanceLevel.CRITICAL),
        VisualBeat(beat_number=4, description="d", beat_importance=ImportanceLevel.HIGH),
    ]
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=40.0,
        scenes=[_composition(1, duration=40.0, visual_beats=beats)],
    )
    planner = CompositionAwareShotPlanner(Settings())

    shots = planner.plan(scenes=None, image_count=4, scene_seconds=40.0, composition_plan=composition_plan)

    assert [shot.duration_seconds for shot in shots] == [pytest.approx(6.0), pytest.approx(8.0), pytest.approx(14.0), pytest.approx(12.0)]
    assert sum(shot.duration_seconds for shot in shots) == pytest.approx(40.0)


def test_plan_beat_importance_never_produces_zero_duration():
    beats = [
        VisualBeat(beat_number=1, description="a", beat_importance=ImportanceLevel.LOW),
        VisualBeat(beat_number=2, description="b", beat_importance=ImportanceLevel.CRITICAL),
    ]
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=1.0,
        scenes=[_composition(1, duration=1.0, visual_beats=beats)],
    )
    planner = CompositionAwareShotPlanner(Settings())

    shots = planner.plan(scenes=None, image_count=2, scene_seconds=1.0, composition_plan=composition_plan)

    assert all(shot.duration_seconds > 0 for shot in shots)
    assert sum(shot.duration_seconds for shot in shots) == pytest.approx(1.0)


def test_plan_uses_transition_energy_from_retention_when_present():
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=6.0,
        scenes=[
            _composition(1),
            _composition(
                2,
                retention=SceneRetention(transition_energy=TransitionEnergy.DRAMATIC),
                relationships=[],
            ),
        ],
    )
    settings = Settings(cinematic_transition_style="dissolve")
    planner = CompositionAwareShotPlanner(settings)
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[0].transition == TransitionType.DISSOLVE
    assert shots[1].transition == TransitionType.FADEBLACK


def test_plan_retention_transition_energy_overrides_contrast_heuristic():
    # transition_energy is more authoritative guidance than the older
    # contrast-relationship heuristic when both are present.
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=6.0,
        scenes=[
            _composition(1),
            _composition(
                2,
                retention=SceneRetention(transition_energy=TransitionEnergy.CALM),
                relationships=[
                    SceneRelationship(relation_type=SceneRelationType.CONTRAST, reference_scene_number=1, note="calm after tension")
                ],
            ),
        ],
    )
    planner = CompositionAwareShotPlanner(Settings())
    shots = planner.plan(scenes=None, image_count=2, scene_seconds=3.0, composition_plan=composition_plan)

    assert shots[1].transition == TransitionType.DISSOLVE
