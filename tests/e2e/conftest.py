"""
Configuration pytest pour les tests end-to-end.

Fixtures spécifiques aux tests e2e (scénarios cross-services).
Les fixtures globales sont dans ../conftest.py
"""

import pytest
from typing import Dict, Any


# ============================================================================
# FIXTURES AUTO-USE (exécutées automatiquement)
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
async def verify_services_before_e2e(check_services_running):
    """
    Vérifie automatiquement que tous les services sont running avant les tests e2e.

    Cette fixture est exécutée automatiquement (autouse=True) avant tous
    les tests e2e pour éviter les échecs si docker-compose n'est pas démarré.
    """
    # check_services_running est appelé, lèvera une exception si services down
    pass


# ============================================================================
# FIXTURES SCÉNARIOS E2E
# ============================================================================

@pytest.fixture
def airport_to_flights_scenario() -> Dict[str, Any]:
    """
    Scénario : Rechercher un aéroport puis lister ses vols.

    Returns:
        Dict avec les étapes du scénario
    """
    return {
        "name": "Airport → Flights",
        "description": "Utilisateur recherche un aéroport puis consulte les départs",
        "steps": [
            {
                "step": 1,
                "action": "Rechercher aéroport CDG",
                "service": "airport",
                "method": "GET",
                "endpoint": "/api/v1/airports/CDG",
                "expected_status": 200,
                "expected_fields": ["iata_code", "name", "city", "country"]
            },
            {
                "step": 2,
                "action": "Lister vols au départ de CDG",
                "service": "airport",
                "method": "GET",
                "endpoint": "/api/v1/airports/CDG/departures",
                "expected_status": 200,
                "expected_fields": ["flights", "airport"]
            }
        ]
    }


@pytest.fixture
def assistant_orchestration_scenario() -> Dict[str, Any]:
    """
    Scénario : Assistant orchestre appels à airport et flight.

    Returns:
        Dict avec le scénario assistant
    """
    return {
        "name": "Assistant Orchestration",
        "description": "Assistant interprète un prompt et appelle les bons services",
        "steps": [
            {
                "step": 1,
                "action": "Envoyer prompt à l'assistant",
                "service": "assistant",
                "method": "POST",
                "endpoint": "/assistant/answer",
                "data": {
                    "prompt": "Quels vols partent de CDG ?"
                },
                "expected_status": 200,
                "expected_fields": ["answer", "data"]
            }
        ],
        "validation": {
            "answer_contains": ["CDG", "vols", "départ"],
            "data_not_empty": True
        }
    }


@pytest.fixture
def full_user_journey_scenario() -> Dict[str, Any]:
    """
    Scénario : Parcours utilisateur complet.

    Returns:
        Dict avec le parcours complet
    """
    return {
        "name": "Full User Journey",
        "description": "Parcours complet : recherche aéroport → vols → statut vol → assistant",
        "steps": [
            {
                "step": 1,
                "action": "Rechercher aéroport par adresse",
                "service": "airport",
                "method": "POST",
                "endpoint": "/api/v1/airports/search/address",
                "data": {"address": "Paris, France"},
                "expected_status": 200
            },
            {
                "step": 2,
                "action": "Lister vols au départ",
                "service": "airport",
                "method": "GET",
                "endpoint": "/api/v1/airports/CDG/departures",
                "expected_status": 200
            },
            {
                "step": 3,
                "action": "Vérifier statut d'un vol spécifique",
                "service": "flight",
                "method": "GET",
                "endpoint": "/api/v1/flights/AF447",
                "expected_status": 200
            },
            {
                "step": 4,
                "action": "Demander à l'assistant des infos sur le vol",
                "service": "assistant",
                "method": "POST",
                "endpoint": "/assistant/answer",
                "data": {
                    "prompt": "Quel est le statut du vol AF447 ?"
                },
                "expected_status": 200
            }
        ]
    }


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def common_airports() -> list[str]:
    """
    Codes IATA d'aéroports couramment utilisés pour tests e2e.

    Returns:
        Liste de codes IATA
    """
    return ["CDG", "JFK", "ORY", "LHR", "AMS", "FRA"]


@pytest.fixture
def common_flights() -> list[str]:
    """
    Codes de vols couramment utilisés pour tests e2e.

    Returns:
        Liste de codes IATA vols
    """
    return ["AF447", "LH400", "BA117", "AA100"]
