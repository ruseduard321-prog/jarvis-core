from __future__ import annotations

from backend.core.config import Settings
from backend.schemas.assets import Scene, ScenePlan, VoiceAsset
from backend.services.audio_timeline_planner import DeterministicAudioTimelinePlanner
from backend.services.timeline_planner import DeterministicTimelinePlanner


def _voice_asset(duration: float = 30.0) -> VoiceAsset:
    return VoiceAsset(provider="fake-tts", generation_time="2026-01-01T00:00:00Z", status="SUCCESS", duration=duration)


def test_plan_produces_one_full_length_narration_segment():
    planner = DeterministicAudioTimelinePlanner(Settings())

    timeline = planner.plan(
        voice_asset=_voice_asset(30.0), scene_plan=None, music_source_path=None, sound_effect_paths_by_scene={}
    )

    assert timeline.total_duration_seconds == 30.0
    assert len(timeline.narration_segments) == 1
    assert timeline.narration_segments[0].duration_seconds == 30.0
    assert timeline.music_cues == []
    assert timeline.sound_effect_events == []


def test_plan_adds_a_ducked_music_cue_when_a_track_is_selected():
    planner = DeterministicAudioTimelinePlanner(Settings())

    timeline = planner.plan(
        voice_asset=_voice_asset(30.0),
        scene_plan=None,
        music_source_path="/library/ambient/track.mp3",
        sound_effect_paths_by_scene={},
    )

    assert len(timeline.music_cues) == 1
    cue = timeline.music_cues[0]
    assert cue.source_path == "/library/ambient/track.mp3"
    assert cue.duration_seconds == 30.0
    assert cue.duck_under_narration is True
    assert cue.fade_in_seconds > 0
    assert cue.fade_out_seconds > 0


def test_plan_places_sfx_events_and_scene_transitions_proportionally():
    planner = DeterministicAudioTimelinePlanner(Settings())
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1), Scene(scene_number=2)])

    timeline = planner.plan(
        voice_asset=_voice_asset(20.0),
        scene_plan=scene_plan,
        music_source_path=None,
        sound_effect_paths_by_scene={2: "/library/sfx/wind.wav"},
    )

    assert len(timeline.scene_transitions) == 2
    assert timeline.scene_transitions[0].at_seconds == 0.0
    assert timeline.scene_transitions[1].at_seconds == 10.0
    assert len(timeline.sound_effect_events) == 1
    assert timeline.sound_effect_events[0].scene_number == 2
    assert timeline.sound_effect_events[0].at_seconds == 10.0


def test_plan_uses_settings_for_master_fade_and_loudness():
    settings = Settings(
        audio_master_loudness_lufs=-16.0, audio_master_fade_in_seconds=0.5, audio_master_fade_out_seconds=1.5
    )
    planner = DeterministicAudioTimelinePlanner(settings)

    timeline = planner.plan(
        voice_asset=_voice_asset(10.0), scene_plan=None, music_source_path=None, sound_effect_paths_by_scene={}
    )

    assert timeline.master_loudness_lufs == -16.0
    assert timeline.fade_in_seconds == 0.5
    assert timeline.fade_out_seconds == 1.5


def test_plan_handles_zero_duration_voice_asset_gracefully():
    planner = DeterministicAudioTimelinePlanner(Settings())

    timeline = planner.plan(
        voice_asset=_voice_asset(0.0),
        scene_plan=None,
        music_source_path="/library/track.mp3",
        sound_effect_paths_by_scene={},
    )

    assert timeline.total_duration_seconds == 0.0
    assert timeline.music_cues == []


def test_plan_uses_timeline_plan_start_seconds_when_given_and_covering_all_scenes():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1), Scene(scene_number=2)])
    # A non-uniform TimelinePlan: scene 1 is much shorter than scene 2 — if the
    # planner ignored timeline_plan and fell back to its own proportional split,
    # scene_transitions[1].at_seconds would be 10.0 (half of 20), not 4.0.
    timeline_plan = DeterministicTimelinePlanner(Settings()).plan(scene_plan=scene_plan, total_duration_seconds=20.0)
    # Force a deliberately non-uniform plan for this assertion instead of relying
    # on the pacing arc's specific multipliers.
    timeline_plan = timeline_plan.model_copy(
        update={
            "scenes": [
                timeline_plan.scenes[0].model_copy(update={"start_seconds": 0.0, "duration_seconds": 4.0, "end_seconds": 4.0}),
                timeline_plan.scenes[1].model_copy(update={"start_seconds": 4.0, "duration_seconds": 16.0, "end_seconds": 20.0}),
            ]
        }
    )
    planner = DeterministicAudioTimelinePlanner(Settings())

    timeline = planner.plan(
        voice_asset=_voice_asset(20.0),
        scene_plan=scene_plan,
        music_source_path=None,
        sound_effect_paths_by_scene={},
        timeline_plan=timeline_plan,
    )

    assert timeline.scene_transitions[0].at_seconds == 0.0
    assert timeline.scene_transitions[1].at_seconds == 4.0


def test_plan_falls_back_to_proportional_split_when_timeline_plan_is_missing_a_scene():
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1), Scene(scene_number=2)])
    # TimelinePlan only covers scene 1 — a mismatch that must trigger the fallback
    # rather than a crash or a partially-applied timeline.
    incomplete_timeline_plan = DeterministicTimelinePlanner(Settings()).plan(
        scene_plan=ScenePlan(topic="Test", scenes=[Scene(scene_number=1)]), total_duration_seconds=20.0
    )
    planner = DeterministicAudioTimelinePlanner(Settings())

    timeline = planner.plan(
        voice_asset=_voice_asset(20.0),
        scene_plan=scene_plan,
        music_source_path=None,
        sound_effect_paths_by_scene={},
        timeline_plan=incomplete_timeline_plan,
    )

    assert timeline.scene_transitions[0].at_seconds == 0.0
    assert timeline.scene_transitions[1].at_seconds == 10.0


def test_plan_without_timeline_plan_keeps_original_proportional_behavior():
    planner = DeterministicAudioTimelinePlanner(Settings())
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1), Scene(scene_number=2)])

    timeline = planner.plan(
        voice_asset=_voice_asset(20.0), scene_plan=scene_plan, music_source_path=None, sound_effect_paths_by_scene={}
    )

    assert timeline.scene_transitions[0].at_seconds == 0.0
    assert timeline.scene_transitions[1].at_seconds == 10.0
