from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.core.media_asset import MediaAsset
from backend.schemas.assets import MusicPlan, Scene, ScenePlan, VoiceAsset
from backend.schemas.audio import AudioTimeline, NarrationSegment
from backend.services.audio_engine_service import AudioEngineService
from backend.services.audio_mixer_service import AudioMixError


def _voice_asset(status: str = "SUCCESS", duration: float = 10.0) -> VoiceAsset:
    return VoiceAsset(provider="fake-tts", generation_time="2026-01-01T00:00:00Z", status=status, duration=duration)


def _skipped_media_asset() -> MediaAsset:
    return MediaAsset(id="none", type="audio", source="", provider="fake", mime_type="", metadata={"status": "SKIPPED"})


class FakeMusicProvider:
    def __init__(self, asset: MediaAsset | None = None):
        self._asset = asset or _skipped_media_asset()

    async def generate_music(self, *, prompt, duration=None):
        self.called_with = {"prompt": prompt, "duration": duration}
        return self._asset


class FakeSoundEffectProvider:
    def __init__(self, asset: MediaAsset | None = None):
        self._asset = asset or _skipped_media_asset()

    async def get_sound_effect(self, *, keywords):
        self.called_with = {"keywords": keywords}
        return self._asset


class FakeTimelinePlanner:
    def __init__(self, timeline: AudioTimeline | None = None):
        self._timeline = timeline or AudioTimeline(
            total_duration_seconds=10.0, narration_segments=[NarrationSegment(duration_seconds=10.0)]
        )

    def plan(self, **kwargs):
        self.called_with = kwargs
        return self._timeline


class FakeMixer:
    def __init__(self, *, result: bytes | None = b"mixed-bytes", raises: Exception | None = None):
        self._result = result
        self._raises = raises

    def mix(self, **kwargs):
        self.called_with = kwargs
        if self._raises:
            raise self._raises
        return self._result


@pytest.mark.asyncio
async def test_execute_skips_when_no_narration_bytes():
    service = AudioEngineService(
        Settings(),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=FakeTimelinePlanner(),
        mixer=FakeMixer(),
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(), narration_bytes=None, music_plan=None, scene_plan=None
    )

    assert asset.status == "SKIPPED"
    assert mixed is None


@pytest.mark.asyncio
async def test_execute_skips_when_disabled_by_settings():
    service = AudioEngineService(
        Settings(audio_engine_enabled=False),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=FakeTimelinePlanner(),
        mixer=FakeMixer(),
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(), narration_bytes=b"narration", music_plan=None, scene_plan=None
    )

    assert asset.status == "SKIPPED"
    assert mixed is None


@pytest.mark.asyncio
async def test_execute_mixes_narration_only_when_music_and_sfx_disabled():
    mixer = FakeMixer()
    service = AudioEngineService(
        Settings(background_music_enabled=False, sound_effects_enabled=False),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=FakeTimelinePlanner(),
        mixer=mixer,
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(),
        narration_bytes=b"narration",
        music_plan=MusicPlan(reference="ambient"),
        scene_plan=None,
    )

    assert asset.status == "SUCCESS"
    assert mixed == b"mixed-bytes"
    assert asset.music_included is False
    assert mixer.called_with["music_bytes"] == {}


@pytest.mark.asyncio
async def test_execute_resolves_music_when_enabled_and_selection_succeeds(tmp_path):
    track_path = tmp_path / "track.mp3"
    track_path.write_bytes(b"real-music-bytes")
    music_asset = MediaAsset(
        id="track", type="audio", source=str(track_path), provider="fake", mime_type="audio/mpeg", metadata={"status": "SUCCESS"}
    )
    mixer = FakeMixer()

    service = AudioEngineService(
        Settings(background_music_enabled=True),
        music_provider=FakeMusicProvider(asset=music_asset),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=FakeTimelinePlanner(),
        mixer=mixer,
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(),
        narration_bytes=b"narration",
        music_plan=MusicPlan(reference="ambient calm"),
        scene_plan=None,
    )

    assert asset.status == "SUCCESS"
    assert asset.music_included is True
    assert mixer.called_with["music_bytes"] == {str(track_path): b"real-music-bytes"}


@pytest.mark.asyncio
async def test_execute_resolves_sound_effects_per_scene_when_enabled(tmp_path):
    sfx_path = tmp_path / "wind.wav"
    sfx_path.write_bytes(b"real-sfx-bytes")
    sfx_asset = MediaAsset(
        id="wind", type="audio", source=str(sfx_path), provider="fake", mime_type="audio/wav", metadata={"status": "SUCCESS"}
    )
    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1, environment="windy cliff")])
    mixer = FakeMixer()

    service = AudioEngineService(
        Settings(sound_effects_enabled=True),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(asset=sfx_asset),
        timeline_planner=FakeTimelinePlanner(),
        mixer=mixer,
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(), narration_bytes=b"narration", music_plan=None, scene_plan=scene_plan
    )

    assert asset.status == "SUCCESS"
    assert asset.sound_effect_count == 1
    assert mixer.called_with["sound_effect_bytes"] == {str(sfx_path): b"real-sfx-bytes"}


@pytest.mark.asyncio
async def test_execute_passes_timeline_plan_through_to_timeline_planner():
    from backend.schemas.assets import Scene, ScenePlan
    from backend.services.timeline_planner import DeterministicTimelinePlanner

    scene_plan = ScenePlan(topic="Test", scenes=[Scene(scene_number=1)])
    timeline_plan = DeterministicTimelinePlanner(Settings()).plan(scene_plan=scene_plan, total_duration_seconds=10.0)
    timeline_planner = FakeTimelinePlanner()

    service = AudioEngineService(
        Settings(),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=timeline_planner,
        mixer=FakeMixer(),
    )

    await service.execute(
        voice_asset=_voice_asset(),
        narration_bytes=b"narration",
        music_plan=None,
        scene_plan=scene_plan,
        timeline_plan=timeline_plan,
    )

    assert timeline_planner.called_with["timeline_plan"] is timeline_plan


@pytest.mark.asyncio
async def test_execute_returns_failed_asset_when_mixing_raises():
    mixer = FakeMixer(raises=AudioMixError("boom"))
    service = AudioEngineService(
        Settings(),
        music_provider=FakeMusicProvider(),
        sound_effect_provider=FakeSoundEffectProvider(),
        timeline_planner=FakeTimelinePlanner(),
        mixer=mixer,
    )

    asset, mixed = await service.execute(
        voice_asset=_voice_asset(), narration_bytes=b"narration", music_plan=None, scene_plan=None
    )

    assert asset.status == "FAILED"
    assert mixed is None
