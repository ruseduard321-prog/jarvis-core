from backend.repositories.base import BaseRepository


class BaseService:
    """Base service that stores the repository."""

    def __init__(self, repository: BaseRepository) -> None:
        self.repository = repository
