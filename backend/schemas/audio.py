from __future__ import annotations

from pydantic import BaseModel, Field

from backend.schemas.assets import AssetStatus


class VoiceProfile(BaseModel):
    """A reusable, named narration style. Adding a profile is adding a registry
    entry (see backend/services/voice_profiles.py) — no code path changes required."""

    key: str = Field(description="Stable identifier, e.g. 'documentary_male'")
    display_name: str = Field(description="Human-readable profile name")
    model: str = Field(description="TTS model to use for this profile")
    voice: str = Field(description="TTS voice id to use for this profile")
    instructions: str = Field(description="Base natural-language delivery direction")
    pace: float = Field(default=1.0, description="Default speed multiplier for this profile")


class VoiceDirection(BaseModel):
    """Directs HOW narration should be delivered. Produced today by a deterministic
    profile lookup (VoiceDirectionPlanner); F28's AI Director is expected to produce
    richer, per-scene VoiceDirection later with no change to VoiceGenerationService
    or TextToSpeechProvider — the same seam Shot already gives the video renderer."""

    profile: str = Field(description="VoiceProfile key this direction was derived from")
    model: str = Field(description="TTS model to use")
    voice: str = Field(description="TTS voice id to use")
    pace: float = Field(default=1.0, description="Speed multiplier passed to the TTS provider")
    instructions: str = Field(default="", description="Natural-language delivery direction sent to the TTS provider")


class NarrationSegment(BaseModel):
    """One placed span of the processed narration track on the timeline. Multiple
    segments (with gaps between them) are how the timeline represents silence —
    no separate 'silence' type is needed."""

    start_seconds: float = Field(default=0.0, description="Segment start on the mixed timeline")
    duration_seconds: float = Field(default=0.0, description="Segment length in seconds")
    scene_number: int | None = Field(default=None, description="Matching Scene.scene_number, when known")
    volume_db: float = Field(default=0.0, description="Gain applied to this segment, in dB")


class MusicCue(BaseModel):
    """One placed background-music span. `duck_under_narration` is a future-proof
    seam for a volume-automation curve (a list of (time, db) points) — not needed
    while ducking is a single on/off decision for the whole cue."""

    start_seconds: float = Field(default=0.0, description="Cue start on the mixed timeline")
    duration_seconds: float = Field(default=0.0, description="Cue length in seconds")
    source_path: str = Field(description="Path to the selected music asset on disk")
    volume_db: float = Field(default=-18.0, description="Base gain applied to this cue, in dB")
    fade_in_seconds: float = Field(default=0.0, description="Cue-local fade-in length")
    fade_out_seconds: float = Field(default=0.0, description="Cue-local fade-out length")
    duck_under_narration: bool = Field(default=True, description="Attenuate this cue while narration is present")


class SoundEffectEvent(BaseModel):
    """One instantaneous/short sound-effect placement, keyed to the scene it
    illustrates so future direction can stay in sync with Shot's scene_number."""

    at_seconds: float = Field(default=0.0, description="Playback position on the mixed timeline")
    source_path: str = Field(description="Path to the selected sound-effect asset on disk")
    scene_number: int | None = Field(default=None, description="Matching Scene.scene_number, when known")
    volume_db: float = Field(default=0.0, description="Gain applied to this event, in dB")


class SceneTransitionMarker(BaseModel):
    """Marks where one scene's audio hands off to the next. Reserved for future
    per-scene ducking/SFX timing refinement; AudioMixerService does not consume this
    yet, but it is populated today so a future consumer needs no new data."""

    scene_number: int = Field(description="Matching Scene.scene_number")
    at_seconds: float = Field(description="Transition point on the mixed timeline")


class AudioTimeline(BaseModel):
    """The data contract between audio planning ('what should happen, and when') and
    audio execution ('mix exactly that'). This is Shot's counterpart for audio
    (see backend/schemas/shots.py): AudioTimelinePlanner resolves it deterministically
    today; F28's AI Director is expected to produce AudioTimelines directly later,
    keyed by the same scene_number as Shot. AudioMixerService executes whatever
    timeline it is given and never makes a creative decision itself — same
    discipline F25's RendererPipeline applies to Shot."""

    total_duration_seconds: float = Field(default=0.0, description="Total length of the final mixed track")
    narration_segments: list[NarrationSegment] = Field(default_factory=list, description="Ordered narration placements")
    music_cues: list[MusicCue] = Field(default_factory=list, description="Background-music placements; empty is valid")
    sound_effect_events: list[SoundEffectEvent] = Field(default_factory=list, description="SFX placements; empty is valid")
    scene_transitions: list[SceneTransitionMarker] = Field(
        default_factory=list, description="Scene handoff points, reserved for future use"
    )
    fade_in_seconds: float = Field(default=1.0, description="Master fade-in at the start of the mix")
    fade_out_seconds: float = Field(default=2.0, description="Master fade-out at the end of the mix")
    master_loudness_lufs: float = Field(default=-14.0, description="Target integrated loudness (YouTube norm)")


class AudioAsset(BaseModel):
    """Metadata for the final mixed/mastered audio track produced by AudioMixerService."""

    provider: str = Field(default="ffmpeg-audio-mixer", description="Tool that produced the mix")
    duration: float = Field(default=0.0, description="Duration of the mixed track in seconds")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="audio_mix.m4a", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock ffmpeg call duration in milliseconds")
    music_included: bool = Field(default=False, description="Whether a music cue was mixed in")
    sound_effect_count: int = Field(default=0, description="Number of sound-effect events mixed in")
    master_loudness_lufs: float = Field(default=-14.0, description="Target integrated loudness applied")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost of this mixing pass (always 0 — local ffmpeg only)")
