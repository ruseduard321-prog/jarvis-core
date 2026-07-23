from __future__ import annotations

import subprocess

import pytest

from backend.core.config import Settings
from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)
from backend.schemas.shots import CameraMovementType, Shot, TransitionType
from backend.services.cinematic_renderer_pipeline import CinematicRenderError, RendererPipeline
from backend.services.render_profile_registry import YOUTUBE_LONG_PROFILE


class FakeSubprocessRunner:
    def __init__(self, *, fail_on_call: int | None = None, returncode: int = 0):
        self.calls: list[list[str]] = []
        self._fail_on_call = fail_on_call
        self._returncode = returncode

    def __call__(self, args, capture_output=True, timeout=None):
        self.calls.append(args)
        call_index = len(self.calls)
        returncode = self._returncode if self._fail_on_call is None or call_index == self._fail_on_call else 0
        output_path = args[-1]
        if returncode == 0:
            with open(output_path, "wb") as handle:
                handle.write(f"fake-bytes-call-{call_index}".encode())
        return subprocess.CompletedProcess(
            args=args, returncode=returncode, stdout=b"", stderr=b"" if returncode == 0 else b"boom"
        )


def _shot(scene_number: int, **overrides) -> Shot:
    defaults = dict(scene_number=scene_number, duration_seconds=3.0)
    defaults.update(overrides)
    return Shot(**defaults)


