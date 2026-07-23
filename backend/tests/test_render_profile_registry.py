from __future__ import annotations

import pytest

from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)
from backend.services.render_profile_registry import (
    DEFAULT_RENDER_PROFILE_NAME,
    YOUTUBE_LONG_PROFILE,
    RenderProfileNotFoundError,
    RenderProfileRegistry,
    build_default_render_profile_registry,
)


def test_default_registry_contains_youtube_long_profile():
    registry = build_default_render_profile_registry()
    profile = registry.get(DEFAULT_RENDER_PROFILE_NAME)
    assert profile == YOUTUBE_LONG_PROFILE


def test_get_with_none_name_returns_default_profile():
    registry = build_default_render_profile_registry()
    assert registry.get(None) == YOUTUBE_LONG_PROFILE


def test_get_with_empty_string_returns_default_profile():
    registry = build_default_render_profile_registry()
    assert registry.get("") == YOUTUBE_LONG_PROFILE


def test_youtube_long_profile_matches_brief_requirements():
    assert YOUTUBE_LONG_PROFILE.width == 1920
    assert YOUTUBE_LONG_PROFILE.height == 1080
    assert YOUTUBE_LONG_PROFILE.aspect_ratio == "16:9"
    assert YOUTUBE_LONG_PROFILE.frame_rate == 30
    assert YOUTUBE_LONG_PROFILE.video_codec == VideoCodec.H264
    assert YOUTUBE_LONG_PROFILE.audio_codec == AudioCodec.AAC
    assert YOUTUBE_LONG_PROFILE.audio_sample_rate == 48000
    assert YOUTUBE_LONG_PROFILE.container == ContainerFormat.MP4


def test_get_raises_not_found_for_unregistered_name():
    registry = build_default_render_profile_registry()
    with pytest.raises(RenderProfileNotFoundError):
        registry.get("does_not_exist")


def test_register_new_profile_makes_it_retrievable():
    registry = RenderProfileRegistry()
    shorts = RenderProfile(
        name="youtube_shorts",
        target_platform=TargetPlatform.YOUTUBE_SHORTS,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        frame_rate=30,
        video_codec=VideoCodec.H264,
        audio_codec=AudioCodec.AAC,
        audio_sample_rate=48000,
        bitrate_strategy=BitrateStrategy.CRF,
        crf=20,
        container=ContainerFormat.MP4,
    )
    registry.register(shorts)

    assert registry.get("youtube_shorts") == shorts
    assert len(registry.list_profiles()) == 1


def test_registering_a_new_profile_does_not_require_renderer_changes():
    # This is the concrete architectural claim F28A makes: adding a profile is
    # registering data, nothing else. An empty registry plus one registration is
    # a fully functional registry — no RendererPipeline/RenderProfileRegistry
    # code path needs to change to support it.
    registry = RenderProfileRegistry()
    assert registry.list_profiles() == []
    registry.register(YOUTUBE_LONG_PROFILE)
    assert registry.get("youtube_long") == YOUTUBE_LONG_PROFILE
