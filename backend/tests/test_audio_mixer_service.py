from __future__ import annotations

import subprocess

import pytest

from backend.core.config import Settings
from backend.schemas.audio import AudioTimeline, MusicCue, NarrationSegment, SoundEffectEvent
from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)
from backend.services.audio_mixer_service import AudioMixError, AudioMixerService
from backend.services.render_profile_registry import YOUTUBE_LONG_PROFILE


class FakeSubprocessRunner:
    def __init__(self, *, returncode: int = 0, output_bytes: bytes = b"fake-mixed-bytes"):
        self.returncode = returncode
        self.output_bytes = output_bytes
        self.calls: list[list[str]] = []

    def __call__(self, args, capture_output=True, timeout=None):
        self.calls.append(args)
        output_path = args[-1]
        if self.returncode == 0:
            with open(output_path, "wb") as handle:
                handle.write(self.output_bytes)
        return subprocess.CompletedProcess(
            args=args, returncode=self.returncode, stdout=b"", stderr=b"" if self.returncode == 0 else b"boom"
        )


def _timeline(**overrides) -> AudioTimeline:
    defaults: dict = dict(
        total_duration_seconds=10.0,
        narration_segments=[NarrationSegment(start_seconds=0.0, duration_seconds=10.0)],
    )
    defaults.update(overrides)
    return AudioTimeline(**defaults)


def test_mix_narration_only_skips_amix_and_masters(tmp_path):
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)

    result = mixer.mix(
        narration_bytes=b"narration-bytes", timeline=_timeline(), music_bytes={}, sound_effect_bytes={}, timeout_seconds=30.0
    )

    assert result == b"fake-mixed-bytes"
    args = runner.calls[0]
    assert args.count("-i") == 1
    filter_complex = args[args.index("-filter_complex") + 1]
    assert "amix" not in filter_complex
    assert "loudnorm" in filter_complex
    assert "aac" in args


def test_mix_with_music_cue_applies_ducking_and_amix(tmp_path):
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)
    timeline = _timeline(
        music_cues=[
            MusicCue(start_seconds=0.0, duration_seconds=10.0, source_path="/lib/track.mp3", duck_under_narration=True)
        ]
    )

    mixer.mix(
        narration_bytes=b"narration-bytes",
        timeline=timeline,
        music_bytes={"/lib/track.mp3": b"music-bytes"},
        sound_effect_bytes={},
        timeout_seconds=30.0,
    )

    args = runner.calls[0]
    assert args.count("-i") == 2
    filter_complex = args[args.index("-filter_complex") + 1]
    assert "sidechaincompress" in filter_complex
    assert "amix=inputs=2" in filter_complex


def test_mix_with_sound_effect_event_positions_it_with_adelay(tmp_path):
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)
    timeline = _timeline(sound_effect_events=[SoundEffectEvent(at_seconds=5.0, source_path="/sfx/wind.wav")])

    mixer.mix(
        narration_bytes=b"narration-bytes",
        timeline=timeline,
        music_bytes={},
        sound_effect_bytes={"/sfx/wind.wav": b"sfx-bytes"},
        timeout_seconds=30.0,
    )

    args = runner.calls[0]
    filter_complex = args[args.index("-filter_complex") + 1]
    assert "adelay=5000|5000" in filter_complex
    assert "amix=inputs=2" in filter_complex


def test_mix_skips_music_cue_when_bytes_were_not_resolved(tmp_path):
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)
    timeline = _timeline(
        music_cues=[MusicCue(start_seconds=0.0, duration_seconds=10.0, source_path="/lib/missing.mp3")]
    )

    mixer.mix(
        narration_bytes=b"narration-bytes",
        timeline=timeline,
        music_bytes={},
        sound_effect_bytes={},
        timeout_seconds=30.0,
    )

    args = runner.calls[0]
    assert args.count("-i") == 1
    filter_complex = args[args.index("-filter_complex") + 1]
    assert "sidechaincompress" not in filter_complex


def test_mix_raises_audio_mix_error_on_ffmpeg_failure(tmp_path):
    runner = FakeSubprocessRunner(returncode=1)
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)

    with pytest.raises(AudioMixError):
        mixer.mix(
            narration_bytes=b"narration-bytes",
            timeline=_timeline(),
            music_bytes={},
            sound_effect_bytes={},
            timeout_seconds=30.0,
        )


def test_mix_uses_default_render_profile_codec_and_sample_rate(tmp_path):
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner)

    mixer.mix(
        narration_bytes=b"narration-bytes", timeline=_timeline(), music_bytes={}, sound_effect_bytes={}, timeout_seconds=30.0
    )

    args = runner.calls[0]
    assert "aac" in args
    assert str(YOUTUBE_LONG_PROFILE.audio_sample_rate) in args


def test_mix_uses_custom_render_profile_codec_and_sample_rate(tmp_path):
    custom_profile = RenderProfile(
        name="custom",
        target_platform=TargetPlatform.TIKTOK,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        frame_rate=30,
        video_codec=VideoCodec.H264,
        audio_codec=AudioCodec.OPUS,
        audio_sample_rate=44100,
        bitrate_strategy=BitrateStrategy.CRF,
        crf=20,
        container=ContainerFormat.MP4,
    )
    runner = FakeSubprocessRunner()
    mixer = AudioMixerService(Settings(), subprocess_runner=runner, render_profile=custom_profile)

    mixer.mix(
        narration_bytes=b"narration-bytes", timeline=_timeline(), music_bytes={}, sound_effect_bytes={}, timeout_seconds=30.0
    )

    args = runner.calls[0]
    assert "libopus" in args
    assert "44100" in args
