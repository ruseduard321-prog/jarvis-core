from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)


def _profile(**overrides) -> RenderProfile:
    defaults = dict(
        name="test_profile",
        target_platform=TargetPlatform.YOUTUBE_LONG,
        width=1920,
        height=1080,
        aspect_ratio="16:9",
        frame_rate=30,
        video_codec=VideoCodec.H264,
        audio_codec=AudioCodec.AAC,
        audio_sample_rate=48000,
        bitrate_strategy=BitrateStrategy.CRF,
        crf=18,
        container=ContainerFormat.MP4,
    )
    defaults.update(overrides)
    return RenderProfile(**defaults)


def test_valid_profile_constructs_successfully():
    profile = _profile()
    assert profile.width == 1920
    assert profile.color_space == "bt709"
    assert profile.pixel_format == "yuv420p"
    assert profile.encoder_preset == "medium"


def test_rejects_mismatched_aspect_ratio_and_resolution():
    with pytest.raises(ValidationError, match="aspect_ratio"):
        _profile(aspect_ratio="9:16")  # 1920x1080 is 16:9, not 9:16


def test_rejects_malformed_aspect_ratio_string():
    with pytest.raises(ValidationError, match="W:H"):
        _profile(aspect_ratio="widescreen")


def test_accepts_vertical_profile_with_matching_aspect_ratio():
    profile = _profile(width=1080, height=1920, aspect_ratio="9:16")
    assert profile.aspect_ratio == "9:16"


def test_rejects_unsupported_audio_sample_rate():
    with pytest.raises(ValidationError, match="audio_sample_rate"):
        _profile(audio_sample_rate=22050)


def test_rejects_crf_strategy_without_crf_value():
    with pytest.raises(ValidationError, match="crf is required"):
        _profile(bitrate_strategy=BitrateStrategy.CRF, crf=None)


def test_rejects_cbr_strategy_without_bitrate():
    with pytest.raises(ValidationError, match="video_bitrate_kbps is required"):
        _profile(bitrate_strategy=BitrateStrategy.CBR, crf=None, video_bitrate_kbps=None)


def test_accepts_cbr_strategy_with_bitrate():
    profile = _profile(bitrate_strategy=BitrateStrategy.CBR, crf=None, video_bitrate_kbps=8000)
    assert profile.video_bitrate_kbps == 8000


def test_rejects_non_positive_width_or_height():
    with pytest.raises(ValidationError):
        _profile(width=0)
    with pytest.raises(ValidationError):
        _profile(height=-10)


def test_rejects_frame_rate_out_of_range():
    with pytest.raises(ValidationError):
        _profile(frame_rate=0)
    with pytest.raises(ValidationError):
        _profile(frame_rate=1000)


def test_rejects_crf_out_of_valid_range():
    with pytest.raises(ValidationError):
        _profile(crf=52)


def test_mutating_to_invalid_state_is_rejected_by_validate_assignment():
    profile = _profile()
    with pytest.raises(ValidationError):
        profile.audio_sample_rate = 11025
