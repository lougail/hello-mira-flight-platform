"""
Configuration pytest pour les tests d'intégration Airport.

Fixtures spécifiques aux tests d'intégration (nécessitent services running).
Les fixtures globales sont dans ../conftest.py
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# FIXTURES CONFIGURATION
# ============================================================================

@pytest.fixture
def base_url() -> str:
    """
    URL de base pour les tests d'intégration.

    Returns:
        URL du service airport
    """
    return "http://localhost:8001"


# ============================================================================
# FIXTURES DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def valid_iata_codes() -> list[str]:
    """
    Codes IATA valides pour tests.

    Returns:
        Liste de codes IATA existants
    """
    return ["CDG", "JFK", "ORY", "LHR", "AMS"]


@pytest.fixture
def invalid_iata_codes() -> list[str]:
    """
    Codes IATA invalides pour tests.

    Returns:
        Liste de codes IATA inexistants
    """
    return ["XXX", "ZZZ", "AAA"]


@pytest.fixture
def sample_addresses() -> dict[str, str]:
    """
    Adresses d'exemple pour tests de géocodage.

    Returns:
        Dict avec clé = ville, valeur = adresse
    """
    return {
        "paris": "Tour Eiffel, Paris, France",
        "london": "Big Ben, London, UK",
        "new_york": "Times Square, New York, USA"
    }
