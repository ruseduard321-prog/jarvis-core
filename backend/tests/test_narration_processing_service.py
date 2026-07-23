from __future__ import annotations

import subprocess

from backend.core.config import Settings
from backend.services.narration_processing_service import NarrationProcessingService


class FakeSubprocessRunner:
    def __init__(self, *, returncode: int = 0, output_bytes: bytes = b"normalized-bytes"):
        self.returncode = returncode
        self.output_bytes = output_bytes
        self.calls: list[list[str]] = []

    def __call__(self, args, capture_output=True, timeout=None):
        self.calls.append(args)
        output_path = args[-1]
        if self.returncode == 0:
            with open(output_path, "wb") as handle:
                handle.write(self.output_bytes)
        return subprocess.CompletedProcess(
            args=args, returncode=self.returncode, stdout=b"", stderr=b"" if self.returncode == 0 else b"boom"
        )


def test_process_returns_normalized_bytes_on_success():
    runner = FakeSubprocessRunner()
    service = NarrationProcessingService(Settings(), subprocess_runner=runner)

    result = service.process(b"raw-audio-bytes")

    assert result == b"normalized-bytes"
    assert len(runner.calls) == 1
    args = runner.calls[0]
    assert "loudnorm" in args[args.index("-af") + 1]


def test_process_falls_back_to_original_bytes_on_ffmpeg_failure():
    runner = FakeSubprocessRunner(returncode=1)
    service = NarrationProcessingService(Settings(), subprocess_runner=runner)

    result = service.process(b"raw-audio-bytes")

    assert result == b"raw-audio-bytes"


def test_process_falls_back_to_original_bytes_when_ffmpeg_binary_missing():
    def raising_runner(args, capture_output=True, timeout=None):
        raise FileNotFoundError("ffmpeg not found")

    service = NarrationProcessingService(Settings(), subprocess_runner=raising_runner)

    result = service.process(b"raw-audio-bytes")

    assert result == b"raw-audio-bytes"


def test_process_skips_when_disabled_by_settings():
    def failing_runner(args, capture_output=True, timeout=None):
        raise AssertionError("should not be called when normalization is disabled")

    service = NarrationProcessingService(
        Settings(narration_normalization_enabled=False), subprocess_runner=failing_runner
    )

    result = service.process(b"raw-audio-bytes")

    assert result == b"raw-audio-bytes"


def test_process_skips_empty_bytes():
    def failing_runner(args, capture_output=True, timeout=None):
        raise AssertionError("should not be called for empty input")

    service = NarrationProcessingService(Settings(), subprocess_runner=failing_runner)

    result = service.process(b"")

    assert result == b""
