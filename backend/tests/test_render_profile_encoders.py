from __future__ import annotations

from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)
from backend.services.render_profile_encoders import audio_encoder_name, video_bitrate_args, video_encoder_name


def _profile(**overrides) -> RenderProfile:
    defaults = dict(
        name="test",
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


def test_video_encoder_name_maps_every_codec():
    assert video_encoder_name(VideoCodec.H264) == "libx264"
    assert video_encoder_name(VideoCodec.HEVC) == "libx265"
    assert video_encoder_name(VideoCodec.VP9) == "libvpx-vp9"
    assert video_encoder_name(VideoCodec.AV1) == "libaom-av1"


def test_audio_encoder_name_maps_every_codec():
    assert audio_encoder_name(AudioCodec.AAC) == "aac"
    assert audio_encoder_name(AudioCodec.OPUS) == "libopus"
    assert audio_encoder_name(AudioCodec.MP3) == "libmp3lame"


def test_video_bitrate_args_for_crf_strategy():
    profile = _profile(bitrate_strategy=BitrateStrategy.CRF, crf=20)
    assert video_bitrate_args(profile) == ["-crf", "20"]


def test_video_bitrate_args_for_cbr_strategy_forces_min_max_equal_target():
    profile = _profile(bitrate_strategy=BitrateStrategy.CBR, crf=None, video_bitrate_kbps=8000)
    args = video_bitrate_args(profile)
    assert args == ["-b:v", "8000k", "-minrate", "8000k", "-maxrate", "8000k", "-bufsize", "16000k"]


def test_video_bitrate_args_for_vbr_strategy_sets_only_target():
    profile = _profile(bitrate_strategy=BitrateStrategy.VBR, crf=None, video_bitrate_kbps=6000)
    assert video_bitrate_args(profile) == ["-b:v", "6000k"]
