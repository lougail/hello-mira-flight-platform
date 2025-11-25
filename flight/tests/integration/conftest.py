"""
Configuration pytest pour les tests d'intégration Flight.

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
        URL du service flight
    """
    return "http://localhost:8002"


# ============================================================================
# FIXTURES DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def valid_flight_codes() -> list[str]:
    """
    Codes de vol valides pour tests.

    Returns:
        Liste de codes IATA existants
    """
    return ["AF447", "LH400", "BA117", "AA100", "DL100"]


@pytest.fixture
def invalid_flight_codes() -> list[str]:
    """
    Codes de vol invalides pour tests.

    Returns:
        Liste de codes IATA inexistants
    """
    return ["XX999", "ZZ000", "AA9999"]


@pytest.fixture
def sample_date_ranges() -> dict[str, dict[str, str]]:
    """
    Plages de dates d'exemple pour tests historique.

    Returns:
        Dict avec différentes périodes
    """
    return {
        "week": {
            "start_date": "2024-11-18",
            "end_date": "2024-11-25"
        },
        "month": {
            "start_date": "2024-10-25",
            "end_date": "2024-11-25"
        },
        "invalid": {
            "start_date": "2024-11-25",
            "end_date": "2024-11-18"  # End avant start
        }
    }


@pytest.fixture
def flight_statuses() -> list[str]:
    """
    Statuts de vol possibles pour tests.

    Returns:
        Liste des statuts Aviationstack
    """
    return [
        "scheduled",
        "active",
        "landed",
        "cancelled",
        "incident",
        "diverted"
    ]
