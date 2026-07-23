from typing import Any

from pydantic import ValidationError

from backend.core.config import Settings, settings


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails."""


def validate_configuration(settings_obj: Settings) -> None:
    """Validate required application configuration at startup.

    Args:
        settings_obj: The loaded settings instance.

    Raises:
        ConfigurationValidationError: If required configuration values are missing or invalid.
    """
    errors: list[str] = []

    _validate_database(settings_obj, errors)
    _validate_auth(settings_obj, errors)
    _validate_ai(settings_obj, errors)
    _validate_storage(settings_obj, errors)
    _validate_external_services(settings_obj, errors)

    if errors:
        raise ConfigurationValidationError("; ".join(errors))


def _validate_database(settings_obj: Settings, errors: list[str]) -> None:
    # In debug mode, Supabase is optional (dev auth bypass is used instead).
    if settings_obj.debug:
        return
    if settings_obj.supabase_url is None or not settings_obj.supabase_url.strip():
        errors.append("Database configuration missing: SUPABASE_URL")
    if settings_obj.supabase_key is None or not settings_obj.supabase_key.strip():
        errors.append("Database configuration missing: SUPABASE_KEY")


def _validate_auth(settings_obj: Settings, errors: list[str]) -> None:
    # Auth configuration is currently shared with the database provider.
    if settings_obj.supabase_url is None or not settings_obj.supabase_url.strip():
        return
    if settings_obj.supabase_key is None or not settings_obj.supabase_key.strip():
        return


def _validate_ai(settings_obj: Settings, errors: list[str]) -> None:
    # Future AI config validation can be added here.
    return


def _validate_storage(settings_obj: Settings, errors: list[str]) -> None:
    # Future storage config validation can be added here.
    return


def _validate_external_services(settings_obj: Settings, errors: list[str]) -> None:
    # Future external service config validation can be added here.
    return


def startup_validate_settings() -> None:
    try:
        validate_configuration(settings)
    except ValidationError as exc:
        raise ConfigurationValidationError(str(exc)) from exc
