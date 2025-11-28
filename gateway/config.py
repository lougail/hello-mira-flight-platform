"""Configuration du Gateway."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Aviationstack
    aviationstack_api_key: str = os.getenv("AVIATIONSTACK_API_KEY", "")
    aviationstack_base_url: str = "http://api.aviationstack.com/v1"

    # MongoDB
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    mongodb_database: str = "hellomira_db"

    # Cache
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))

    # Debug
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        env_file = ".env"


settings = Settings()
