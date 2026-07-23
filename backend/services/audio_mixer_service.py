from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from backend.core.config import Settings
from backend.schemas.audio import AudioTimeline, MusicCue, SoundEffectEvent
from backend.schemas.render_profile import RenderProfile
from backend.services.render_profile_encoders import audio_encoder_name
from backend.services.render_profile_registry import build_default_render_profile_registry

SubprocessRunner = Callable[..., subprocess.CompletedProcess]


class AudioMixError(RuntimeError):
    """Raised when the final ffmpeg mix call fails; callers fall back to the
    unmixed (normalized) narration track on this exception."""


class AudioMixerService:
    """Executes an AudioTimeline against narration/music/SFX source bytes to produce
    one mixed, mastered audio track via ffmpeg filters only — amix/sidechaincompress
    (ducking), afade (fades), loudnorm (mastering to a fixed LUFS target). Mirrors
    RendererPipeline exactly: every value comes from the AudioTimeline it is given;
    it never chooses volumes, timing, or whether to duck — those are planning
    decisions already made by AudioTimelinePlanner before this is ever called.

    Consumes only `narration_segments[0]` today, since F26 always produces exactly
    one continuous narration source — splicing multiple narration segments from one
    source is a natural future extension of this method's inner loop, not a change
    to the AudioTimeline schema, which already supports a list."""

    def __init__(
        self,
        settings: Settings,
        subprocess_runner: SubprocessRunner | None = None,
        render_profile: RenderProfile | None = None,
    ) -> None:
        self._settings = settings
        self._run_subprocess = subprocess_runner or subprocess.run
        self._render_profile = render_profile or build_default_render_profile_registry().get(settings.render_profile_name)

    def mix(
        self,
        *,
        narration_bytes: bytes,
        timeline: AudioTimeline,
        music_bytes: dict[str, bytes],
        sound_effect_bytes: dict[str, bytes],
        timeout_seconds: float,
    ) -> bytes:
        with tempfile.TemporaryDirectory(prefix="audio_mix_") as work_dir:
            workspace = Path(work_dir)
            narration_path = workspace / "narration.mp3"
            narration_path.write_bytes(narration_bytes)
            inputs = [narration_path]

            resolved_music_cues: list[MusicCue] = []
            for index, cue in enumerate(timeline.music_cues):
                data = music_bytes.get(cue.source_path)
                if data is None:
                    continue
                path = workspace / f"music_{index}{Path(cue.source_path).suffix or '.mp3'}"
                path.write_bytes(data)
                inputs.append(path)
                resolved_music_cues.append(cue)

            resolved_sfx_events: list[SoundEffectEvent] = []
            for index, event in enumerate(timeline.sound_effect_events):
                data = sound_effect_bytes.get(event.source_path)
                if data is None:
                    continue
                path = workspace / f"sfx_{index}{Path(event.source_path).suffix or '.mp3'}"
                path.write_bytes(data)
                inputs.append(path)
                resolved_sfx_events.append(event)

            filter_complex, output_label = self._build_filter_complex(
                timeline, music_cues=resolved_music_cues, sfx_events=resolved_sfx_events
            )

            output_path = workspace / "audio_mix.m4a"
            args = [self._settings.ffmpeg_binary, "-y"]
            for input_path in inputs:
                args.extend(["-i", str(input_path)])
            args.extend(
                [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    f"[{output_label}]",
                    "-c:a",
                    audio_encoder_name(self._render_profile.audio_codec),
                    "-ar",
                    str(self._render_profile.audio_sample_rate),
                    str(output_path),
                ]
            )

            completed = self._run_subprocess(args, capture_output=True, timeout=timeout_seconds)
            if completed.returncode != 0:
                stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
                raise AudioMixError(f"audio mix failed (exit {completed.returncode}): {stderr}")
            return output_path.read_bytes()

    def _build_filter_complex(
        self,
        timeline: AudioTimeline,
        *,
        music_cues: list[MusicCue],
        sfx_events: list[SoundEffectEvent],
    ) -> tuple[str, str]:
        narration_input_index = 0
        chains: list[str] = []
        stream_labels: list[str] = []

        narration_volume_db = timeline.narration_segments[0].volume_db if timeline.narration_segments else 0.0
        if narration_volume_db:
            chains.append(f"[{narration_input_index}:a]volume={narration_volume_db}dB[narr]")
            stream_labels.append("narr")
        else:
            stream_labels.append(f"{narration_input_index}:a")

        next_input_index = narration_input_index + 1
        for i, cue in enumerate(music_cues):
            input_index = next_input_index + i
            raw_label = f"music_raw_{i}"
            filter_parts = [f"volume={cue.volume_db}dB"]
            if cue.fade_in_seconds > 0:
                filter_parts.append(f"afade=t=in:st=0:d={cue.fade_in_seconds}")
            if cue.fade_out_seconds > 0:
                fade_out_start = max(cue.duration_seconds - cue.fade_out_seconds, 0.0)
                filter_parts.append(f"afade=t=out:st={fade_out_start}:d={cue.fade_out_seconds}")
            delay_ms = round(cue.start_seconds * 1000)
            filter_parts.append(f"adelay={delay_ms}|{delay_ms}")
            chains.append(f"[{input_index}:a]" + ",".join(filter_parts) + f"[{raw_label}]")

            if cue.duck_under_narration:
                ducked_label = f"music_{i}"
                chains.append(
                    f"[{raw_label}][{narration_input_index}:a]sidechaincompress="
                    f"threshold=0.05:ratio=8:attack=5:release=200[{ducked_label}]"
                )
                stream_labels.append(ducked_label)
            else:
                stream_labels.append(raw_label)

        next_input_index += len(music_cues)
        for j, event in enumerate(sfx_events):
            input_index = next_input_index + j
            label = f"sfx_{j}"
            delay_ms = round(event.at_seconds * 1000)
            chains.append(f"[{input_index}:a]volume={event.volume_db}dB,adelay={delay_ms}|{delay_ms}[{label}]")
            stream_labels.append(label)

        if len(stream_labels) > 1:
            mix_inputs = "".join(f"[{label}]" for label in stream_labels)
            chains.append(f"{mix_inputs}amix=inputs={len(stream_labels)}:duration=first:dropout_transition=0[premix]")
            premix_label = "premix"
        else:
            premix_label = stream_labels[0]

        fade_out_start = max(timeline.total_duration_seconds - timeline.fade_out_seconds, 0.0)
        chains.append(
            f"[{premix_label}]afade=t=in:st=0:d={timeline.fade_in_seconds},"
            f"afade=t=out:st={fade_out_start}:d={timeline.fade_out_seconds},"
            f"loudnorm=I={timeline.master_loudness_lufs}:TP=-1.5:LRA=11[out]"
        )

        return ";".join(chains), "out"