def test_render_two_shots_makes_two_clip_calls_plus_one_compose_call(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    shots = [_shot(1), _shot(2, transition=TransitionType.FADEBLACK)]

    result = pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1"), (2, b"image-2")],
        shots=shots,
        audio_path=None,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    assert len(runner.calls) == 3
    compose_args = runner.calls[-1]
    assert "-filter_complex" in compose_args
    assert any("fadeblack" in arg for arg in compose_args)
    assert result.output_path.exists()
    assert result.shots_used == shots


def test_render_single_shot_skips_filter_complex(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    shots = [_shot(1)]

    pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1")],
        shots=shots,
        audio_path=None,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    assert len(runner.calls) == 2
    compose_args = runner.calls[-1]
    assert "-filter_complex" not in compose_args
    assert "0:v" in compose_args


def test_render_muxes_audio_and_subtitles_in_compose_call(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    audio_path = tmp_path / "voice.mp3"
    audio_path.write_bytes(b"fake-audio")
    subtitle_path = tmp_path / "subtitles.srt"
    subtitle_path.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n")
    shots = [_shot(1), _shot(2)]

    pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1"), (2, b"image-2")],
        shots=shots,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        timeout_seconds=30.0,
    )

    compose_args = runner.calls[-1]
    assert any(arg.endswith("voice.mp3") for arg in compose_args)
    assert any(arg.endswith("subtitles.srt") for arg in compose_args)
    assert "aac" in compose_args
    assert "mov_text" in compose_args


def test_render_raises_cinematic_render_error_when_a_clip_render_fails(tmp_path):
    runner = FakeSubprocessRunner(fail_on_call=1, returncode=1)
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    shots = [_shot(1), _shot(2)]

    with pytest.raises(CinematicRenderError):
        pipeline.render(
            workspace=tmp_path,
            images=[(1, b"image-1"), (2, b"image-2")],
            shots=shots,
            audio_path=None,
            subtitle_path=None,
            timeout_seconds=30.0,
        )


def test_render_raises_cinematic_render_error_when_compose_fails(tmp_path):
    runner = FakeSubprocessRunner(fail_on_call=3, returncode=1)
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    shots = [_shot(1), _shot(2)]

    with pytest.raises(CinematicRenderError):
        pipeline.render(
            workspace=tmp_path,
            images=[(1, b"image-1"), (2, b"image-2")],
            shots=shots,
            audio_path=None,
            subtitle_path=None,
            timeout_seconds=30.0,
        )


def test_render_rejects_mismatched_images_and_shots_length(tmp_path):
    pipeline = RendererPipeline(Settings(), subprocess_runner=FakeSubprocessRunner())
    with pytest.raises(ValueError):
        pipeline.render(
            workspace=tmp_path,
            images=[(1, b"image-1")],
            shots=[_shot(1), _shot(2)],
            audio_path=None,
            subtitle_path=None,
            timeout_seconds=30.0,
        )


def test_movement_filter_uses_all_camera_movement_types(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)
    shots = [_shot(1, camera_movement=CameraMovementType.HANDHELD)]

    pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1")],
        shots=shots,
        audio_path=None,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    clip_args = runner.calls[0]
    vf_index = clip_args.index("-vf")
    assert "sin(" in clip_args[vf_index + 1]


def test_render_defaults_to_the_youtube_long_render_profile(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)

    result = pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1")],
        shots=[_shot(1)],
        audio_path=None,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    compose_args = runner.calls[-1]
    assert "libx264" in compose_args
    assert str(YOUTUBE_LONG_PROFILE.frame_rate) in compose_args
    assert "yuv420p" in compose_args
    assert "bt709" in compose_args
    assert "-crf" in compose_args
    assert str(YOUTUBE_LONG_PROFILE.crf) in compose_args
    assert "medium" in compose_args
    assert result.output_path.name == "video.mp4"


def test_render_scene_clip_uses_profile_resolution_and_frame_rate(tmp_path):
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner)

    pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1")],
        shots=[_shot(1, duration_seconds=2.0)],
        audio_path=None,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    clip_args = runner.calls[0]
    assert str(YOUTUBE_LONG_PROFILE.frame_rate) in clip_args
    assert "yuv420p" in clip_args
    frame_count_index = clip_args.index("-frames:v") + 1
    assert clip_args[frame_count_index] == str(round(2.0 * YOUTUBE_LONG_PROFILE.frame_rate))


def test_render_with_custom_render_profile_uses_its_codec_resolution_and_container(tmp_path):
    # Proves the renderer contains no hardcoded technical values: a completely
    # different profile (HEVC, 4K, 60fps, CBR bitrate, HDR-ish color space, mov
    # container) must show up verbatim in the ffmpeg calls.
    custom_profile = RenderProfile(
        name="custom_4k",
        target_platform=TargetPlatform.YOUTUBE_4K,
        width=3840,
        height=2160,
        aspect_ratio="16:9",
        frame_rate=60,
        video_codec=VideoCodec.HEVC,
        audio_codec=AudioCodec.OPUS,
        audio_sample_rate=48000,
        bitrate_strategy=BitrateStrategy.CBR,
        video_bitrate_kbps=20000,
        container=ContainerFormat.MOV,
        color_space="bt2020",
        pixel_format="yuv420p10le",
        encoder_preset="slow",
    )
    runner = FakeSubprocessRunner()
    pipeline = RendererPipeline(Settings(), subprocess_runner=runner, render_profile=custom_profile)
    audio_path = tmp_path / "voice.mp3"
    audio_path.write_bytes(b"fake-audio")

    result = pipeline.render(
        workspace=tmp_path,
        images=[(1, b"image-1")],
        shots=[_shot(1)],
        audio_path=audio_path,
        subtitle_path=None,
        timeout_seconds=30.0,
    )

    compose_args = runner.calls[-1]
    assert "libx265" in compose_args
    assert "libopus" in compose_args
    assert "60" in compose_args
    assert "bt2020" in compose_args
    assert "yuv420p10le" in compose_args
    assert "-b:v" in compose_args
    assert "20000k" in compose_args
    assert "-minrate" in compose_args  # CBR forces min/max/target equal
    assert "48000" in compose_args
    assert result.output_path.name == "video.mov"

    clip_args = runner.calls[0]
    assert "60" in clip_args
    assert "yuv420p10le" in clip_args
