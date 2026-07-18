from __future__ import annotations

import abc

from backend.core.retrieval_models import RetrievalRequest, RetrievalResult


class RetrievalEngine(abc.ABC):
    """Abstract interface for document retrieval."""

    @abc.abstractmethod
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Retrieve documents matching the request criteria."""
        raise NotImplementedError
