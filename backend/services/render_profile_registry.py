from __future__ import annotations

from backend.schemas.render_profile import (
    AudioCodec,
    BitrateStrategy,
    ContainerFormat,
    RenderProfile,
    TargetPlatform,
    VideoCodec,
)

DEFAULT_RENDER_PROFILE_NAME = "youtube_long"

# CRF 18 + a "medium" preset is the standard "visually lossless, still
# pipeline-speed-reasonable" choice for a single high-quality master file that
# YouTube will itself re-encode on ingest — exactly the "high-quality
# YouTube-appropriate encoder defaults" the brief asks for, without picking a
# preset slow enough to make routine production runs impractical.
YOUTUBE_LONG_PROFILE = RenderProfile(
    name=DEFAULT_RENDER_PROFILE_NAME,
    target_platform=TargetPlatform.YOUTUBE_LONG,
    width=1920,
    height=1080,
    aspect_ratio="16:9",
    frame_rate=30,
    video_codec=VideoCodec.H264,
    audio_codec=AudioCodec.AAC,
    audio_sample_rate=48000,
    bitrate_strategy=BitrateStrategy.CRF,
    crf=18,
    container=ContainerFormat.MP4,
    color_space="bt709",
    pixel_format="yuv420p",
    encoder_preset="medium",
)


class RenderProfileNotFoundError(KeyError):
    """Raised when a caller asks the registry for a profile name that was never
    registered — a config/typo problem, distinct from an invalid RenderProfile
    (which can't be constructed at all, see schemas/render_profile.py)."""


class RenderProfileRegistry:
    """Every RenderProfile a production could be rendered with. Adding a future
    platform (YouTube Shorts, TikTok, HEVC, ...) is registering one new
    RenderProfile here — no Renderer/exporter change required, per the brief's
    'configuration problem, not an architectural problem' goal."""

    def __init__(self) -> None:
        self._profiles: dict[str, RenderProfile] = {}

    def register(self, profile: RenderProfile) -> None:
        self._profiles[profile.name] = profile

    def get(self, name: str | None) -> RenderProfile:
        """Returns the named profile, or the default YouTube Long profile when
        `name` is None/empty — the concrete mechanism behind 'if no RenderProfile
        is specified, automatically select the default'."""
        resolved_name = name or DEFAULT_RENDER_PROFILE_NAME
        try:
            return self._profiles[resolved_name]
        except KeyError:
            raise RenderProfileNotFoundError(resolved_name) from None

    def list_profiles(self) -> list[RenderProfile]:
        return list(self._profiles.values())


def build_default_render_profile_registry() -> RenderProfileRegistry:
    registry = RenderProfileRegistry()
    registry.register(YOUTUBE_LONG_PROFILE)
    return registry
