from __future__ import annotations

from backend.core.config import Settings
from backend.schemas.assets import Scene, ScenePlan
from backend.schemas.composition import ScenePurpose, SceneRelationType
from backend.services.composition_planner import DeterministicCompositionPlanner
from backend.services.timeline_planner import DeterministicTimelinePlanner


def _scene_plan(*scenes: Scene) -> ScenePlan:
    return ScenePlan(topic="Test", scenes=list(scenes))


def _timeline(scene_plan: ScenePlan, total_duration_seconds: float = 80.0):
    return DeterministicTimelinePlanner(Settings()).plan(scene_plan=scene_plan, total_duration_seconds=total_duration_seconds)


def test_plan_returns_skipped_when_timeline_plan_has_no_scenes():
    scene_plan = _scene_plan(Scene(scene_number=1))
    empty_timeline = DeterministicTimelinePlanner(Settings()).plan(scene_plan=scene_plan, total_duration_seconds=0.0)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=empty_timeline)

    assert composition_plan.scenes == []
    assert composition_plan.metadata["status"] == "skipped"


def test_plan_assigns_introduction_to_first_scene_and_carries_timing_verbatim():
    scene_plan = _scene_plan(*[Scene(scene_number=i) for i in range(1, 9)])
    timeline_plan = _timeline(scene_plan)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

    assert composition_plan.scenes[0].purpose == ScenePurpose.INTRODUCTION
    for composition in composition_plan.scenes:
        expected_timing = timeline_plan.timing_for(composition.scene_number)
        assert composition.timing == expected_timing


def test_plan_never_invents_a_duration_different_from_timeline_plan():
    scene_plan = _scene_plan(*[Scene(scene_number=i) for i in range(1, 6)])
    timeline_plan = _timeline(scene_plan, total_duration_seconds=50.0)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

    total_from_composition = sum(scene.timing.duration_seconds for scene in composition_plan.scenes)
    assert total_from_composition == timeline_plan.total_duration_seconds


def test_plan_detects_recurring_object_motif_and_adds_callback_relationship():
    scene_plan = _scene_plan(
        Scene(scene_number=1, narration="They found an old wooden cabinet in the attic."),
        Scene(scene_number=2, narration="Nothing unusual happened here."),
        Scene(scene_number=3, narration="The wooden cabinet appeared again, locked shut."),
    )
    timeline_plan = _timeline(scene_plan, total_duration_seconds=30.0)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

    assert any(motif.description == "cabinet" for motif in composition_plan.motifs)
    scene_three = next(scene for scene in composition_plan.scenes if scene.scene_number == 3)
    assert "cabinet" in scene_three.continuity_tags
    assert any(
        relationship.relation_type == SceneRelationType.CALLBACK and relationship.reference_scene_number == 1
        for relationship in scene_three.relationships
    )


def test_plan_adds_continuation_relationship_for_consecutive_same_purpose_scenes():
    # Two adjacent scenes near the start of a large scene count land on the same
    # (STANDARD -> DISCOVERY) purpose bucket, exercising the CONTINUATION rule.
    scene_plan = _scene_plan(*[Scene(scene_number=i) for i in range(1, 9)])
    timeline_plan = _timeline(scene_plan)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)
    purposes = [scene.purpose for scene in composition_plan.scenes]

    continuation_found = False
    for index in range(1, len(composition_plan.scenes)):
        if purposes[index] == purposes[index - 1]:
            relationships = composition_plan.scenes[index].relationships
            if any(r.relation_type == SceneRelationType.CONTINUATION for r in relationships):
                continuation_found = True
    assert continuation_found


def test_plan_is_deterministic_across_repeated_calls():
    scene_plan = _scene_plan(
        Scene(scene_number=1, narration="A quiet house on the hill."),
        Scene(scene_number=2, narration="A quiet house on the hill again."),
    )
    timeline_plan = _timeline(scene_plan, total_duration_seconds=20.0)
    planner = DeterministicCompositionPlanner()

    first = planner.plan(scene_plan=scene_plan, timeline_plan=timeline_plan)
    second = planner.plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

    assert first.model_dump() == second.model_dump()


def test_plan_bounds_motif_count_at_five():
    words = [
        "lighthouse", "cathedral", "mountain", "obsidian", "labyrinth",
        "serenade", "wilderness", "chronicle", "artifact", "threshold",
    ]
    scenes = [
        Scene(scene_number=index + 1, narration=f"{word} appears here and reappears constantly")
        for index, word in enumerate(words)
    ]
    # Force every word to repeat across two scenes so all 10 would qualify as motifs
    # without the cap.
    scenes.append(Scene(scene_number=len(scenes) + 1, narration=" ".join(words)))
    scene_plan = _scene_plan(*scenes)
    timeline_plan = _timeline(scene_plan, total_duration_seconds=60.0)

    composition_plan = DeterministicCompositionPlanner().plan(scene_plan=scene_plan, timeline_plan=timeline_plan)

    assert len(composition_plan.motifs) <= 5
