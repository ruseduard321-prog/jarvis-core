from __future__ import annotations


class ConversationError(Exception):
    """Base exception for conversation engine failures."""


class ConversationNotFoundError(ConversationError):
    """Raised when a conversation cannot be found."""


class ConversationStateError(ConversationError):
    """Raised when a conversation state transition is invalid."""


class ConversationValidationError(ConversationError):
    """Raised when a conversation request is invalid."""
