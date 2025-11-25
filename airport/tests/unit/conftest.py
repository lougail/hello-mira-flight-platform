"""
Configuration pytest pour les tests unitaires Airport.

Fixtures spécifiques aux tests unitaires (mocks, stubs, etc.).
Les fixtures globales sont dans ../conftest.py
"""

import pytest
from typing import Dict, Any


# ============================================================================
# FIXTURES MOCK DATA
# ============================================================================

@pytest.fixture
def mock_airport_api_response() -> Dict[str, Any]:
    """
    Mock de réponse Aviationstack pour /airports.

    Returns:
        Dict simulant la réponse API réelle
    """
    return {
        "pagination": {
            "limit": 100,
            "offset": 0,
            "count": 1,
            "total": 1
        },
        "data": [
            {
                "airport_name": "Charles de Gaulle International Airport",
                "iata_code": "CDG",
                "icao_code": "LFPG",
                "city_iata_code": "PAR",
                "country_name": "France",
                "country_iso2": "FR",
                "latitude": "49.012779",
                "longitude": "2.55",
                "timezone": "Europe/Paris",
                "gmt": "1"
            }
        ]
    }


@pytest.fixture
def mock_flight_api_response() -> Dict[str, Any]:
    """
    Mock de réponse Aviationstack pour /flights.

    Returns:
        Dict simulant la réponse API réelle
    """
    return {
        "pagination": {
            "limit": 100,
            "offset": 0,
            "count": 1,
            "total": 1
        },
        "data": [
            {
                "flight_date": "2024-11-25",
                "flight_status": "scheduled",
                "departure": {
                    "airport": "Charles de Gaulle",
                    "iata": "CDG",
                    "scheduled": "2024-11-25T10:00:00+00:00"
                },
                "arrival": {
                    "airport": "John F Kennedy International",
                    "iata": "JFK",
                    "scheduled": "2024-11-25T14:00:00+00:00"
                },
                "airline": {
                    "name": "Air France",
                    "iata": "AF"
                },
                "flight": {
                    "iata": "AF447"
                }
            }
        ]
    }


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def sample_coordinates() -> Dict[str, float]:
    """
    Coordonnées GPS d'exemple pour tests.

    Returns:
        Dict avec latitude et longitude
    """
    return {
        "latitude": 48.8566,
        "longitude": 2.3522
    }
