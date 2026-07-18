from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuthUser:
    """Authentication user model."""

    id: str
    email: str
    full_name: str | None = None


@dataclass
class AuthSession:
    """Authentication session model."""

    access_token: str
    refresh_token: str
    expires_at: datetime
