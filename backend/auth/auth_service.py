from backend.auth.auth_models import AuthSession, AuthUser
from backend.auth.supabase_auth import SupabaseAuthClient
from backend.core.config import settings
from backend.core.domain_exceptions import DatabaseUnavailableError


class AuthService:
    """Service for authentication operations."""

    def __init__(self, client: SupabaseAuthClient) -> None:
        self.client = client

    def sign_up(self, email: str, password: str, full_name: str | None = None) -> AuthUser:
        """Register a new user."""
        raise NotImplementedError

    def sign_in(self, email: str, password: str) -> AuthSession:
        """Sign in a user and return a session.

        In debug mode (``settings.debug = True``) the special development
        credentials ``dev@jarvis.local`` / ``dev-password`` are accepted
        without a live Supabase connection.
        """
        if settings.debug and email == "dev@jarvis.local" and password == "dev-password":
            from backend.auth.dev_auth import create_dev_session
            return create_dev_session()
        return self.client.sign_in(email=email, password=password)

    def refresh_session(self, refresh_token: str) -> AuthSession:
        """Refresh an existing session.

        In debug mode, the dev refresh token returns a fresh dev session.
        """
        if settings.debug:
            from backend.auth.dev_auth import DEV_REFRESH_TOKEN, create_dev_session
            if refresh_token == DEV_REFRESH_TOKEN:
                return create_dev_session()
        raise DatabaseUnavailableError()

    def sign_out(self, refresh_token: str) -> None:
        """Sign out the current user session."""
        # Fire-and-forget — ignore errors
