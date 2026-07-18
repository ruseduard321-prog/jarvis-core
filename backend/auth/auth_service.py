from backend.auth.auth_models import AuthSession, AuthUser
from backend.auth.supabase_auth import SupabaseAuthClient


class AuthService:
    """Service for authentication operations."""

    def __init__(self, client: SupabaseAuthClient) -> None:
        self.client = client

    def sign_up(self, email: str, password: str, full_name: str | None = None) -> AuthUser:
        """Register a new user."""
        raise NotImplementedError

    def sign_in(self, email: str, password: str) -> AuthSession:
        """Sign in a user and return a session."""
        return self.client.sign_in(email=email, password=password)

    def sign_out(self, refresh_token: str) -> None:
        """Sign out the current user session."""
        raise NotImplementedError

    def refresh_session(self, refresh_token: str) -> AuthSession:
        """Refresh an existing session."""
        raise NotImplementedError
