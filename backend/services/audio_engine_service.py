from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.core.config import Settings
from backend.schemas.assets import MusicPlan, ScenePlan, VoiceAsset
from backend.schemas.audio import AudioAsset
from backend.schemas.timeline import TimelinePlan
from backend.services.audio_mixer_service import AudioMixError, AudioMixerService
from backend.services.audio_timeline_planner import AudioTimelinePlanner, DeterministicAudioTimelinePlanner
from backend.services.music_generation_provider import MusicGenerationProvider
from backend.services.sound_effect_provider import SoundEffectProvider

logger = logging.getLogger(__name__)

_MIX_TIMEOUT_SECONDS = 120.0


class AudioEngineService:
    """Builds the final mixed/mastered narration track: resolves optional
    background music and sound effects, plans an AudioTimeline, and executes it via
    AudioMixerService. Never raises — mixing failure or disabled configuration
    returns a non-SUCCESS AudioAsset with no bytes, and the workflow falls back to
    muxing the raw (normalized) narration track untouched, exactly like cinematic
    rendering falls back to the legacy slideshow renderer."""

    def __init__(
        self,
        settings: Settings,
        music_provider: MusicGenerationProvider,
        sound_effect_provider: SoundEffectProvider,
        timeline_planner: AudioTimelinePlanner | None = None,
        mixer: AudioMixerService | None = None,
    ) -> None:
        self._settings = settings
        self._music_provider = music_provider
        self._sound_effect_provider = sound_effect_provider
        self._timeline_planner = timeline_planner or DeterministicAudioTimelinePlanner(settings)
        self._mixer = mixer or AudioMixerService(settings)

    async def execute(
        self,
        *,
        voice_asset: VoiceAsset,
        narration_bytes: bytes | None,
        music_plan: MusicPlan | None,
        scene_plan: ScenePlan | None,
        timeline_plan: TimelinePlan | None = None,
    ) -> tuple[AudioAsset, bytes | None]:
        if not narration_bytes or voice_asset.status != "SUCCESS":
            return self._skipped("No narration available to mix"), None
        if not self._settings.audio_engine_enabled:
            return self._skipped("Audio engine disabled by configuration"), None

        started_at = datetime.now(timezone.utc)

        music_source_path, music_bytes = await self._resolve_music(music_plan, voice_asset.duration)
        sound_effect_paths_by_scene, sound_effect_bytes = await self._resolve_sound_effects(scene_plan)

        timeline = self._timeline_planner.plan(
            voice_asset=voice_asset,
            scene_plan=scene_plan,
            music_source_path=music_source_path,
            sound_effect_paths_by_scene=sound_effect_paths_by_scene,
            timeline_plan=timeline_plan,
        )

        try:
            mixed_bytes = self._mixer.mix(
                narration_bytes=narration_bytes,
                timeline=timeline,
                music_bytes=music_bytes,
                sound_effect_bytes=sound_effect_bytes,
                timeout_seconds=_MIX_TIMEOUT_SECONDS,
            )
        except (AudioMixError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("audio_engine_mix_failed", extra={"reason": str(exc)})
            return self._failed(str(exc)), None
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("audio_engine_unexpected_failure")
            return self._failed(f"Unexpected audio mixing failure: {exc}"), None

        finished_at = datetime.now(timezone.utc)
        asset = AudioAsset(
            duration=timeline.total_duration_seconds,
            generation_time=finished_at.isoformat(),
            status="SUCCESS",
            generation_duration_ms=(finished_at - started_at).total_seconds() * 1000,
            music_included=bool(music_source_path),
            sound_effect_count=len(sound_effect_paths_by_scene),
            master_loudness_lufs=timeline.master_loudness_lufs,
        )
        return asset, mixed_bytes

    async def _resolve_music(self, music_plan: MusicPlan | None, duration: float) -> tuple[str | None, dict[str, bytes]]:
        if not self._settings.background_music_enabled or music_plan is None:
            return None, {}
        direction = (music_plan.reference or f"{music_plan.genre} {music_plan.mood}").strip()
        if not direction:
            return None, {}
        media_asset = await self._music_provider.generate_music(prompt=direction, duration=duration)
        if media_asset.metadata.get("status") != "SUCCESS" or not media_asset.source:
            return None, {}
        try:
            return media_asset.source, {media_asset.source: Path(media_asset.source).read_bytes()}
        except OSError as exc:
            logger.warning("audio_engine_music_read_failed", extra={"reason": str(exc)})
            return None, {}

    async def _resolve_sound_effects(self, scene_plan: ScenePlan | None) -> tuple[dict[int, str], dict[str, bytes]]:
        paths_by_scene: dict[int, str] = {}
        bytes_by_path: dict[str, bytes] = {}
        if not self._settings.sound_effects_enabled or scene_plan is None:
            return paths_by_scene, bytes_by_path

        for scene in scene_plan.scenes:
            keywords = f"{scene.environment} {scene.animation}".strip()
            if not keywords:
                continue
            media_asset = await self._sound_effect_provider.get_sound_effect(keywords=keywords)
            if media_asset.metadata.get("status") != "SUCCESS" or not media_asset.source:
                continue
            try:
                bytes_by_path[media_asset.source] = Path(media_asset.source).read_bytes()
                paths_by_scene[scene.scene_number] = media_asset.source
            except OSError as exc:
                logger.warning("audio_engine_sfx_read_failed", extra={"reason": str(exc)})
        return paths_by_scene, bytes_by_path

    def _skipped(self, reason: str) -> AudioAsset:
        return AudioAsset(generation_time=datetime.now(timezone.utc).isoformat(), status="SKIPPED", error=reason)

    def _failed(self, reason: str) -> AudioAsset:
        return AudioAsset(generation_time=datetime.now(timezone.utc).isoformat(), status="FAILED", error=reason)
