from __future__ import annotations

from backend.core.config import Settings


def get_default_llm_provider(settings: Settings) -> str:
    return settings.default_llm_provider or "openai"


def get_openai_api_key(settings: Settings) -> str | None:
    return settings.openai_api_key


def get_openai_api_base(settings: Settings) -> str | None:
    return settings.openai_api_base


def get_openai_api_version(settings: Settings) -> str | None:
    return settings.openai_api_version
