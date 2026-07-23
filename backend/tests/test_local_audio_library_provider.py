from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.services.local_audio_library_provider import LocalMusicLibraryProvider, LocalSoundEffectLibraryProvider


@pytest.mark.asyncio
async def test_generate_music_matches_by_mood_keyword(tmp_path):
    mystery_dir = tmp_path / "mystery"
    mystery_dir.mkdir()
    (mystery_dir / "tense_theme.mp3").write_bytes(b"fake-mp3")
    ambient_dir = tmp_path / "ambient"
    ambient_dir.mkdir()
    (ambient_dir / "calm_pad.mp3").write_bytes(b"fake-mp3")

    provider = LocalMusicLibraryProvider(Settings(music_library_root=str(tmp_path)))

    asset = await provider.generate_music(prompt="mystery tension", duration=30.0)

    assert asset.metadata["status"] == "SUCCESS"
    assert "mystery" in asset.source
    assert asset.duration == 30.0


@pytest.mark.asyncio
async def test_generate_music_falls_back_to_first_track_when_no_keyword_matches(tmp_path):
    ambient_dir = tmp_path / "ambient"
    ambient_dir.mkdir()
    (ambient_dir / "calm_pad.mp3").write_bytes(b"fake-mp3")

    provider = LocalMusicLibraryProvider(Settings(music_library_root=str(tmp_path)))

    asset = await provider.generate_music(prompt="nonexistent genre xyz")

    assert asset.metadata["status"] == "SUCCESS"
    assert asset.source.endswith("calm_pad.mp3")


@pytest.mark.asyncio
async def test_generate_music_skips_when_library_missing(tmp_path):
    provider = LocalMusicLibraryProvider(Settings(music_library_root=str(tmp_path / "does-not-exist")))

    asset = await provider.generate_music(prompt="anything")

    assert asset.metadata["status"] == "SKIPPED"
    assert asset.source == ""


@pytest.mark.asyncio
async def test_get_sound_effect_matches_by_keyword(tmp_path):
    (tmp_path / "wind_howl.wav").write_bytes(b"fake-wav")
    (tmp_path / "typewriter_clack.wav").write_bytes(b"fake-wav")

    provider = LocalSoundEffectLibraryProvider(Settings(sound_effect_library_root=str(tmp_path)))

    asset = await provider.get_sound_effect(keywords="stormy wind outdoors")

    assert asset.metadata["status"] == "SUCCESS"
    assert "wind" in asset.source


@pytest.mark.asyncio
async def test_get_sound_effect_skips_when_library_empty(tmp_path):
    provider = LocalSoundEffectLibraryProvider(Settings(sound_effect_library_root=str(tmp_path)))

    asset = await provider.get_sound_effect(keywords="anything")

    assert asset.metadata["status"] == "SKIPPED"
    assert asset.source == ""
