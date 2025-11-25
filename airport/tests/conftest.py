"""
Configuration pytest pour les tests Airport.

Fixtures réutilisables pour tous les tests du microservice airport.
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
    db_name = "hello_mira_test"
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
        service_name="airport_test"
    )


@pytest.fixture
def mock_geocoding_service():
    """
    GeocodingService mock pour tests.

    Utilise des données mockées au lieu d'appeler Nominatim.
    """
    from services.geocoding_service import GeocodingService

    service = GeocodingService()
    # TODO: Peut être étendu avec mocks pour éviter appels réels
    return service


# ============================================================================
# FIXTURES DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def sample_airport_data():
    """
    Données d'exemple pour un aéroport (CDG).

    Returns:
        Dict avec données aéroport
    """
    return {
        "iata_code": "CDG",
        "icao_code": "LFPG",
        "name": "Charles de Gaulle International Airport",
        "city": "Paris",
        "country": "France",
        "country_iso2": "FR",
        "latitude": 49.012779,
        "longitude": 2.55,
        "timezone": "Europe/Paris",
        "gmt_offset": 1
    }


@pytest.fixture
def sample_flight_data():
    """
    Données d'exemple pour un vol.

    Returns:
        Dict avec données vol
    """
    return {
        "flight_iata": "AF447",
        "airline": {
            "name": "Air France",
            "iata": "AF"
        },
        "flight_status": "scheduled",
        "departure": {
            "airport": "CDG",
            "scheduled": "2024-11-25T10:00:00Z"
        },
        "arrival": {
            "airport": "JFK",
            "scheduled": "2024-11-25T14:00:00Z"
        }
    }


# ============================================================================
# FIXTURES MOCKS API EXTERNE
# ============================================================================

@pytest.fixture
def mock_aviationstack_response_airport():
    """
    Mock de réponse Aviationstack pour endpoint /airports.

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
def mock_aviationstack_response_flights():
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
