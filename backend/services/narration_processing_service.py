from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from backend.core.config import Settings

logger = logging.getLogger(__name__)

SubprocessRunner = Callable[..., subprocess.CompletedProcess]

_TIMEOUT_SECONDS = 60.0


class NarrationProcessingService:
    """Normalizes the raw narration track to a consistent loudness level before
    mixing, via a single ffmpeg `loudnorm` pass — local, free, and the only
    "Narration Processing" stage F26 ships today (see
    docs/F26_ARCHITECTURE_PROPOSAL.md §3.3). Never raises: any ffmpeg failure
    (missing binary, bad input, timeout) returns the original bytes unchanged so a
    processing failure never blocks voice generation."""

    def __init__(self, settings: Settings, subprocess_runner: SubprocessRunner | None = None) -> None:
        self._settings = settings
        self._run_subprocess = subprocess_runner or subprocess.run

    def process(self, audio_bytes: bytes) -> bytes:
        if not audio_bytes or not self._settings.narration_normalization_enabled:
            return audio_bytes

        try:
            with tempfile.TemporaryDirectory(prefix="narration_processing_") as work_dir:
                workspace = Path(work_dir)
                input_path = workspace / "narration_raw.mp3"
                input_path.write_bytes(audio_bytes)
                output_path = workspace / "narration_normalized.mp3"

                args = [
                    self._settings.ffmpeg_binary,
                    "-y",
                    "-i",
                    str(input_path),
                    "-af",
                    f"loudnorm=I={self._settings.narration_target_lufs}:TP=-1.5:LRA=11",
                    str(output_path),
                ]
                completed = self._run_subprocess(args, capture_output=True, timeout=_TIMEOUT_SECONDS)
                if completed.returncode != 0:
                    stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
                    logger.warning("narration_processing_failed", extra={"reason": stderr})
                    return audio_bytes
                return output_path.read_bytes()
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("narration_processing_unavailable", extra={"reason": str(exc)})
            return audio_bytes
        except Exception:  # pragma: no cover - defensive path
            logger.exception("narration_processing_unexpected_failure")
            return audio_bytes
