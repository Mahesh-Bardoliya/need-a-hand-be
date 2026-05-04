import typing

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # App secret key.
    secret_key: str = "development-secret-key-do-not-use-in-production"

    # Environment
    environment: str = "development"

    # Database connection.
    sqlalchemy_database_url: str = "sqlite:///./need_a_hand.db"

    # Allowed CORS origins.
    # NOTE: Currently by default, we are allowing all origins.
    # In future we need to provide only specific ones.
    # E.g. frontend origin URL.
    cors_allow_origins: typing.List[str] = [
        "https://localhost",
        "capacitor://localhost",
        "http://localhost",
        "http://localhost:8081",
        "http://127.0.0.1",
        "http://127.0.0.1:8081",
    ]

    # JWT algorithm.
    jwt_algorithm: str = "HS256"

    # Auth token expiry time.
    access_token_expire_minutes: int = 60

    model_config = ConfigDict(env_file=".env", extra="allow")


# Create a settings instance
settings = Settings()
