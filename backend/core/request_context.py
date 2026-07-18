from contextvars import ContextVar

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str) -> None:
    """Set the request ID for the current request context."""
    request_id.set(value)


def get_request_id() -> str | None:
    """Return the current request ID from the request context."""
    return request_id.get()
