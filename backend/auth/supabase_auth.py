from datetime import datetime
from typing import Any

from backend.auth.auth_models import AuthSession, AuthUser
from backend.core.database import DatabaseProvider
from backend.core.domain_exceptions import (
    AuthenticationError,
    DatabaseUnavailableError,
    RepositoryError,
)
from supabase import AuthApiError, AuthInvalidCredentialsError


class SupabaseAuthClient:
    """Supabase authentication client abstraction."""

    def __init__(self, database: DatabaseProvider) -> None:
        self.database = database

    def sign_up(self, email: str, password: str, full_name: str | None = None):
        """Register a new user with Supabase auth."""
        raise NotImplementedError

    def sign_in(self, email: str, password: str) -> AuthSession:
        """Sign in a user with Supabase auth."""
        if not hasattr(self.database, "client") or self.database.client is None:
            raise DatabaseUnavailableError()

        try:
            response = self.database.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            user_data: Any = getattr(response, "user", None)
            session_data: Any = getattr(response, "session", None)
            if user_data is None or session_data is None:
                raise RepositoryError()

            full_name = None
            user_metadata = getattr(user_data, "user_metadata", None)
            if isinstance(user_metadata, dict):
                full_name = user_metadata.get("full_name")

            AuthUser(
                id=str(getattr(user_data, "id", "")),
                email=str(getattr(user_data, "email", "")),
                full_name=full_name,
            )

            expires_at = getattr(session_data, "expires_at", None)
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            elif isinstance(expires_at, int):
                expires_at = datetime.fromtimestamp(expires_at)
            elif not isinstance(expires_at, datetime):
                raise RepositoryError()

            return AuthSession(
                access_token=str(getattr(session_data, "access_token", "")),
                refresh_token=str(getattr(session_data, "refresh_token", "")),
                expires_at=expires_at,
            )
        except AuthInvalidCredentialsError as exc:
            raise RepositoryError() from exc
        except AuthApiError as exc:
            raise DatabaseUnavailableError() from exc
        except OSError as exc:
            raise DatabaseUnavailableError() from exc
        except Exception as exc:
            raise RepositoryError() from exc

    def validate_token(self, access_token: str) -> AuthUser:
        """Validate a Supabase access token and return the authenticated user."""
        if not hasattr(self.database, "client") or self.database.client is None:
            raise DatabaseUnavailableError()

        try:
            user_data = self.database.client.auth.get_user(jwt=access_token)
            if user_data is None:
                raise AuthenticationError("Invalid access token")

            full_name = None
            user_metadata = getattr(user_data, "user_metadata", None)
            if isinstance(user_metadata, dict):
                full_name = user_metadata.get("full_name")

            return AuthUser(
                id=str(getattr(user_data, "id", "")),
                email=str(getattr(user_data, "email", "")),
                full_name=full_name,
            )
        except AuthApiError as exc:
            raise AuthenticationError("Invalid access token") from exc
        except OSError as exc:
            raise DatabaseUnavailableError() from exc
        except Exception as exc:
            raise RepositoryError() from exc

    def sign_out(self, refresh_token: str) -> None:
        """Sign out a user session."""
        raise NotImplementedError

    def refresh_session(self, refresh_token: str):
        """Refresh an authentication session."""
        raise NotImplementedError
