from __future__ import annotations


class PromptTemplateError(Exception):
    """Base exception for prompt template failures."""


class PromptTemplateValidationError(PromptTemplateError):
    """Raised when required prompt variables are missing."""


class PromptTemplateRenderingError(PromptTemplateError):
    """Raised when prompt rendering fails."""


class PromptTemplateNotFoundError(PromptTemplateError):
    """Raised when a named prompt template cannot be resolved."""
