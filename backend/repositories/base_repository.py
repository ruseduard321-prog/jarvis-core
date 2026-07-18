from typing import Generic, TypeVar

from backend.core.database import DatabaseProvider

TModel = TypeVar("TModel")


class BaseRepository(Generic[TModel]):
    """A generic base repository that exposes a database provider."""

    def __init__(self, database: DatabaseProvider) -> None:
        self._database = database

    @property
    def database(self) -> DatabaseProvider:
        """Return the configured database provider."""
        return self._database
