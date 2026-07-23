from __future__ import annotations

from backend.services.voice_direction_planner import DeterministicVoiceDirectionPlanner
from backend.services.voice_profiles import VOICE_PROFILES


def test_plan_resolves_direction_from_profile():
    planner = DeterministicVoiceDirectionPlanner()
    direction = planner.plan(profile_key="documentary_male")

    profile = VOICE_PROFILES["documentary_male"]
    assert direction.profile == "documentary_male"
    assert direction.model == profile.model
    assert direction.voice == profile.voice
    assert direction.pace == profile.pace
    assert direction.instructions == profile.instructions


def test_plan_falls_back_to_default_for_unknown_profile():
    planner = DeterministicVoiceDirectionPlanner()
    direction = planner.plan(profile_key="does-not-exist")

    assert direction.profile == "documentary_male"
