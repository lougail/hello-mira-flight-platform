"""
Configuration du microservice Flight.
Partage la meme base MongoDB que Airport.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Configuration Flight microservice."""

    # API Aviationstack (partagee avec Airport)
    aviationstack_api_key: str
    aviationstack_base_url: str = "http://api.aviationstack.com/v1"
    aviationstack_timeout: int = 30

    # MongoDB (meme instance que Airport)
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "hello_mira"
    mongodb_timeout: int = 5000

    # Cache
    cache_ttl: int = 300  # 5 minutes

    # Application
    app_name: str = "Hello Mira - Flight Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def mongodb_uri_safe(self) -> str:
        """URI MongoDB sans mot de passe pour les logs."""
        uri = self.mongodb_url
        if "@" in uri and ":" in uri:
            parts = uri.split("@")
            credentials = parts[0].split("://")[1]
            if ":" in credentials:
                user = credentials.split(":")[0]
                return uri.replace(credentials, f"{user}:***")
        return uri


settings = Settings()  # type: ignore
