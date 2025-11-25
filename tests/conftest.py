"""
Configuration pytest globale pour tous les tests du projet.

Fixtures partagées entre microservices pour tests cross-services (e2e).
"""

import pytest
import asyncio
from httpx import AsyncClient
from typing import Dict, AsyncGenerator


# ============================================================================
# FIXTURES EVENT LOOP
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Event loop pour les tests async cross-services.

    Scope session pour réutiliser le même loop dans tous les tests e2e.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# FIXTURES CLIENTS HTTP MULTI-SERVICES
# ============================================================================

@pytest.fixture
async def airport_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Client HTTP async pour le service Airport.

    Returns:
        AsyncClient configuré pour http://localhost:8001
    """
    async with AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
        yield client


@pytest.fixture
async def flight_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Client HTTP async pour le service Flight.

    Returns:
        AsyncClient configuré pour http://localhost:8002
    """
    async with AsyncClient(base_url="http://localhost:8002", timeout=10.0) as client:
        yield client


@pytest.fixture
async def assistant_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Client HTTP async pour le service Assistant.

    Returns:
        AsyncClient configuré pour http://localhost:8003
    """
    async with AsyncClient(base_url="http://localhost:8003", timeout=30.0) as client:
        yield client


@pytest.fixture
async def all_services() -> AsyncGenerator[Dict[str, AsyncClient], None]:
    """
    Tous les clients HTTP pour tests e2e complets.

    Returns:
        Dict avec airport, flight, assistant clients
    """
    async with AsyncClient(base_url="http://localhost:8001", timeout=10.0) as airport, \
               AsyncClient(base_url="http://localhost:8002", timeout=10.0) as flight, \
               AsyncClient(base_url="http://localhost:8003", timeout=30.0) as assistant:
        yield {
            "airport": airport,
            "flight": flight,
            "assistant": assistant
        }


# ============================================================================
# FIXTURES VÉRIFICATION SERVICES
# ============================================================================

@pytest.fixture(scope="session")
async def check_services_running():
    """
    Vérifie que tous les services sont démarrés avant les tests e2e.

    Raises:
        RuntimeError: Si un service n'est pas accessible
    """
    services = {
        "airport": "http://localhost:8001/api/v1/health/liveness",
        "flight": "http://localhost:8002/api/v1/health/liveness",
        "assistant": "http://localhost:8003/health"
    }

    async with AsyncClient(timeout=5.0) as client:
        for service_name, health_url in services.items():
            try:
                response = await client.get(health_url)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Service {service_name} not healthy: {response.status_code}"
                    )
            except Exception as e:
                raise RuntimeError(
                    f"Service {service_name} not accessible at {health_url}. "
                    f"Make sure docker-compose is running. Error: {e}"
                )


# ============================================================================
# FIXTURES DONNÉES DE TEST E2E
# ============================================================================

@pytest.fixture
def e2e_test_scenarios() -> Dict[str, Dict]:
    """
    Scénarios de test end-to-end prédéfinis.

    Returns:
        Dict avec différents scénarios utilisateur
    """
    return {
        "search_airport_and_flights": {
            "description": "Rechercher un aéroport puis ses vols",
            "steps": [
                {"service": "airport", "endpoint": "/api/v1/airports/CDG"},
                {"service": "airport", "endpoint": "/api/v1/airports/CDG/departures"}
            ]
        },
        "check_flight_status": {
            "description": "Vérifier le statut d'un vol",
            "steps": [
                {"service": "flight", "endpoint": "/api/v1/flights/AF447"}
            ]
        },
        "assistant_full_flow": {
            "description": "Assistant → Airport → Flight",
            "steps": [
                {
                    "service": "assistant",
                    "endpoint": "/assistant/answer",
                    "method": "POST",
                    "data": {"prompt": "Quels vols partent de CDG ?"}
                }
            ]
        }
    }


@pytest.fixture
def sample_user_prompts() -> list[str]:
    """
    Prompts utilisateur d'exemple pour tester l'assistant.

    Returns:
        Liste de prompts variés
    """
    return [
        "Quels vols partent de CDG cet après-midi ?",
        "Je suis sur le vol AF447, à quelle heure vais-je arriver ?",
        "Trouve-moi l'aéroport le plus proche de Lille",
        "Quel est le statut du vol LH400 ?",
        "Y a-t-il des vols qui arrivent à JFK maintenant ?"
    ]


# ============================================================================
# CONFIGURATION PYTEST
# ============================================================================

def pytest_configure(config):
    """
    Configuration globale pytest pour tous les tests.

    Enregistre des markers custom.
    """
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (require all services running)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
