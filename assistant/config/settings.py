"""
Configuration du microservice Assistant.

Gestion des variables d'environnement et settings globaux.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """
    Configuration de l'application Assistant.

    Les valeurs sont chargées depuis le fichier .env à la racine du projet
    ou depuis les variables d'environnement (priorité aux env vars).
    """

    # ==========================================================================
    # API EXTERNE - Mistral AI
    # ==========================================================================

    mistral_api_key: str = ""  # Valeur par défaut pour éviter erreur IDE
    mistral_model: str = "mistral-large-latest"
    mistral_temperature: float = 0.0  # Déterministe pour meilleure cohérence

    # ==========================================================================
    # MICROSERVICES INTERNES
    # ==========================================================================

    # URL des microservices (dans Docker : nom du service)
    airport_api_url: str = "http://airport:8001/api/v1"
    flight_api_url: str = "http://flight:8002/api/v1"

    # Timeouts pour les appels HTTP (en secondes)
    http_timeout: int = 30

    # ==========================================================================
    # APPLICATION
    # ==========================================================================

    # Mode debug
    debug: bool = False

    # Mode DEMO : utilise des données mockées au lieu d'appeler les vrais microservices
    # Utile pour démonstration sans quota API Aviationstack
    demo_mode: bool = False

    # CORS origins (pour frontend React)
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ==========================================================================
    # LANGGRAPH CONFIGURATION
    # ==========================================================================

    # Activer le mode streaming (pour réponses en temps réel)
    enable_streaming: bool = False

    # Nombre max de tokens pour les réponses
    max_tokens: int = 1000

    # Configuration de Pydantic Settings v2
    model_config = SettingsConfigDict(
        # Chercher .env à la racine du projet (un niveau au-dessus de assistant/)
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignorer les variables d'env non définies dans le modèle
    )


# Instance globale des settings
settings = Settings()
