from __future__ import annotations

import subprocess
from datetime import datetime, timezone

import pytest

from backend.core.config import Settings
from backend.schemas.assets import Scene, SceneImageAsset, SceneImageSet, ScenePlan, SubtitleAsset, VoiceAsset
from backend.schemas.composition import (
    CameraIntent,
    ColorLanguage,
    CompositionPlan,
    CompositionStyle,
    SceneComposition,
    ScenePurpose,
)
from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)
from backend.schemas.timeline import ScenePacing, SceneTiming
from backend.services.render_profile_registry import YOUTUBE_LONG_PROFILE
from backend.services.video_assembly_service import VideoAssemblyService


class FakeSubprocessRunner:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stderr: bytes = b"",
        output_bytes: bytes = b"fake-mp4-bytes",
        fail_on_calls: set[int] | None = None,
    ):
        self.returncode = returncode
        self.stderr = stderr
        self.output_bytes = output_bytes
        self.fail_on_calls = fail_on_calls or set()
        self.calls: list[list[str]] = []

    def __call__(self, args, capture_output=True, timeout=None):
        self.calls.append(args)
        call_index = len(self.calls)
        returncode = self.returncode if call_index not in self.fail_on_calls else 1
        output_path = args[-1]
        if returncode == 0:
            with open(output_path, "wb") as handle:
                handle.write(self.output_bytes)
        stderr = self.stderr if returncode == 0 else (self.stderr or b"forced failure")
        return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=b"", stderr=stderr)


def _scene_image_set(*, statuses: list[str]) -> SceneImageSet:
    images = [
        SceneImageAsset(
            scene_number=i + 1,
            provider="fake-image",
            generation_time="2026-01-01T00:00:00Z",
            filename=f"scene_{i + 1:02d}.png",
            status=status,
        )
        for i, status in enumerate(statuses)
    ]
    return SceneImageSet(topic="Test Topic", images=images)


def _voice_asset(*, status: str = "SUCCESS", duration: float = 6.0) -> VoiceAsset:
    return VoiceAsset(
        provider="fake-tts", generation_time="2026-01-01T00:00:00Z", status=status, duration=duration
    )


def _subtitle_asset(*, status: str = "SUCCESS") -> SubtitleAsset:
    return SubtitleAsset(generation_time="2026-01-01T00:00:00Z", status=status, cue_count=1)


@pytest.mark.asyncio
async def test_execute_skips_when_no_scene_images(tmp_path):
    service = VideoAssemblyService(
        settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=FakeSubprocessRunner()
    )

    asset, video_bytes = await service.execute(
        scene_image_set=_scene_image_set(statuses=[]),
        image_bytes_by_filename={},
        voice_asset=_voice_asset(),
        audio_bytes=b"fake-audio",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-1",
    )

    assert asset.status == "SKIPPED"
    assert video_bytes is None
    assert asset.file_path is None


