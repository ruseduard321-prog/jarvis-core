from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.schemas.assets import Scene, ScenePlan
from backend.schemas.timeline import ScenePacing
from backend.services.timeline_planner import DeterministicTimelinePlanner


def _scene_plan(count: int) -> ScenePlan:
    return ScenePlan(topic="Test", scenes=[Scene(scene_number=i) for i in range(1, count + 1)])


def test_plan_returns_empty_timeline_when_no_scenes():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=ScenePlan(topic="Test", scenes=[]), total_duration_seconds=30.0)

    assert timeline.scenes == []
    assert timeline.metadata["status"] == "skipped"


def test_plan_returns_empty_timeline_when_duration_is_zero():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(3), total_duration_seconds=0.0)

    assert timeline.scenes == []
    assert timeline.metadata["status"] == "skipped"


def test_plan_durations_sum_to_exact_total_duration():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(8), total_duration_seconds=64.0)

    assert timeline.total_duration_seconds == 64.0
    assert sum(scene.duration_seconds for scene in timeline.scenes) == pytest.approx(64.0)


def test_plan_assigns_sequential_order_and_contiguous_start_end():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(5), total_duration_seconds=50.0)

    assert [scene.order for scene in timeline.scenes] == [1, 2, 3, 4, 5]
    assert [scene.scene_number for scene in timeline.scenes] == [1, 2, 3, 4, 5]
    for previous, current in zip(timeline.scenes, timeline.scenes[1:]):
        assert current.start_seconds == pytest.approx(previous.end_seconds)


def test_plan_pacing_arc_first_standard_last_breathing_second_to_last_climax():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(8), total_duration_seconds=80.0)

    pacings = [scene.pacing for scene in timeline.scenes]
    assert pacings[0] == ScenePacing.STANDARD
    assert pacings[-1] == ScenePacing.BREATHING
    assert pacings[-2] == ScenePacing.CLIMAX


def test_plan_scenes_do_not_all_share_the_same_duration():
    # This is the concrete regression test for the F27 problem statement: today's
    # pipeline gives every scene identical screen time. TimelinePlan must not.
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(8), total_duration_seconds=80.0)

    durations = {round(scene.duration_seconds, 6) for scene in timeline.scenes}
    assert len(durations) > 1


def test_plan_single_scene_gets_standard_pacing_and_full_duration():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(1), total_duration_seconds=12.0)

    assert len(timeline.scenes) == 1
    assert timeline.scenes[0].pacing == ScenePacing.STANDARD
    assert timeline.scenes[0].duration_seconds == pytest.approx(12.0)


def test_plan_sorts_scenes_by_scene_number_regardless_of_input_order():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=2), Scene(scene_number=1), Scene(scene_number=3)])
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=scene_plan, total_duration_seconds=30.0)

    assert [scene.scene_number for scene in timeline.scenes] == [1, 2, 3]


def test_timing_for_returns_matching_entry_and_none_when_missing():
    planner = DeterministicTimelinePlanner(Settings())
    timeline = planner.plan(scene_plan=_scene_plan(3), total_duration_seconds=30.0)

    found = timeline.timing_for(2)
    assert found is not None
    assert found.scene_number == 2
    assert timeline.timing_for(99) is None
