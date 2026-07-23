from __future__ import annotations

import logging
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from backend.core.config import Settings
from backend.schemas.assets import ScenePlan, SceneImageSet, SubtitleAsset, VideoAsset, VoiceAsset
from backend.schemas.composition import CompositionPlan
from backend.schemas.render_profile import RenderProfile
from backend.services.cinematic_renderer_pipeline import CinematicRenderError, RendererPipeline
from backend.services.cinematic_shot_planner import ShotPlanner
from backend.services.composition_aware_shot_planner import CompositionAwareShotPlanner
from backend.services.render_profile_encoders import audio_encoder_name, video_bitrate_args, video_encoder_name
from backend.services.render_profile_registry import build_default_render_profile_registry

logger = logging.getLogger(__name__)

_DEFAULT_SCENE_SECONDS = 3.0
_FFMPEG_TIMEOUT_SECONDS = 300.0

SubprocessRunner = Callable[..., subprocess.CompletedProcess]


class VideoAssemblyService:
    """Composes the narration audio, per-scene images, and subtitles produced by earlier
    pipeline steps into a single playable .mp4 via `ffmpeg`. Tries the F25 cinematic
    renderer (camera movement + transitions via RendererPipeline) first; on any rendering
    failure it falls back to the plain slideshow assembly that shipped before F25. Never
    raises — ffmpeg/filesystem failures are captured as a FAILED VideoAsset so the workflow
    continues."""

    def __init__(
        self,
        settings: Settings,
        subprocess_runner: SubprocessRunner | None = None,
        shot_planner: ShotPlanner | None = None,
        renderer_pipeline: RendererPipeline | None = None,
        render_profile: RenderProfile | None = None,
    ) -> None:
        self._settings = settings
        self._run_subprocess = subprocess_runner or subprocess.run
        self._shot_planner = shot_planner or CompositionAwareShotPlanner(settings)
        self._render_profile = render_profile or build_default_render_profile_registry().get(settings.render_profile_name)
        self._renderer_pipeline = renderer_pipeline or RendererPipeline(
            settings, self._run_subprocess, render_profile=self._render_profile
        )

    async def execute(
        self,
        *,
        scene_image_set: SceneImageSet,
        image_bytes_by_filename: dict[str, bytes],
        voice_asset: VoiceAsset,
        audio_bytes: bytes | None,
        subtitle_asset: SubtitleAsset,
        subtitle_content: str,
        run_id: str,
        scene_plan: ScenePlan | None = None,
        composition_plan: CompositionPlan | None = None,
    ) -> tuple[VideoAsset, bytes | None]:
        # Positionally indexed (1..N), not looked up by scene_number: a scene with
        # F28B visual beats contributes multiple SceneImageAsset entries sharing
        # one scene_number, so scene_number can no longer serve as a unique key.
        # Every downstream consumer (ShotPlanner, RendererPipeline) already only
        # relies on list order/count, never on this int's value, so a synthetic
        # sequential index is a safe, purely-positional replacement.
        images = [
            (index, image_bytes_by_filename[image.filename])
            for index, image in enumerate(scene_image_set.images, start=1)
            if image.status == "SUCCESS" and image.filename in image_bytes_by_filename
        ]
        if not images:
            return self._skipped("No successfully generated scene images to assemble"), None

        scene_seconds = (
            voice_asset.duration / len(images)
            if voice_asset.status == "SUCCESS" and voice_asset.duration > 0
            else _DEFAULT_SCENE_SECONDS
        )
        use_audio = bool(audio_bytes) and voice_asset.status == "SUCCESS"
        use_subtitles = bool(subtitle_content) and subtitle_asset.status == "SUCCESS"

        started_at = datetime.now(timezone.utc)
        try:
            with tempfile.TemporaryDirectory(prefix="video_assembly_") as work_dir:
                workspace = Path(work_dir)
                asset, video_bytes = self._assemble(
                    workspace,
                    images,
                    scene_seconds,
                    audio_bytes if use_audio else None,
                    subtitle_content if use_subtitles else "",
                    started_at,
                    scene_plan,
                    composition_plan,
                )
            if asset.status == "SUCCESS" and video_bytes is not None:
                asset = self._persist(asset, video_bytes, run_id)
            return asset, video_bytes
        except FileNotFoundError as exc:
            logger.warning("video_assembly_ffmpeg_not_found", extra={"reason": str(exc)})
            return self._failed(f"ffmpeg binary not found: {exc}"), None
        except subprocess.TimeoutExpired as exc:
            logger.warning("video_assembly_timeout", extra={"reason": str(exc)})
            return self._failed(f"ffmpeg timed out: {exc}"), None
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("video_assembly_unexpected_failure")
            return self._failed(f"Unexpected video assembly failure: {exc}"), None

    def _assemble(
        self,
        workspace: Path,
        images: list[tuple[int, bytes]],
        scene_seconds: float,
        audio_bytes: bytes | None,
        subtitle_content: str,
        started_at: datetime,
        scene_plan: ScenePlan | None,
        composition_plan: CompositionPlan | None,
    ) -> tuple[VideoAsset, bytes | None]:
        audio_path: Path | None = None
        if audio_bytes:
            audio_path = workspace / "voice.mp3"
            audio_path.write_bytes(audio_bytes)

        subtitle_path: Path | None = None
        if subtitle_content:
            subtitle_path = workspace / "subtitles.srt"
            subtitle_path.write_text(subtitle_content, encoding="utf-8")

        if self._settings.cinematic_rendering_enabled:
            try:
                return self._assemble_cinematic(
                    workspace, images, scene_seconds, audio_path, subtitle_path, started_at, scene_plan, composition_plan
                )
            except (CinematicRenderError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
                logger.warning("video_assembly_cinematic_fallback", extra={"reason": str(exc)})

        return self._assemble_slideshow_fallback(workspace, images, scene_seconds, audio_path, subtitle_path, started_at)

    def _assemble_cinematic(
        self,
        workspace: Path,
        images: list[tuple[int, bytes]],
        scene_seconds: float,
        audio_path: Path | None,
        subtitle_path: Path | None,
        started_at: datetime,
        scene_plan: ScenePlan | None,
        composition_plan: CompositionPlan | None,
    ) -> tuple[VideoAsset, bytes | None]:
        scenes = scene_plan.scenes if scene_plan is not None else None
        shots = self._shot_planner.plan(
            scenes=scenes, image_count=len(images), scene_seconds=scene_seconds, composition_plan=composition_plan
        )
        rendered = self._renderer_pipeline.render(
            workspace=workspace,
            images=images,
            shots=shots,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            timeout_seconds=_FFMPEG_TIMEOUT_SECONDS,
        )
        video_bytes = rendered.output_path.read_bytes()
        finished_at = datetime.now(timezone.utc)

        # Sums each shot's own duration rather than assuming a uniform
        # scene_seconds — required once CompositionAwareShotPlanner can assign
        # variable per-scene durations (F27); still correct for the uniform
        # fallback case since every shot's duration_seconds equals scene_seconds
        # there.
        transition_seconds = self._settings.cinematic_transition_duration_seconds if len(shots) > 1 else 0.0
        duration = sum(shot.duration_seconds for shot in shots) - transition_seconds * max(len(shots) - 1, 0)

        asset = VideoAsset(
            provider="ffmpeg-cinematic",
            duration=duration,
            generation_time=finished_at.isoformat(),
            status="SUCCESS",
            generation_duration_ms=(finished_at - started_at).total_seconds() * 1000,
            scene_count=len(shots),
            estimated_cost_usd=0.0,
            render_mode="cinematic",
            camera_movements=[shot.camera_movement.value for shot in shots],
            transition=shots[1].transition.value if len(shots) > 1 else "",
            atmosphere_overlay=next((shot.atmosphere.value for shot in shots if shot.atmosphere is not None), None),
        )
        return asset, video_bytes

    def _assemble_slideshow_fallback(
        self,
        workspace: Path,
        images: list[tuple[int, bytes]],
        scene_seconds: float,
        audio_path: Path | None,
        subtitle_path: Path | None,
        started_at: datetime,
    ) -> tuple[VideoAsset, bytes | None]:
        concat_lines: list[str] = []
        for image_index, image_data in images:
            image_path = workspace / f"scene_{image_index:02d}.png"
            image_path.write_bytes(image_data)
            concat_lines.append(f"file '{image_path.name}'")
            concat_lines.append(f"duration {scene_seconds}")
        # ffmpeg's concat demuxer ignores the final entry's duration directive unless
        # the last image is repeated once more without one.
        last_image_name = f"scene_{images[-1][0]:02d}.png"
        concat_lines.append(f"file '{last_image_name}'")
        concat_list_path = workspace / "concat_list.txt"
        concat_list_path.write_text("\n".join(concat_lines), encoding="utf-8")

        args = [self._settings.ffmpeg_binary, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path)]

        if audio_path is not None:
            args.extend(["-i", str(audio_path)])

        if subtitle_path is not None:
            args.extend(["-i", str(subtitle_path)])

        args.extend(["-map", "0:v"])
        if audio_path is not None:
            args.extend(["-map", "1:a"])
        if subtitle_path is not None:
            subtitle_input_index = 2 if audio_path is not None else 1
            args.extend(["-map", f"{subtitle_input_index}:s"])

        profile = self._render_profile
        args.extend(["-c:v", video_encoder_name(profile.video_codec), "-preset", profile.encoder_preset])
        args.extend(video_bitrate_args(profile))
        args.extend(["-pix_fmt", profile.pixel_format, "-colorspace", profile.color_space, "-r", str(profile.frame_rate)])
        if audio_path is not None:
            args.extend(["-c:a", audio_encoder_name(profile.audio_codec), "-ar", str(profile.audio_sample_rate)])
        if subtitle_path is not None:
            args.extend(["-c:s", "mov_text"])
        args.append("-shortest")

        output_path = workspace / f"video.{profile.container.value}"
        args.append(str(output_path))

        completed = self._run_subprocess(args, capture_output=True, timeout=_FFMPEG_TIMEOUT_SECONDS)
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
            return self._failed(f"ffmpeg exited with code {completed.returncode}: {stderr}"), None

        video_bytes = output_path.read_bytes()
        finished_at = datetime.now(timezone.utc)
        asset = VideoAsset(
            provider="ffmpeg-local",
            duration=scene_seconds * len(images),
            generation_time=finished_at.isoformat(),
            status="SUCCESS",
            generation_duration_ms=(finished_at - started_at).total_seconds() * 1000,
            scene_count=len(images),
            estimated_cost_usd=0.0,
            render_mode="slideshow",
        )
        return asset, video_bytes

    def _persist(self, asset: VideoAsset, video_bytes: bytes, run_id: str) -> VideoAsset:
        run_dir = Path(self._settings.run_storage_root) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        video_path = run_dir / asset.filename
        video_path.write_bytes(video_bytes)
        absolute_path = str(video_path.resolve())
        logger.info("Saved final video:\n%s", absolute_path)
        return asset.model_copy(update={"file_path": absolute_path})

    def _skipped(self, reason: str) -> VideoAsset:
        return VideoAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error=reason,
        )

    def _failed(self, reason: str) -> VideoAsset:
        return VideoAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="FAILED",
            error=reason,
        )
