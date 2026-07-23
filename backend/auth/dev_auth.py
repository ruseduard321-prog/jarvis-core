"""Development-only authentication bypass.

Provides a mock session so the frontend can be tested without a live
Supabase instance.  This module is only active when ``settings.debug``
is ``True`` and MUST NOT be deployed to production.
"""
from datetime import datetime, timedelta, timezone

from backend.auth.auth_models import AuthSession, AuthUser

# Fixed, non-secret token strings that identify a dev session.
DEV_ACCESS_TOKEN = "dev.access.jarvis.local"
DEV_REFRESH_TOKEN = "dev.refresh.jarvis.local"

DEV_USER = AuthUser(
    id="00000000-0000-0000-0000-dev000000001",
    email="dev@jarvis.local",
    full_name="Development User",
)


def create_dev_session() -> AuthSession:
    """Return a long-lived development session (1 year expiry)."""
    return AuthSession(
        access_token=DEV_ACCESS_TOKEN,
        refresh_token=DEV_REFRESH_TOKEN,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=365),
    )


def validate_dev_token(token: str) -> AuthUser | None:
    """Return ``DEV_USER`` when *token* matches the dev access token."""
    if token in (DEV_ACCESS_TOKEN, DEV_REFRESH_TOKEN):
        return DEV_USER
    return None
