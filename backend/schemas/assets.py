from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AssetStatus = Literal["SUCCESS", "FAILED", "SKIPPED"]


class VoiceAsset(BaseModel):
    """Metadata for a generated narration voice-over track."""

    provider: str = Field(description="Provider that generated the voice track")
    model: str = Field(default="", description="Provider model identifier used")
    voice: str = Field(default="", description="Voice preset used")
    voice_profile: str = Field(default="", description="VoiceProfile key the VoiceDirection was derived from")
    language: str = Field(default="en", description="Narration language")
    duration: float = Field(default=0.0, description="Estimated audio duration in seconds")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="voice.mp3", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock provider call duration in milliseconds")
    retry_count: int = Field(default=0, description="Number of retry attempts made before success")
    estimated_input_tokens: int = Field(default=0, description="Estimated input tokens/characters billed")
    estimated_output_tokens: int = Field(default=0, description="Estimated output tokens billed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost of this generation")


class ImageAsset(BaseModel):
    """Metadata for a generated thumbnail image."""

    provider: str = Field(description="Provider that generated the image")
    model: str = Field(default="", description="Provider model identifier used")
    resolution: str = Field(default="", description="Generated image resolution, e.g. 1024x1024")
    prompt: str = Field(default="", description="Prompt used for generation")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="thumbnail.png", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock provider call duration in milliseconds")
    retry_count: int = Field(default=0, description="Number of retry attempts made before success")
    estimated_input_tokens: int = Field(default=0, description="Estimated input tokens/characters billed")
    estimated_output_tokens: int = Field(default=0, description="Estimated output tokens billed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost of this generation")
    validation_status: str = Field(
        default="not_validated", description="F31 Image Validation outcome: not_validated, valid, invalid, or unavailable"
    )
    validation_issues: list[str] = Field(default_factory=list, description="F31: defects ImageValidationService detected, if any")


class SceneImageAsset(BaseModel):
    """Metadata for one generated per-scene production image."""

    scene_number: int = Field(description="Matching Scene.scene_number")
    beat_number: int = Field(
        default=0, description="1-based visual beat index within the scene (F28B); 0 means no beat, single image"
    )
    provider: str = Field(description="Provider that generated the image")
    model: str = Field(default="", description="Provider model identifier used")
    resolution: str = Field(default="", description="Generated image resolution, e.g. 1024x1024")
    prompt: str = Field(default="", description="Prompt used for generation")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock provider call duration in milliseconds")
    retry_count: int = Field(default=0, description="Number of retry attempts made before success")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost of this generation")
    validation_status: str = Field(
        default="not_validated", description="F31 Image Validation outcome: not_validated, valid, invalid, or unavailable"
    )
    validation_issues: list[str] = Field(default_factory=list, description="F31: defects ImageValidationService detected, if any")
    character_name: str = Field(default="", description="F31: name of the CharacterVisualIdentity matched to this beat, if any")


class SceneImageSet(BaseModel):
    """Per-scene generated production images for one run."""

    topic: str = Field(description="Original topic")
    images: list[SceneImageAsset] = Field(default_factory=list, description="Ordered per-scene generated images")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class TranscriptAsset(BaseModel):
    """Metadata for a speech-to-text transcription (platform capability, not wired
    into the YouTube production workflow — reserved for future forced-alignment use)."""

    provider: str = Field(description="Provider that produced the transcript")
    model: str = Field(default="", description="Provider model identifier used")
    language: str = Field(default="", description="Detected or requested language")
    text: str = Field(default="", description="Transcribed text")
    generation_time: str = Field(description="ISO timestamp of generation")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")


class SubtitleAsset(BaseModel):
    """Metadata for a generated subtitle track."""

    provider: str = Field(default="generated", description="Subtitle generation source")
    format: str = Field(default="srt", description="Subtitle file format")
    cue_count: int = Field(default=0, description="Number of subtitle cues produced")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="subtitles.srt", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")


class VideoAsset(BaseModel):
    """Metadata for the assembled slideshow video composed from scene images, narration
    audio, and subtitles."""

    provider: str = Field(description="Tool that assembled the video")
    duration: float = Field(default=0.0, description="Estimated video duration in seconds")
    resolution: str = Field(default="", description="Rendered video resolution, e.g. 1024x1024")
    generation_time: str = Field(description="ISO timestamp of generation")
    filename: str = Field(default="video.mp4", description="Exported filename")
    status: AssetStatus = Field(default="SUCCESS", description="Generation outcome")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock ffmpeg call duration in milliseconds")
    scene_count: int = Field(default=0, description="Number of scene images composed into the video")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost of this generation")
    file_path: str | None = Field(
        default=None, description="Absolute path of the persisted video file on disk, e.g. storage/runs/<run_id>/video.mp4"
    )
    render_mode: str = Field(
        default="slideshow", description="'cinematic' when the F25 renderer succeeded, 'slideshow' for the legacy fallback"
    )
    camera_movements: list[str] = Field(
        default_factory=list, description="CameraMovementType value used for each scene, in scene order"
    )
    transition: str = Field(default="", description="TransitionType value used between shots, when render_mode is cinematic")
    atmosphere_overlay: str | None = Field(
        default=None, description="AtmosphereOverlayType value applied, when one was instructed"
    )


