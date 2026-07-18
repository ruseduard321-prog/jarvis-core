from typing import Any

from supabase import create_client

from backend.core.config import settings
from backend.core.database import DatabaseProvider


class SupabaseProvider(DatabaseProvider):
    """Supabase database provider implementation."""

    def __init__(self) -> None:
        self.client: Any | None = None

    async def connect(self) -> None:
        """Initialize the Supabase client using environment settings."""
        if settings.supabase_url is None or settings.supabase_key is None:
            self.client = None
            return

        self.client = create_client(settings.supabase_url, settings.supabase_key)

    async def disconnect(self) -> None:
        """Clear the Supabase client reference."""
        self.client = None

    async def health_check(self) -> bool:
        """Return True if the Supabase client has been initialized."""
        return self.client is not None
