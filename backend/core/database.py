from abc import ABC, abstractmethod


class DatabaseProvider(ABC):
    """Abstract base class for database provider implementations."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the database provider."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the database provider."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True when the database provider is healthy."""
        raise NotImplementedError