class Scene(BaseModel):
    """One shot/beat in the production scene breakdown."""

    scene_number: int = Field(description="1-based scene order")
    start_time: str = Field(default="", description="Estimated start timestamp mm:ss")
    end_time: str = Field(default="", description="Estimated end timestamp mm:ss")
    narration: str = Field(default="", description="Narration excerpt covered by this scene")
    camera: str = Field(default="", description="Camera framing/movement")
    lens: str = Field(default="", description="Lens or focal-length notes")
    lighting: str = Field(default="", description="Lighting direction")
    environment: str = Field(default="", description="Setting/environment description")
    animation: str = Field(default="", description="Animation/motion notes")
    composition: str = Field(default="", description="Shot composition notes")
    visual_prompt: str = Field(default="", description="Image-generation prompt for this scene")


class ScenePlan(BaseModel):
    """Full scene-by-scene production breakdown for a script."""

    topic: str = Field(description="Original topic")
    scenes: list[Scene] = Field(default_factory=list, description="Ordered scene breakdown")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class ScenePrompt(BaseModel):
    """Image-generation prompt parameters for one scene (or one visual beat within
    it — F28B). Multiple ScenePrompt entries may share the same scene_number when
    the scene has more than one visual beat; beat_number disambiguates them."""

    scene_number: int = Field(description="Matching Scene.scene_number")
    beat_number: int = Field(
        default=0, description="1-based visual beat index within the scene (F28B); 0 means no beat, single prompt"
    )
    prompt: str = Field(default="", description="Positive image-generation prompt")
    negative_prompt: str = Field(default="", description="Negative image-generation prompt")
    style: str = Field(default="", description="Visual style descriptor")
    aspect_ratio: str = Field(default="", description="Target aspect ratio, e.g. 16:9")
    camera: str = Field(default="", description="Camera framing/movement")
    mood: str = Field(default="", description="Emotional mood/tone")


class ScenePromptSet(BaseModel):
    """Per-scene image-generation prompts derived from the scene plan."""

    topic: str = Field(description="Original topic")
    prompts: list[ScenePrompt] = Field(default_factory=list, description="Ordered scene prompts")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class BrollSegment(BaseModel):
    """One B-roll footage suggestion mapped to a narration range."""

    narration_range: str = Field(default="", description="Narration span this segment covers")
    footage_description: str = Field(default="", description="Suggested B-roll footage")
    camera_motion: str = Field(default="", description="Suggested camera motion")
    transition: str = Field(default="", description="Suggested transition in/out")
    duration: str = Field(default="", description="Suggested segment duration")


class BrollPlan(BaseModel):
    """B-roll plan for a production, derived from the media package."""

    topic: str = Field(description="Original topic")
    segments: list[BrollSegment] = Field(default_factory=list, description="Ordered B-roll segments")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class MusicPlan(BaseModel):
    """Music direction for a production. Documents intent only — no music is generated."""

    genre: str = Field(default="", description="Suggested musical genre")
    mood: str = Field(default="", description="Suggested musical mood")
    tempo: str = Field(default="", description="Suggested tempo")
    energy: str = Field(default="", description="Suggested energy level")
    reference: str = Field(default="", description="Freeform music direction notes")
    metadata: dict[str, object] = Field(default_factory=dict, description="Execution metadata including status")


class AssetManifestEntry(BaseModel):
    """One tracked asset in the final asset manifest."""

    asset_type: str = Field(description="Kind of asset, e.g. voice, thumbnail, subtitle, document")
    provider: str = Field(default="", description="Provider or service that produced the asset")
    status: AssetStatus = Field(description="Generation outcome")
    duration: float | None = Field(default=None, description="Duration in seconds, when applicable")
    path: str = Field(description="Filename relative to the export folder")
    timestamp: str = Field(description="ISO timestamp of generation")
    hash: str = Field(default="", description="SHA-256 hex digest of the asset content")
    error: str | None = Field(default=None, description="Failure reason when status is FAILED")
    model: str = Field(default="", description="Provider model identifier used")
    generation_duration_ms: float = Field(default=0.0, description="Wall-clock provider call duration in milliseconds")
    retry_count: int = Field(default=0, description="Number of retry attempts made before success")
    size_bytes: int | None = Field(default=None, description="File size in bytes, populated at export time")
    created_at: str | None = Field(default=None, description="ISO file creation timestamp, populated at export time")
    last_modified_at: str | None = Field(
        default=None, description="ISO file last-modified timestamp, populated at export time"
    )


class AssetManifest(BaseModel):
    """Full inventory of every asset generated for one workflow execution."""

    execution_id: str = Field(description="Owning workflow execution id")
    entries: list[AssetManifestEntry] = Field(default_factory=list, description="Tracked assets")
    total_estimated_cost_usd: float = Field(
        default=0.0, description="F3: sum of every step's real reported cost (context.cost_ledger), including image validation and regeneration"
    )
    maximum_video_budget_usd: float = Field(default=0.0, description="F3: the runtime ceiling this run was enforced against")
    budget_status: str = Field(
        default="within_budget", description="F3: 'within_budget' or 'exceeded' — computed from total_estimated_cost_usd vs maximum_video_budget_usd"
    )
