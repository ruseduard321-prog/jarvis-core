"""Domain-specific exceptions for repository errors."""


class DomainException(Exception):
    """Base class for all domain-level exceptions."""


class ResourceNotFoundError(DomainException):
    """Raised when a requested resource cannot be found."""


class DatabaseUnavailableError(DomainException):
    """Raised when the database is unavailable."""


class AuthenticationError(DomainException):
    """Raised when authentication fails."""


class AuthorizationError(DomainException):
    """Raised when authorization fails."""


class RepositoryError(DomainException):
    """Raised for unexpected repository failures."""
