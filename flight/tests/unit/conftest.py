"""
Configuration pytest pour les tests unitaires Flight.

Fixtures spécifiques aux tests unitaires (mocks, stubs, etc.).
Les fixtures globales sont dans ../conftest.py
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta


# ============================================================================
# FIXTURES MOCK DATA
# ============================================================================

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
                    "timezone": "Europe/Paris",
                    "iata": "CDG",
                    "icao": "LFPG",
                    "scheduled": "2024-11-25T10:00:00+00:00"
                },
                "arrival": {
                    "airport": "John F Kennedy International",
                    "timezone": "America/New_York",
                    "iata": "JFK",
                    "icao": "KJFK",
                    "scheduled": "2024-11-25T14:00:00+00:00"
                },
                "airline": {
                    "name": "Air France",
                    "iata": "AF",
                    "icao": "AFR"
                },
                "flight": {
                    "number": "447",
                    "iata": "AF447",
                    "icao": "AFR447"
                }
            }
        ]
    }


@pytest.fixture
def mock_flight_history_data() -> List[Dict[str, Any]]:
    """
    Mock de données d'historique pour tests de statistiques.

    Returns:
        Liste de vols avec différents statuts et retards
    """
    base_date = datetime(2024, 11, 1)
    flights = []

    for i in range(10):
        flight_date = base_date + timedelta(days=i)
        delay = i * 5 if i < 5 else 0  # Premiers vols en retard

        flights.append({
            "flight_iata": "AF447",
            "flight_date": flight_date.strftime("%Y-%m-%d"),
            "flight_status": "landed",
            "departure": {
                "airport": "CDG",
                "scheduled": flight_date.replace(hour=10).isoformat() + "+00:00",
                "actual": (flight_date.replace(hour=10) + timedelta(minutes=delay)).isoformat() + "+00:00",
                "delay": delay
            },
            "arrival": {
                "airport": "JFK",
                "scheduled": flight_date.replace(hour=14).isoformat() + "+00:00",
                "actual": (flight_date.replace(hour=14) + timedelta(minutes=delay)).isoformat() + "+00:00",
                "delay": delay
            },
            "duration": {
                "scheduled": 240,  # 4h
                "actual": 240 + (delay // 2)
            }
        })

    return flights


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def sample_flight_codes() -> Dict[str, str]:
    """
    Codes de vol d'exemple pour tests.

    Returns:
        Dict avec différents codes IATA
    """
    return {
        "air_france": "AF447",
        "lufthansa": "LH400",
        "british_airways": "BA117",
        "american": "AA100"
    }


@pytest.fixture
def sample_date_range() -> Dict[str, str]:
    """
    Plage de dates d'exemple pour tests historique.

    Returns:
        Dict avec start_date et end_date
    """
    return {
        "start_date": "2024-11-01",
        "end_date": "2024-11-10"
    }
