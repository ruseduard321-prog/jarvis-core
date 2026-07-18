from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Jarvis API"
    app_version: str = "0.1.0"
    debug: bool = False
    supabase_url: str | None = None
    supabase_key: str | None = None
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    trusted_hosts: list[str] = ["*"]
    gzip_minimum_size: int = 500
    hsts_header: str = "max-age=31536000; includeSubDomains"
    default_llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    openai_api_version: str | None = None
    default_embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        env_prefix = ""


settings = Settings()
