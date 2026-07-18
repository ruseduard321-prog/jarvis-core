from __future__ import annotations

import time
from typing import Callable, Coroutine

from backend.core.dependencies import get_database
from backend.core.supabase_provider import SupabaseProvider
from backend.core.config import settings


class HealthStatus:
    """Structured health check result."""

    def __init__(self, healthy: bool, message: str | None = None) -> None:
        self.healthy = healthy
        self.message = message


async def check_database() -> HealthStatus:
    database = get_database()
    healthy = await database.health_check()
    return HealthStatus(healthy=healthy, message="database")


async def check_auth() -> HealthStatus:
    provider = get_database()
    if not isinstance(provider, SupabaseProvider):
        return HealthStatus(healthy=True, message="auth not configured")
    healthy = await provider.health_check()
    return HealthStatus(healthy=healthy, message="auth")


async def check_storage() -> HealthStatus:
    # Storage is not yet configured in this application.
    return HealthStatus(healthy=True, message="storage not configured")


async def run_health_checks(checks: list[Callable[[], Coroutine[None, None, HealthStatus]]]) -> list[HealthStatus]:
    results: list[HealthStatus] = []
    for check in checks:
        results.append(await check())
    return results


def format_overall_status(checks: list[HealthStatus]) -> str:
    return "ok" if all(check.healthy for check in checks) else "unhealthy"


class AppHealthInfo:
    """Information returned by the app health endpoint."""

    def __init__(self, service: str, version: str, environment: str, uptime_seconds: float, status: str) -> None:
        self.service = service
        self.version = version
        self.environment = environment
        self.uptime_seconds = uptime_seconds
        self.status = status


start_time = time.time()


def get_uptime_seconds() -> float:
    return time.time() - start_time


def build_health_info() -> AppHealthInfo:
    return AppHealthInfo(
        service=settings.app_name,
        version=settings.app_version,
        environment="production" if not settings.debug else "development",
        uptime_seconds=get_uptime_seconds(),
        status="ok",
    )
