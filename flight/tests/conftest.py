"""
Configuration pytest pour les tests Flight.

Fixtures réutilisables pour tous les tests du microservice flight.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient

# Import de l'app FastAPI
import sys
from pathlib import Path

# Ajoute le dossier parent au path pour import
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config.settings import settings


# ============================================================================
# FIXTURES EVENT LOOP
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Event loop pour les tests async.

    Scope session pour réutiliser le même loop dans tous les tests.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# FIXTURES CLIENT HTTP
# ============================================================================

@pytest.fixture
async def async_client():
    """
    Client HTTP async pour tester les endpoints FastAPI.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# FIXTURES MONGODB
# ============================================================================

@pytest.fixture(scope="session")
async def mongo_client():
    """
    Client MongoDB pour tests.

    Scope session pour connexion unique durant tous les tests.
    """
    client = AsyncIOMotorClient(settings.mongodb_url)
    yield client
    client.close()


@pytest.fixture
async def mongo_test_db(mongo_client):
    """
    Base de données MongoDB de test.

    Crée une DB temporaire pour chaque test, la nettoie après.
    """
    db_name = "hello_mira_flight_test"
    db = mongo_client[db_name]

    yield db

    # Cleanup : supprime la DB de test
    await mongo_client.drop_database(db_name)


@pytest.fixture
async def mock_cache_collection(mongo_test_db):
    """
    Collection MongoDB mock pour tester CacheService.

    Returns:
        Collection MongoDB avec TTL index configuré
    """
    collection = mongo_test_db["cache_test"]

    # Configure TTL index
    await collection.create_index("expires_at", expireAfterSeconds=0)

    yield collection

    # Cleanup
    await collection.drop()


@pytest.fixture
async def mock_history_collection(mongo_test_db):
    """
    Collection MongoDB mock pour tester l'historique des vols.

    Returns:
        Collection MongoDB pour historique
    """
    collection = mongo_test_db["history_test"]

    yield collection

    # Cleanup
    await collection.drop()


# ============================================================================
# FIXTURES SERVICES
# ============================================================================

@pytest.fixture
def mock_cache_service(mock_cache_collection):
    """
    CacheService mock pour tests unitaires.

    Returns:
        CacheService configuré avec collection de test
    """
    from services.cache_service import CacheService

    return CacheService(
        collection=mock_cache_collection,
        ttl=300,
        service_name="flight_test"
    )


# ============================================================================
# FIXTURES DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def sample_flight_data():
    """
    Données d'exemple pour un vol.

    Returns:
        Dict avec données vol
    """
    return {
        "flight_iata": "AF447",
        "flight_icao": "AFR447",
        "airline": {
            "name": "Air France",
            "iata": "AF",
            "icao": "AFR"
        },
        "flight_status": "scheduled",
        "departure": {
            "airport": "CDG",
            "timezone": "Europe/Paris",
            "iata": "CDG",
            "icao": "LFPG",
            "scheduled": "2024-11-25T10:00:00+00:00"
        },
        "arrival": {
            "airport": "JFK",
            "timezone": "America/New_York",
            "iata": "JFK",
            "icao": "KJFK",
            "scheduled": "2024-11-25T14:00:00+00:00"
        }
    }


@pytest.fixture
def sample_flight_history():
    """
    Données d'exemple pour l'historique d'un vol.

    Returns:
        Liste de vols avec différents statuts
    """
    return [
        {
            "flight_iata": "AF447",
            "flight_date": "2024-11-20",
            "flight_status": "landed",
            "departure": {
                "airport": "CDG",
                "scheduled": "2024-11-20T10:00:00+00:00",
                "actual": "2024-11-20T10:15:00+00:00",
                "delay": 15
            },
            "arrival": {
                "airport": "JFK",
                "scheduled": "2024-11-20T14:00:00+00:00",
                "actual": "2024-11-20T14:10:00+00:00",
                "delay": 10
            }
        },
        {
            "flight_iata": "AF447",
            "flight_date": "2024-11-21",
            "flight_status": "landed",
            "departure": {
                "airport": "CDG",
                "scheduled": "2024-11-21T10:00:00+00:00",
                "actual": "2024-11-21T10:00:00+00:00",
                "delay": 0
            },
            "arrival": {
                "airport": "JFK",
                "scheduled": "2024-11-21T14:00:00+00:00",
                "actual": "2024-11-21T13:55:00+00:00",
                "delay": -5
            }
        }
    ]


# ============================================================================
# FIXTURES MOCKS API EXTERNE
# ============================================================================

@pytest.fixture
def mock_aviationstack_response_flight():
    """
    Mock de réponse Aviationstack pour endpoint /flights.

    Returns:
        Dict simulant la réponse API
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


# ============================================================================
# CONFIGURATION PYTEST
# ============================================================================

def pytest_configure(config):
    """
    Configuration globale pytest.

    Enregistre des markers custom.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
