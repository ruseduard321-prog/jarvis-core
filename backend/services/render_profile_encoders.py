from __future__ import annotations

from backend.schemas.render_profile import AudioCodec, BitrateStrategy, RenderProfile, VideoCodec

# The only place RenderProfile's portable codec enums are translated into
# ffmpeg-specific encoder names. Adding a codec is one new enum member (schema)
# plus one new entry here — no caller (RendererPipeline, VideoAssemblyService,
# AudioMixerService) ever needs to know an ffmpeg encoder name directly.
_VIDEO_ENCODERS: dict[VideoCodec, str] = {
    VideoCodec.H264: "libx264",
    VideoCodec.HEVC: "libx265",
    VideoCodec.VP9: "libvpx-vp9",
    VideoCodec.AV1: "libaom-av1",
}

_AUDIO_ENCODERS: dict[AudioCodec, str] = {
    AudioCodec.AAC: "aac",
    AudioCodec.OPUS: "libopus",
    AudioCodec.MP3: "libmp3lame",
}


def video_encoder_name(codec: VideoCodec) -> str:
    return _VIDEO_ENCODERS[codec]


def audio_encoder_name(codec: AudioCodec) -> str:
    return _AUDIO_ENCODERS[codec]


def video_bitrate_args(profile: RenderProfile) -> list[str]:
    """Builds the ffmpeg args that make bitrate_strategy concrete. CRF is a
    quality target (no explicit bitrate cap); CBR forces min==max==target for a
    true constant bitrate; VBR sets only a target, letting the encoder vary
    around it."""
    if profile.bitrate_strategy == BitrateStrategy.CRF:
        return ["-crf", str(profile.crf)]

    target = f"{profile.video_bitrate_kbps}k"
    if profile.bitrate_strategy == BitrateStrategy.CBR:
        buffer_size = f"{profile.video_bitrate_kbps * 2}k"
        return ["-b:v", target, "-minrate", target, "-maxrate", target, "-bufsize", buffer_size]

    return ["-b:v", target]
