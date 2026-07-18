from __future__ import annotations

from typing import Iterable

from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    cors_allowed_origins: list[str] = []
    trusted_hosts: list[str] = ["*"]
    gzip_minimum_size: int = 500
    production_strict_transport_security: str = "max-age=31536000; includeSubDomains"

    class Config:
        env_file = ".env"
        env_prefix = "SEC_"


security_settings = SecuritySettings()
