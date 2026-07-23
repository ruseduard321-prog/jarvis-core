from __future__ import annotations

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Provider abstraction for web search backends."""

    @abstractmethod
    async def search(self, query: str, limit: int = 8) -> list[dict[str, str]]:
        raise NotImplementedError
