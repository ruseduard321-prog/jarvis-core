from typing import Callable

from fastapi import Depends, Request

from backend.auth.auth_models import AuthUser
from backend.core.domain_exceptions import AuthenticationError, AuthorizationError


def get_current_user(request: Request) -> AuthUser:
    """Return the authenticated user attached to the request state.

    Args:
        request: The incoming HTTP request.

    Returns:
        The authenticated AuthUser.

    Raises:
        AuthenticationError: If no authenticated user is present.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise AuthenticationError("Authentication required")
    return user


def require_roles(*required_roles: str) -> Callable[[AuthUser], AuthUser]:
    """Return a dependency that enforces required role membership.

    Args:
        *required_roles: Roles required to access the endpoint.

    Returns:
        A callable dependency that returns the authenticated user.

    Raises:
        AuthorizationError: If the authenticated user does not have required roles.
    """

    def dependency(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if not required_roles:
            return current_user

        current_roles = set(getattr(current_user, "roles", []))
        missing_roles = set(required_roles) - current_roles
        if missing_roles:
            raise AuthorizationError("Forbidden")

        return current_user

    return dependency
