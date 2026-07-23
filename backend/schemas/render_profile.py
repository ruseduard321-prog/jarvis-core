from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Sample rates ffmpeg/every target platform below actually expects. Rejecting
# anything else here is what makes "reject invalid combinations" concrete rather
# than aspirational.
_VALID_SAMPLE_RATES = {44100, 48000, 96000}


class TargetPlatform(str, Enum):
    """Descriptive label for what a RenderProfile is tuned for. Purely metadata —
    it never drives creative decisions (that remains CompositionPlan's job) and
    the Renderer never branches on it directly; it only ever reads the concrete
    technical fields below. Adding a platform is adding a member here plus one
    registry entry (see render_profile_registry.py) — no Renderer change."""

    YOUTUBE_LONG = "youtube_long"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_4K = "youtube_4k"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"


class VideoCodec(str, Enum):
    H264 = "h264"
    HEVC = "hevc"
    VP9 = "vp9"
    AV1 = "av1"


class AudioCodec(str, Enum):
    AAC = "aac"
    OPUS = "opus"
    MP3 = "mp3"


class ContainerFormat(str, Enum):
    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"


class BitrateStrategy(str, Enum):
    """How the encoder is told to spend bits. CRF (constant rate factor) is a
    quality target, not a bitrate target — the recommended choice for a single
    high-quality master file like this pipeline produces. CBR/VBR are provided
    for future platforms with a hard bitrate ceiling (e.g. live/streaming-style
    delivery constraints)."""

    CRF = "crf"
    CBR = "cbr"
    VBR = "vbr"


class RenderProfile(BaseModel):
    """The single source of truth for every technical rendering/export parameter.
    Defines HOW the finished video is encoded — resolution, codecs, container,
    color/pixel format, encoder preset — and nothing about WHAT the video shows
    or WHY (that is TimelinePlan/CompositionPlan/Shot/AudioTimeline's job, all
    unchanged by this schema). RendererPipeline, VideoAssemblyService, and
    AudioMixerService execute whatever RenderProfile they are given; none of them
    may hardcode a technical value RenderProfile already defines.

    `validate_assignment=True` so mutating a constructed profile re-runs
    validation too — a RenderProfile can never exist in an invalid state, which
    is what makes 'validate before rendering starts' true by construction rather
    than a separate step callers could forget to run."""

    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(description="Stable registry key, e.g. 'youtube_long'")
    target_platform: TargetPlatform

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    aspect_ratio: str = Field(description="e.g. '16:9' — must match width/height within tolerance")
    frame_rate: int = Field(gt=0, le=120)

    video_codec: VideoCodec
    audio_codec: AudioCodec
    audio_sample_rate: int = Field(description="Hz, e.g. 48000")

    bitrate_strategy: BitrateStrategy
    crf: int | None = Field(default=None, ge=0, le=51, description="Required when bitrate_strategy is CRF")
    video_bitrate_kbps: int | None = Field(default=None, gt=0, description="Required when bitrate_strategy is CBR/VBR")

    container: ContainerFormat
    color_space: str = Field(default="bt709", description="ffmpeg -colorspace value")
    pixel_format: str = Field(default="yuv420p", description="ffmpeg -pix_fmt value")
    encoder_preset: str = Field(default="medium", description="ffmpeg -preset value")

    @model_validator(mode="after")
    def _validate_combination(self) -> "RenderProfile":
        if self.audio_sample_rate not in _VALID_SAMPLE_RATES:
            raise ValueError(
                f"audio_sample_rate {self.audio_sample_rate} is not one of the supported rates {sorted(_VALID_SAMPLE_RATES)}"
            )

        if self.bitrate_strategy == BitrateStrategy.CRF and self.crf is None:
            raise ValueError("crf is required when bitrate_strategy is 'crf'")
        if self.bitrate_strategy in (BitrateStrategy.CBR, BitrateStrategy.VBR) and self.video_bitrate_kbps is None:
            raise ValueError(f"video_bitrate_kbps is required when bitrate_strategy is '{self.bitrate_strategy.value}'")

        try:
            ratio_w, ratio_h = (float(part) for part in self.aspect_ratio.split(":"))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"aspect_ratio '{self.aspect_ratio}' must be in 'W:H' form, e.g. '16:9'") from exc
        if ratio_w <= 0 or ratio_h <= 0:
            raise ValueError(f"aspect_ratio '{self.aspect_ratio}' must have positive components")

        declared_ratio = ratio_w / ratio_h
        actual_ratio = self.width / self.height
        if abs(declared_ratio - actual_ratio) > 0.01:
            raise ValueError(
                f"aspect_ratio '{self.aspect_ratio}' ({declared_ratio:.4f}) does not match "
                f"width/height {self.width}x{self.height} ({actual_ratio:.4f})"
            )

        return self
