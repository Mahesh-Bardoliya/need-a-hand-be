import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # App secret key.
    secret_key: str

    # Database connection.
    sqlalchemy_database_url: str

    # Allowed CORS origins.
    # NOTE: Currently by default, we are allowing all origins.
    # In future we need to provide only specific ones.
    # E.g. frontend origin URL.
    cors_allow_origins: typing.List[str] = [
        "https://preview--hand-up-community-app.lovable.app",
        "https://localhost",
        "capacitor://localhost",
    ]

    # JWT algorithm.
    jwt_algorithm: str = "HS256"

    # Auth token expiry time.
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        extra = "allow"


# Create a settings instance
settings = Settings()
