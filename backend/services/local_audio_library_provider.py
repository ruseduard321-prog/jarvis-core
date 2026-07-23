from __future__ import annotations

import re
from pathlib import Path

from backend.core.config import Settings
from backend.core.media_asset import MediaAsset
from backend.services.music_generation_provider import MusicGenerationProvider
from backend.services.sound_effect_provider import SoundEffectProvider

_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
_MIME_BY_SUFFIX = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _keywords(text: str) -> list[str]:
    return [word for word in re.split(r"\W+", text.lower()) if word]


def _mime_type(path: Path) -> str:
    return _MIME_BY_SUFFIX.get(path.suffix.lower(), "audio/mpeg")


def _find_best_match(root: Path, keywords: list[str]) -> Path | None:
    """Keyword-matches a track's filename/parent-folder name against the requested
    keywords — the same deterministic-keyword-matching pattern
    DeterministicShotPlanner already uses for camera movement. Falls back to the
    first available track deterministically (sorted) rather than nothing, so a
    populated library always contributes *something* even without a clean match."""
    if not root.exists() or not root.is_dir():
        return None

    candidates = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in _AUDIO_EXTENSIONS)
    if not candidates:
        return None

    for candidate in candidates:
        haystack = f"{candidate.parent.name} {candidate.stem}".lower()
        if any(keyword in haystack for keyword in keywords):
            return candidate
    return candidates[0]


def _skipped_asset(provider: str, media_type: str, reason: str) -> MediaAsset:
    return MediaAsset(
        id="none",
        type=media_type,  # type: ignore[arg-type]
        source="",
        provider=provider,
        mime_type="",
        metadata={"status": "SKIPPED", "reason": reason},
    )


class LocalMusicLibraryProvider(MusicGenerationProvider):
    """First concrete MusicGenerationProvider (F26): selects a pre-existing
    royalty-free track from a local, keyword-matched folder instead of generating
    audio — zero API cost, consistent with F25's "prioritize local rendering"
    precedent. True generative music can be added later as a second implementation
    of this same interface with no caller changes. Gracefully SKIPs (never raises)
    when the configured library is empty or missing — background music must always
    remain optional."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_music(self, *, prompt: str, duration: float | None = None) -> MediaAsset:
        root = Path(self._settings.music_library_root)
        match = _find_best_match(root, _keywords(prompt))
        if match is None:
            return _skipped_asset("local-music-library", "audio", f"No track found under {root}")
        return MediaAsset(
            id=match.stem,
            type="audio",
            source=str(match),
            provider="local-music-library",
            mime_type=_mime_type(match),
            duration=duration,
            prompt=prompt,
            metadata={"status": "SUCCESS"},
        )


class LocalSoundEffectLibraryProvider(SoundEffectProvider):
    """First concrete SoundEffectProvider (F26): selects a pre-existing CC0 sound
    effect from a local, keyword-matched folder — zero API cost. Mirrors
    LocalMusicLibraryProvider exactly. Gracefully SKIPs when the configured library
    is empty or missing — sound effects must always remain optional."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_sound_effect(self, *, keywords: str) -> MediaAsset:
        root = Path(self._settings.sound_effect_library_root)
        match = _find_best_match(root, _keywords(keywords))
        if match is None:
            return _skipped_asset("local-sound-effect-library", "audio", f"No effect found under {root}")
        return MediaAsset(
            id=match.stem,
            type="audio",
            source=str(match),
            provider="local-sound-effect-library",
            mime_type=_mime_type(match),
            prompt=keywords,
            metadata={"status": "SUCCESS"},
        )
