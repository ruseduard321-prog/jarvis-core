from __future__ import annotations

import abc
from typing import Protocol

from backend.core.ai_models import AIRequest, AIResponse


class AIOrchestrator(Protocol):
    """Abstract orchestrator interface for AI execution."""

    async def execute(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError
