"""
Configuration centralisée de l'application Airport.

Utilise pydantic-settings pour :
- Validation automatique des variables d'environnement
- Valeurs par défaut intelligentes
- Gestion propre des erreurs de configuration
- Type hints pour l'autocomplétion IDE
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Configuration globale de l'application Airport.
    
    Les variables sont lues depuis le fichier .env ou les variables d'environnement.
    Les valeurs par défaut sont fournies quand c'est pertinent.
    
    Attributes:
        # API Aviationstack
        aviationstack_api_key: Clé API pour Aviationstack (OBLIGATOIRE)
        aviationstack_base_url: URL de base de l'API Aviationstack
        aviationstack_timeout: Timeout en secondes pour les requêtes
        
        # MongoDB
        mongodb_url: URL de connexion MongoDB
        mongodb_database: Nom de la base de données
        mongodb_timeout: Timeout en secondes pour MongoDB
        
        # Cache
        cache_ttl: Durée de vie du cache en secondes (défaut: 5 minutes)
        
        # FastAPI
        app_name: Nom de l'application
        app_version: Version de l'application
        debug: Mode debug (désactivé en production)
        
        # CORS
        cors_origins: Liste des origines autorisées pour CORS
    """
    
    # API Aviationstack
    aviationstack_api_key: str  # OBLIGATOIRE
    aviationstack_base_url: str = "http://api.aviationstack.com/v1"
    aviationstack_timeout: int = 30
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "hello_mira"
    mongodb_timeout: int = 5000
    
    # Cache
    cache_ttl: int = 300  # 5 minutes
    
    # FastAPI
    app_name: str = "Hello Mira - Airport Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Configuration Pydantic
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @property
    def mongodb_uri_safe(self) -> str:
        """Retourne l'URI MongoDB sans mot de passe pour les logs.
        
        Returns:
            str: URI MongoDB avec mot de passe masqué
        """
        uri = self.mongodb_url
        if "@" in uri and ":" in uri:
            parts = uri.split("@")
            credentials = parts[0].split("://")[1]
            if ":" in credentials:
                user = credentials.split(":")[0]
                return uri.replace(credentials, f"{user}:***")
        return uri
    
    def validate_config(self) -> dict[str, bool]:
        """Valide la configuration et retourne les résultats.
        
        Returns:
            dict: Dictionnaire avec les résultats de validation
        """
        checks = {
            "aviationstack_api_key_present": bool(self.aviationstack_api_key),
            "aviationstack_api_key_valid_format": len(self.aviationstack_api_key) == 32,  # ← CHANGE
            "mongodb_url_present": bool(self.mongodb_url),
            "cache_ttl_positive": self.cache_ttl > 0,
        }
        return checks


# Instance globale
settings = Settings() # type: ignore