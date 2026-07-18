from __future__ import annotations


class LLMError(Exception):
    """Base exception for LLM provider failures."""


class LLMInitializationError(LLMError):
    """Raised when an LLM provider fails to initialize."""


class LLMHealthError(LLMError):
    """Raised when an LLM provider health check fails."""


class LLMGenerationError(LLMError):
    """Raised when LLM generation fails."""


class LLMStreamingError(LLMError):
    """Raised when LLM streaming fails."""


class LLMShutdownError(LLMError):
    """Raised when provider shutdown fails."""
