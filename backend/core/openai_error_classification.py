from __future__ import annotations

import re

from backend.core.provider_exceptions import PermanentProviderError, ProviderError, TransientProviderError

_SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+)", re.IGNORECASE)


def sanitize_error_message(message: str) -> str:
    """Redact anything resembling an API key or bearer token before it is logged
    or surfaced to a caller."""
    return _SECRET_PATTERN.sub("[REDACTED]", message)


def classify_openai_error(exc: Exception) -> ProviderError:
    """Map an OpenAI SDK exception to a typed, sanitized ProviderError. Rate limits,
    timeouts, connection errors, and 5xx responses are transient (retryable);
    everything else (bad request, auth, 4xx) is permanent."""
    message = sanitize_error_message(str(exc))

    try:
        import openai as openai_sdk
    except ImportError:
        return TransientProviderError(message)

    if isinstance(
        exc,
        (
            openai_sdk.APIConnectionError,
            openai_sdk.APITimeoutError,
            openai_sdk.RateLimitError,
            openai_sdk.InternalServerError,
        ),
    ):
        return TransientProviderError(message)

    if isinstance(exc, openai_sdk.APIStatusError):
        if exc.status_code is not None and exc.status_code >= 500:
            return TransientProviderError(message)
        return PermanentProviderError(message)

    return PermanentProviderError(message)
