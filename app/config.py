from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/uncalificado.db"
    jwt_secret: str
    jwt_secret_previous: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30
    password_min_length: int = 10
    auth_rate_limit: int = 10
    file_signing_secret: str | None = None
    signed_url_ttl: int = 900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
