from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TModel = TypeVar('TModel')
TResponse = TypeVar('TResponse')


class BaseMapper(ABC, Generic[TModel, TResponse]):
    """Base mapper interface for domain models and response schemas."""

    @abstractmethod
    def from_row(self, row: dict) -> TModel:
        """Convert a database row into a domain model."""

    @abstractmethod
    def to_response(self, model: TModel) -> TResponse:
        """Convert a domain model into a response schema."""
