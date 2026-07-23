from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from backend.core.config import Settings
from backend.schemas.render_profile import RenderProfile
from backend.schemas.shots import Shot
from backend.services.cinematic_atmosphere_overlay import build_atmosphere_filter
from backend.services.cinematic_camera_movement import build_camera_movement_filter
from backend.services.cinematic_color_processing import ColorProcessing
from backend.services.cinematic_transition import build_transition_chain
from backend.services.render_profile_encoders import audio_encoder_name, video_bitrate_args, video_encoder_name
from backend.services.render_profile_registry import build_default_render_profile_registry

SubprocessRunner = Callable[..., subprocess.CompletedProcess]


@dataclass
class RenderedVideo:
    output_path: Path
    shots_used: list[Shot]


class CinematicRenderError(RuntimeError):
    """Raised when a cinematic-rendering ffmpeg call fails; callers fall back to the
    legacy slideshow path on this exception."""


class RendererPipeline:
    """Executes a list of Shots against a list of scene images to produce one cinematic
    video clip (no audio/subtitles yet — those are muxed in by the final compose call).
    Never chooses effects itself — every creative decision comes from the Shot it's given,
    so a future Shot source (e.g. F28's AI Director) requires no changes here."""

    def __init__(
        self,
        settings: Settings,
        subprocess_runner: SubprocessRunner | None = None,
        render_profile: RenderProfile | None = None,
    ) -> None:
        self._settings = settings
        self._run_subprocess = subprocess_runner or subprocess.run
        self._render_profile = render_profile or build_default_render_profile_registry().get(settings.render_profile_name)

    def render(
        self,
        *,
        workspace: Path,
        images: list[tuple[int, bytes]],
        shots: list[Shot],
        audio_path: Path | None,
        subtitle_path: Path | None,
        timeout_seconds: float,
    ) -> RenderedVideo:
        if len(images) != len(shots):
            raise ValueError("images and shots must be the same length")

        profile = self._render_profile
        clip_paths = [
            self._render_scene_clip(workspace, scene_number, image_bytes, shot, profile, timeout_seconds)
            for (scene_number, image_bytes), shot in zip(images, shots)
        ]

        output_path = workspace / f"video.{profile.container.value}"
        self._compose(clip_paths, shots, audio_path, subtitle_path, output_path, timeout_seconds)
        return RenderedVideo(output_path=output_path, shots_used=shots)

    def _render_scene_clip(
        self,
        workspace: Path,
        scene_number: int,
        image_bytes: bytes,
        shot: Shot,
        profile: RenderProfile,
        timeout_seconds: float,
    ) -> Path:
        image_path = workspace / f"scene_{scene_number:02d}.png"
        image_path.write_bytes(image_bytes)

        frame_count = max(round(shot.duration_seconds * profile.frame_rate), 1)
        filters = [
            build_camera_movement_filter(
                shot.camera_movement, frame_count=frame_count, fps=profile.frame_rate, out_w=profile.width, out_h=profile.height
            )
        ]
        if shot.atmosphere is not None:
            filters.append(build_atmosphere_filter(shot.atmosphere))
        filters.append(ColorProcessing.for_profile(shot.color_profile).build_filter())

        clip_path = workspace / f"clip_{scene_number:02d}.mp4"
        args = [
            self._settings.ffmpeg_binary,
            "-y",
            "-i",
            str(image_path),
            "-vf",
            ",".join(filters),
            "-frames:v",
            str(frame_count),
            "-r",
            str(profile.frame_rate),
            "-pix_fmt",
            profile.pixel_format,
            "-an",
            str(clip_path),
        ]
        completed = self._run_subprocess(args, capture_output=True, timeout=timeout_seconds)
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
            raise CinematicRenderError(f"scene {scene_number} clip render failed (exit {completed.returncode}): {stderr}")
        return clip_path

    def _compose(
        self,
        clip_paths: list[Path],
        shots: list[Shot],
        audio_path: Path | None,
        subtitle_path: Path | None,
        output_path: Path,
        timeout_seconds: float,
    ) -> None:
        profile = self._render_profile
        args = [self._settings.ffmpeg_binary, "-y"]
        for clip_path in clip_paths:
            args.extend(["-i", str(clip_path)])

        audio_input_index = len(clip_paths) if audio_path is not None else None
        if audio_path is not None:
            args.extend(["-i", str(audio_path)])
        subtitle_input_index = None
        if subtitle_path is not None:
            subtitle_input_index = len(clip_paths) + (1 if audio_path is not None else 0)
            args.extend(["-i", str(subtitle_path)])

        if len(clip_paths) >= 2:
            filter_complex, video_label = build_transition_chain(
                clip_durations=[shot.duration_seconds for shot in shots],
                transitions=[shot.transition for shot in shots],
                duration_seconds=self._settings.cinematic_transition_duration_seconds,
            )
            args.extend(["-filter_complex", filter_complex, "-map", f"[{video_label}]"])
        else:
            args.extend(["-map", "0:v"])

        if audio_input_index is not None:
            args.extend(["-map", f"{audio_input_index}:a"])
        if subtitle_input_index is not None:
            args.extend(["-map", f"{subtitle_input_index}:s"])

        args.extend(["-c:v", video_encoder_name(profile.video_codec), "-preset", profile.encoder_preset])
        args.extend(video_bitrate_args(profile))
        args.extend(["-pix_fmt", profile.pixel_format, "-colorspace", profile.color_space, "-r", str(profile.frame_rate)])
        if audio_input_index is not None:
            args.extend(["-c:a", audio_encoder_name(profile.audio_codec), "-ar", str(profile.audio_sample_rate)])
        if subtitle_input_index is not None:
            args.extend(["-c:s", "mov_text"])
        args.extend(["-shortest", str(output_path)])

        completed = self._run_subprocess(args, capture_output=True, timeout=timeout_seconds)
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
            raise CinematicRenderError(f"final compose failed (exit {completed.returncode}): {stderr}")
