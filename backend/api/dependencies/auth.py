from fastapi import Depends

from backend.auth.auth_service import AuthService
from backend.auth.supabase_auth import SupabaseAuthClient
from backend.core.dependencies import (
    get_auth_service as get_auth_service_registry,
    get_supabase_auth_client as get_supabase_auth_client_registry,
)


def get_supabase_auth_client(
    client: SupabaseAuthClient = Depends(get_supabase_auth_client_registry),
) -> SupabaseAuthClient:
    """Return a Supabase authentication client instance."""
    return client


def get_auth_service(
    service: AuthService = Depends(get_auth_service_registry),
) -> AuthService:
    """Return an authentication service instance."""
    return service