@pytest.mark.asyncio
async def test_execute_assembles_cinematic_video_by_default(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS", "SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes", "scene_02.png": b"scene-2-bytes"},
        voice_asset=_voice_asset(duration=6.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-1",
    )

    assert asset.status == "SUCCESS"
    assert asset.provider == "ffmpeg-cinematic"
    assert asset.render_mode == "cinematic"
    assert asset.scene_count == 2
    assert len(asset.camera_movements) == 2
    assert asset.transition
    assert video_bytes == b"fake-mp4-bytes"
    # 2 per-scene clip renders + 1 final compose call
    assert len(runner.calls) == 3
    compose_args = runner.calls[-1]
    assert any(arg.endswith("voice.mp3") for arg in compose_args)
    assert any(arg.endswith("subtitles.srt") for arg in compose_args)
    assert "mov_text" in compose_args

    saved_path = tmp_path / "run-1" / "video.mp4"
    assert asset.file_path == str(saved_path.resolve())
    assert saved_path.read_bytes() == b"fake-mp4-bytes"


@pytest.mark.asyncio
async def test_execute_skips_audio_and_subtitles_when_unavailable(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(status="FAILED", duration=0.0),
        audio_bytes=None,
        subtitle_asset=_subtitle_asset(status="FAILED"),
        subtitle_content="",
        run_id="run-2",
    )

    assert asset.status == "SUCCESS"
    assert asset.render_mode == "cinematic"
    compose_args = runner.calls[-1]
    assert not any(arg.endswith("voice.mp3") for arg in compose_args)
    assert not any(arg.endswith("subtitles.srt") for arg in compose_args)
    assert "aac" not in compose_args
    assert "mov_text" not in compose_args


@pytest.mark.asyncio
async def test_execute_uses_legacy_slideshow_when_cinematic_rendering_disabled(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(
        settings=Settings(run_storage_root=str(tmp_path), cinematic_rendering_enabled=False),
        subprocess_runner=runner,
    )
    scene_image_set = _scene_image_set(statuses=["SUCCESS", "SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes", "scene_02.png": b"scene-2-bytes"},
        voice_asset=_voice_asset(duration=6.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-1",
    )

    assert asset.status == "SUCCESS"
    assert asset.provider == "ffmpeg-local"
    assert asset.render_mode == "slideshow"
    assert asset.scene_count == 2
    assert len(runner.calls) == 1
    args = runner.calls[0]
    assert "-i" in args
    assert any(arg.endswith("voice.mp3") for arg in args)
    assert any(arg.endswith("subtitles.srt") for arg in args)
    assert "mov_text" in args


@pytest.mark.asyncio
async def test_execute_falls_back_to_slideshow_when_cinematic_rendering_fails(tmp_path):
    # The first subprocess call is the cinematic path's first per-scene clip render;
    # forcing it to fail should trigger the automatic fallback to the legacy slideshow,
    # whose single subprocess call (call #2) succeeds normally.
    runner = FakeSubprocessRunner(fail_on_calls={1})
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS", "SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes", "scene_02.png": b"scene-2-bytes"},
        voice_asset=_voice_asset(duration=6.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-1",
    )

    assert asset.status == "SUCCESS"
    assert asset.provider == "ffmpeg-local"
    assert asset.render_mode == "slideshow"
    assert video_bytes == b"fake-mp4-bytes"


@pytest.mark.asyncio
async def test_execute_returns_failed_asset_on_nonzero_ffmpeg_exit(tmp_path):
    runner = FakeSubprocessRunner(returncode=1, stderr=b"invalid input")
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(status="FAILED", duration=0.0),
        audio_bytes=None,
        subtitle_asset=_subtitle_asset(status="FAILED"),
        subtitle_content="",
        run_id="run-3",
    )

    assert asset.status == "FAILED"
    assert "invalid input" in asset.error
    assert video_bytes is None
    assert asset.file_path is None


@pytest.mark.asyncio
async def test_execute_returns_failed_asset_when_ffmpeg_binary_missing(tmp_path):
    def raising_runner(args, capture_output=True, timeout=None):
        raise FileNotFoundError("ffmpeg not found")

    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=raising_runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])

    asset, video_bytes = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(status="FAILED", duration=0.0),
        audio_bytes=None,
        subtitle_asset=_subtitle_asset(status="FAILED"),
        subtitle_content="",
        run_id="run-4",
    )

    assert asset.status == "FAILED"
    assert "ffmpeg binary not found" in asset.error
    assert video_bytes is None
    assert asset.file_path is None


@pytest.mark.asyncio
async def test_execute_passes_scene_plan_into_shot_selection(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])
    scene_plan = ScenePlan(topic="Test Topic", scenes=[Scene(scene_number=1, camera="Pan left across the skyline")])

    asset, _ = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(status="FAILED", duration=0.0),
        audio_bytes=None,
        subtitle_asset=_subtitle_asset(status="FAILED"),
        subtitle_content="",
        run_id="run-5",
        scene_plan=scene_plan,
    )

    assert asset.camera_movements == ["pan_left"]


def _scene_composition(scene_number: int, duration: float) -> SceneComposition:
    return SceneComposition(
        scene_number=scene_number,
        timing=SceneTiming(
            scene_number=scene_number,
            order=scene_number,
            start_seconds=0.0,
            end_seconds=duration,
            duration_seconds=duration,
            pacing=ScenePacing.STANDARD,
        ),
        purpose=ScenePurpose.DISCOVERY,
        composition_style=CompositionStyle.DETAIL_SHOT,
        camera_intent=CameraIntent.INVESTIGATION,
        color_language=ColorLanguage.NEUTRAL,
    )


