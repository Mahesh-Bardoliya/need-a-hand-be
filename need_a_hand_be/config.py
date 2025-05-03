import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Database connection.
    sqlalchemy_database_url: str

    # Allowed CORS origins.
    cors_allow_origins: typing.List[str] = []

    class Config:
        env_file = ".env"
        extra = "allow"


# Create a settings instance
settings = Settings()
