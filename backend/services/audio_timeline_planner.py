from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.config import Settings
from backend.schemas.assets import ScenePlan, VoiceAsset
from backend.schemas.audio import AudioTimeline, MusicCue, NarrationSegment, SceneTransitionMarker, SoundEffectEvent
from backend.schemas.timeline import TimelinePlan


class AudioTimelinePlanner(ABC):
    """Resolves the final AudioTimeline — the single seam between audio planning
    ('what should happen, and when') and audio execution ('mix exactly that').
    F28 (AI Director) is expected to add an LLM-driven implementation of this
    interface later, keyed by the same scene_number as Shot; AudioMixerService only
    ever executes an AudioTimeline, so it needs no changes when that happens —
    mirrors ShotPlanner's relationship to RendererPipeline exactly."""

    @abstractmethod
    def plan(
        self,
        *,
        voice_asset: VoiceAsset,
        scene_plan: ScenePlan | None,
        music_source_path: str | None,
        sound_effect_paths_by_scene: dict[int, str],
        timeline_plan: TimelinePlan | None = None,
    ) -> AudioTimeline:
        """Returns the AudioTimeline to execute for one narration track.

        `timeline_plan` is additive (F27): when given and its scene set matches
        `scene_plan`, per-scene timing is read from it instead of being
        recalculated — TimelinePlan is the single source of truth for scene
        timing. When absent or mismatched, implementations fall back to their
        own proportional split, preserving backward compatibility."""


class DeterministicAudioTimelinePlanner(AudioTimelinePlanner):
    """F26 implementation: one full-length narration segment, one optional
    full-length ducked music cue when a track was selected, and one SFX event for
    each scene that resolved a match. Scene timing (scene_transitions/SFX
    placement) is read from `timeline_plan` when it's given and covers every
    scene in `scene_plan`; otherwise it falls back to evenly spacing scenes
    across the narration's real (measured) duration, exactly as before F27. No
    LLM call, zero added cost either way."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(
        self,
        *,
        voice_asset: VoiceAsset,
        scene_plan: ScenePlan | None,
        music_source_path: str | None,
        sound_effect_paths_by_scene: dict[int, str],
        timeline_plan: TimelinePlan | None = None,
    ) -> AudioTimeline:
        total = max(voice_asset.duration, 0.0)
        narration_segments = [NarrationSegment(start_seconds=0.0, duration_seconds=total, scene_number=None)]

        music_cues: list[MusicCue] = []
        if music_source_path and total > 0:
            fade = min(2.0, total / 4)
            music_cues.append(
                MusicCue(
                    start_seconds=0.0,
                    duration_seconds=total,
                    source_path=music_source_path,
                    volume_db=self._settings.audio_music_volume_db,
                    fade_in_seconds=fade,
                    fade_out_seconds=fade,
                    duck_under_narration=True,
                )
            )

        scenes = scene_plan.scenes if scene_plan is not None else []
        scene_count = len(scenes)
        use_timeline_plan = (
            timeline_plan is not None
            and scene_count > 0
            and all(timeline_plan.timing_for(scene.scene_number) is not None for scene in scenes)
        )

        sound_effect_events: list[SoundEffectEvent] = []
        scene_transitions: list[SceneTransitionMarker] = []
        if scene_count > 0 and total > 0:
            for scene in scenes:
                if use_timeline_plan:
                    timing = timeline_plan.timing_for(scene.scene_number)  # type: ignore[union-attr]
                    at_seconds = timing.start_seconds  # type: ignore[union-attr]
                else:
                    at_seconds = ((scene.scene_number - 1) / scene_count) * total
                scene_transitions.append(SceneTransitionMarker(scene_number=scene.scene_number, at_seconds=at_seconds))
                source_path = sound_effect_paths_by_scene.get(scene.scene_number)
                if source_path:
                    sound_effect_events.append(
                        SoundEffectEvent(at_seconds=at_seconds, source_path=source_path, scene_number=scene.scene_number)
                    )

        return AudioTimeline(
            total_duration_seconds=total,
            narration_segments=narration_segments,
            music_cues=music_cues,
            sound_effect_events=sound_effect_events,
            scene_transitions=scene_transitions,
            fade_in_seconds=self._settings.audio_master_fade_in_seconds,
            fade_out_seconds=self._settings.audio_master_fade_out_seconds,
            master_loudness_lufs=self._settings.audio_master_loudness_lufs,
        )