@pytest.mark.asyncio
async def test_execute_uses_composition_plans_variable_durations_for_total_duration(tmp_path):
    # Regression test for the F27 duration-formula fix: total video duration must
    # sum each shot's own duration, not assume every scene is scene_seconds long.
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS", "SUCCESS"])
    composition_plan = CompositionPlan(
        topic="Test",
        timeline_total_duration_seconds=10.0,
        scenes=[_scene_composition(1, 2.0), _scene_composition(2, 8.0)],
    )

    asset, _ = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes", "scene_02.png": b"scene-2-bytes"},
        voice_asset=_voice_asset(duration=10.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-6",
        composition_plan=composition_plan,
    )

    assert asset.status == "SUCCESS"
    transition_seconds = Settings().cinematic_transition_duration_seconds
    assert asset.duration == pytest.approx(10.0 - transition_seconds)


@pytest.mark.asyncio
async def test_execute_falls_back_when_composition_plan_scene_count_mismatches_images(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(settings=Settings(run_storage_root=str(tmp_path)), subprocess_runner=runner)
    scene_image_set = _scene_image_set(statuses=["SUCCESS", "SUCCESS"])
    # Only one SceneComposition for two images — a mismatch that must trigger the
    # automatic fallback to uniform-duration shot planning rather than crashing.
    composition_plan = CompositionPlan(
        topic="Test", timeline_total_duration_seconds=2.0, scenes=[_scene_composition(1, 2.0)]
    )

    asset, _ = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes", "scene_02.png": b"scene-2-bytes"},
        voice_asset=_voice_asset(duration=6.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-7",
        composition_plan=composition_plan,
    )

    assert asset.status == "SUCCESS"
    assert asset.scene_count == 2


@pytest.mark.asyncio
async def test_slideshow_fallback_uses_default_render_profile(tmp_path):
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(
        settings=Settings(run_storage_root=str(tmp_path), cinematic_rendering_enabled=False),
        subprocess_runner=runner,
    )
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])

    asset, _ = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(duration=3.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-8",
    )

    assert asset.status == "SUCCESS"
    args = runner.calls[0]
    assert "libx264" in args
    assert str(YOUTUBE_LONG_PROFILE.frame_rate) in args
    assert "-crf" in args
    assert str(YOUTUBE_LONG_PROFILE.crf) in args
    assert "48000" in args


@pytest.mark.asyncio
async def test_slideshow_fallback_uses_custom_render_profile(tmp_path):
    custom_profile = RenderProfile(
        name="custom",
        target_platform=TargetPlatform.YOUTUBE_SHORTS,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        frame_rate=30,
        video_codec=VideoCodec.HEVC,
        audio_codec=AudioCodec.OPUS,
        audio_sample_rate=44100,
        bitrate_strategy=BitrateStrategy.VBR,
        video_bitrate_kbps=5000,
        container=ContainerFormat.WEBM,
    )
    runner = FakeSubprocessRunner()
    service = VideoAssemblyService(
        settings=Settings(run_storage_root=str(tmp_path), cinematic_rendering_enabled=False),
        subprocess_runner=runner,
        render_profile=custom_profile,
    )
    scene_image_set = _scene_image_set(statuses=["SUCCESS"])

    asset, _ = await service.execute(
        scene_image_set=scene_image_set,
        image_bytes_by_filename={"scene_01.png": b"scene-1-bytes"},
        voice_asset=_voice_asset(duration=3.0),
        audio_bytes=b"fake-audio-bytes",
        subtitle_asset=_subtitle_asset(),
        subtitle_content="1\n00:00:00,000 --> 00:00:02,000\nHello\n",
        run_id="run-9",
    )

    assert asset.status == "SUCCESS"
    args = runner.calls[0]
    assert "libx265" in args
    assert "libopus" in args
    assert "44100" in args
    assert "-b:v" in args
    assert "5000k" in args
    assert any(arg.endswith("video.webm") for arg in args)
