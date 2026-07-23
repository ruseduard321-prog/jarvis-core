from __future__ import annotations

import pytest

from backend.schemas.ai_director import AIDirectorPlan, AIDirectorSceneDirection
from backend.schemas.assets import Scene, ScenePlan
from backend.schemas.composition import (
    CameraIntent,
    CompositionPlan,
    CompositionStyle,
    ContinuityMotif,
    ImportanceLevel,
    SceneComposition,
    SceneRelationship,
    SceneRelationType,
    ScenePurpose,
    SceneRetention,
    VisualBeat,
)
from backend.schemas.timeline import ScenePacing, SceneTiming
from backend.services.ai_director_plan_builder import (
    build_composition_plan,
    build_timeline_plan,
    clamp_visual_beats_per_scene,
    count_planned_images,
    enforce_visual_beat_budget,
)
from backend.services.ai_director_provider import AIDirectorValidationError


def _direction(
    scene_number: int,
    duration: float = 1.0,
    *,
    purpose: ScenePurpose = ScenePurpose.DISCOVERY,
    relationships: list[SceneRelationship] | None = None,
    visual_beats: list[VisualBeat] | None = None,
    retention: SceneRetention | None = None,
) -> AIDirectorSceneDirection:
    return AIDirectorSceneDirection(
        scene_number=scene_number,
        duration_seconds=duration,
        pacing=ScenePacing.STANDARD,
        purpose=purpose,
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
        relationships=relationships or [],
        visual_beats=visual_beats or [],
        retention=retention,
    )


def _composition(scene_number: int, beat_count: int) -> SceneComposition:
    return SceneComposition(
        scene_number=scene_number,
        timing=SceneTiming(
            scene_number=scene_number, order=scene_number, start_seconds=0.0, end_seconds=1.0, duration_seconds=1.0
        ),
        purpose=ScenePurpose.DISCOVERY,
        composition_style=CompositionStyle.WIDE_SHOT,
        camera_intent=CameraIntent.NEUTRAL_OBSERVATION,
        visual_beats=[VisualBeat(beat_number=i, description=f"beat {i}") for i in range(1, beat_count + 1)],
    )


def _scene_plan(count: int) -> ScenePlan:
    return ScenePlan(topic="Test", scenes=[Scene(scene_number=i) for i in range(1, count + 1)])


def test_build_timeline_plan_rescales_durations_to_exact_total():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0), _direction(2, 3.0)])
    scene_plan = _scene_plan(2)

    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=40.0)

    assert timeline_plan.total_duration_seconds == 40.0
    assert sum(scene.duration_seconds for scene in timeline_plan.scenes) == pytest.approx(40.0)
    # AI's relative 1:3 proportion must be preserved after rescaling.
    assert timeline_plan.scenes[1].duration_seconds == pytest.approx(timeline_plan.scenes[0].duration_seconds * 3)


def test_build_timeline_plan_assigns_contiguous_start_end_in_scene_number_order():
    ai_plan = AIDirectorPlan(scenes=[_direction(2, 1.0), _direction(1, 1.0)])
    scene_plan = _scene_plan(2)

    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=20.0)

    assert [scene.scene_number for scene in timeline_plan.scenes] == [1, 2]
    assert timeline_plan.scenes[0].order == 1
    assert timeline_plan.scenes[1].start_seconds == pytest.approx(timeline_plan.scenes[0].end_seconds)


def test_build_timeline_plan_raises_when_scene_coverage_mismatches():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0)])
    scene_plan = _scene_plan(2)

    with pytest.raises(AIDirectorValidationError):
        build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=20.0)


def test_build_timeline_plan_raises_on_duplicate_scene_number():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0), _direction(1, 2.0)])
    scene_plan = _scene_plan(2)

    with pytest.raises(AIDirectorValidationError):
        build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=20.0)


def test_build_timeline_plan_raises_on_non_positive_duration():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 0.0), _direction(2, 1.0)])
    scene_plan = _scene_plan(2)

    with pytest.raises(AIDirectorValidationError):
        build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=20.0)


def test_build_timeline_plan_raises_on_empty_scenes():
    ai_plan = AIDirectorPlan(scenes=[])
    scene_plan = _scene_plan(0)

    with pytest.raises(AIDirectorValidationError):
        build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=20.0)


def test_build_timeline_plan_raises_on_zero_total_duration():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0)])
    scene_plan = _scene_plan(1)

    with pytest.raises(AIDirectorValidationError):
        build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=0.0)


def test_build_composition_plan_carries_timing_verbatim_from_timeline_plan():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0), _direction(2, 1.0)])
    scene_plan = _scene_plan(2)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    for composition in composition_plan.scenes:
        assert composition.timing == timeline_plan.timing_for(composition.scene_number)
    assert composition_plan.metadata["source"] == "ai_director"


def test_build_composition_plan_drops_relationship_referencing_unknown_scene():
    bad_relationship = SceneRelationship(
        relation_type=SceneRelationType.CALLBACK, reference_scene_number=99, note="invalid"
    )
    ai_plan = AIDirectorPlan(
        scenes=[_direction(1, 1.0), _direction(2, 1.0, relationships=[bad_relationship])]
    )
    scene_plan = _scene_plan(2)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    scene_two = next(scene for scene in composition_plan.scenes if scene.scene_number == 2)
    assert scene_two.relationships == []


