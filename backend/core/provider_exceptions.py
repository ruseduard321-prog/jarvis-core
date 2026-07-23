from __future__ import annotations


class ProviderError(Exception):
    """Base exception for asset-generation provider failures (image/TTS/STT/...)."""


class TransientProviderError(ProviderError):
    """Retryable provider failure: rate limits, timeouts, connection errors, 5xx."""


class PermanentProviderError(ProviderError):
    """Non-retryable provider failure: bad request, auth, unsupported input."""
