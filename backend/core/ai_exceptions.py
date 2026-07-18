from __future__ import annotations


class AIOrchestratorError(Exception):
    """Base exception for AI orchestrator failures."""


class AIRequestError(AIOrchestratorError):
    """Raised when the incoming AI request is invalid."""


class AIPromptError(AIOrchestratorError):
    """Raised when prompt rendering or prompt resolution fails."""


class AIProviderSelectionError(AIOrchestratorError):
    """Raised when the requested LLM provider cannot be selected."""


class AIGenerationError(AIOrchestratorError):
    """Raised when execution of the LLM request fails."""