def test_build_composition_plan_keeps_relationship_referencing_valid_scene():
    good_relationship = SceneRelationship(
        relation_type=SceneRelationType.CALLBACK, reference_scene_number=1, note="valid"
    )
    ai_plan = AIDirectorPlan(
        scenes=[_direction(1, 1.0), _direction(2, 1.0, relationships=[good_relationship])]
    )
    scene_plan = _scene_plan(2)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    scene_two = next(scene for scene in composition_plan.scenes if scene.scene_number == 2)
    assert len(scene_two.relationships) == 1


def test_build_composition_plan_filters_motif_referencing_unknown_scene():
    ai_plan = AIDirectorPlan(
        scenes=[_direction(1, 1.0), _direction(2, 1.0)],
        motifs=[
            ContinuityMotif(motif_type="object", description="lantern", established_scene_number=1, recurring_scene_numbers=[2, 99]),
            ContinuityMotif(motif_type="location", description="cave", established_scene_number=99, recurring_scene_numbers=[]),
        ],
    )
    scene_plan = _scene_plan(2)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    assert len(composition_plan.motifs) == 1
    assert composition_plan.motifs[0].description == "lantern"
    assert composition_plan.motifs[0].recurring_scene_numbers == [2]


def test_build_composition_plan_carries_visual_beats_and_renumbers_them():
    beats = [VisualBeat(beat_number=5, description="the ship leaves the dock"), VisualBeat(beat_number=9, description="crowd waves goodbye")]
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0, visual_beats=beats)])
    scene_plan = _scene_plan(1)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    scene_one = composition_plan.scenes[0]
    assert [beat.beat_number for beat in scene_one.visual_beats] == [1, 2]
    assert scene_one.visual_beats[0].description == "the ship leaves the dock"


def test_build_composition_plan_drops_visual_beats_with_empty_description():
    beats = [VisualBeat(beat_number=1, description="   "), VisualBeat(beat_number=2, description="a real beat")]
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0, visual_beats=beats)])
    scene_plan = _scene_plan(1)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    scene_one = composition_plan.scenes[0]
    assert len(scene_one.visual_beats) == 1
    assert scene_one.visual_beats[0].beat_number == 1
    assert scene_one.visual_beats[0].description == "a real beat"


def test_build_composition_plan_defaults_to_no_visual_beats():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0)])
    scene_plan = _scene_plan(1)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    assert composition_plan.scenes[0].visual_beats == []


def test_build_composition_plan_carries_retention_through_verbatim():
    retention = SceneRetention(retention_priority=ImportanceLevel.CRITICAL, curiosity_level=0.9)
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0, retention=retention)])
    scene_plan = _scene_plan(1)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    assert composition_plan.scenes[0].retention == retention


def test_build_composition_plan_defaults_to_no_retention():
    ai_plan = AIDirectorPlan(scenes=[_direction(1, 1.0)])
    scene_plan = _scene_plan(1)
    timeline_plan = build_timeline_plan(ai_plan, scene_plan=scene_plan, total_duration_seconds=10.0)

    composition_plan = build_composition_plan(ai_plan, timeline_plan=timeline_plan, topic="Test")

    assert composition_plan.scenes[0].retention is None


def test_count_planned_images_treats_empty_beats_as_one_image():
    composition_plan = CompositionPlan(
        topic="Test", scenes=[_composition(1, beat_count=0), _composition(2, beat_count=3)]
    )

    assert count_planned_images(composition_plan) == 1 + 3


def test_clamp_visual_beats_per_scene_trims_to_ceiling_keeping_earliest():
    composition_plan = CompositionPlan(topic="Test", scenes=[_composition(1, beat_count=5)])

    clamped = clamp_visual_beats_per_scene(composition_plan, maximum_per_scene=2)

    assert [beat.beat_number for beat in clamped.scenes[0].visual_beats] == [1, 2]


def test_clamp_visual_beats_per_scene_never_trims_below_the_ceiling():
    composition_plan = CompositionPlan(topic="Test", scenes=[_composition(1, beat_count=2)])

    clamped = clamp_visual_beats_per_scene(composition_plan, maximum_per_scene=4)

    assert len(clamped.scenes[0].visual_beats) == 2


def test_enforce_visual_beat_budget_trims_the_scene_with_the_most_beats_first():
    composition_plan = CompositionPlan(
        topic="Test", scenes=[_composition(1, beat_count=1), _composition(2, beat_count=4)]
    )

    trimmed = enforce_visual_beat_budget(composition_plan, max_total_images=3)

    assert count_planned_images(trimmed) == 3
    assert len(trimmed.scenes[0].visual_beats) == 1  # untouched — already at the floor
    assert len(trimmed.scenes[1].visual_beats) == 2  # trimmed from 4 down to fit (1 + 2 == 3)


def test_enforce_visual_beat_budget_never_removes_a_scenes_last_image():
    # Every scene already at its 1-image floor (0 beats == 1 implicit image) —
    # the budget can't be satisfied without violating the backward-compat
    # guarantee, so the function must stop trimming rather than go to zero scenes.
    composition_plan = CompositionPlan(
        topic="Test", scenes=[_composition(1, beat_count=0), _composition(2, beat_count=0)]
    )

    trimmed = enforce_visual_beat_budget(composition_plan, max_total_images=1)

    assert count_planned_images(trimmed) == 2


def test_enforce_visual_beat_budget_is_a_no_op_when_already_within_budget():
    composition_plan = CompositionPlan(topic="Test", scenes=[_composition(1, beat_count=2)])

    result = enforce_visual_beat_budget(composition_plan, max_total_images=10)

    assert len(result.scenes[0].visual_beats) == 2
