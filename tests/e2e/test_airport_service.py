"""
Tests end-to-end pour le service Airport.

Ces tests vérifient le service Airport via HTTP en conditions réelles.
Nécessite docker-compose up (au minimum airport + mongodb).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestAirportServiceE2E:
    """Tests e2e du service Airport."""

    async def test_health_check(self, airport_client: AsyncClient):
        """Vérifie que le service Airport répond au healthcheck."""
        response = await airport_client.get("/api/v1/health/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    async def test_get_airport_by_iata(self, airport_client: AsyncClient):
        """
        Scénario e2e : Rechercher un aéroport par code IATA.

        Vérifie l'intégration complète :
        - Endpoint FastAPI
        - Client Aviationstack
        - Cache MongoDB
        - Transformations de données
        """
        response = await airport_client.get("/api/v1/airports/CDG")

        assert response.status_code == 200
        data = response.json()

        # Vérifie structure de réponse
        assert data["iata_code"] == "CDG"
        assert "name" in data
        assert "city" in data
        assert "country" in data
        assert "coordinates" in data

        # Vérifie coordonnées
        coords = data["coordinates"]
        assert "latitude" in coords
        assert "longitude" in coords

    async def test_search_airport_by_coordinates(
        self,
        airport_client: AsyncClient
    ):
        """
        Scénario e2e : Trouver l'aéroport le plus proche de coordonnées GPS.

        Test l'intégration avec le service de géocodage.
        """
        # Coordonnées de Paris (devrait trouver CDG ou ORY)
        response = await airport_client.get(
            "/api/v1/airports/search/nearby",
            params={"latitude": 48.8566, "longitude": 2.3522}
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifie qu'on trouve au moins un aéroport
        assert "airports" in data
        assert len(data["airports"]) > 0

        # Vérifie structure du premier résultat
        first_airport = data["airports"][0]
        assert "iata_code" in first_airport
        assert "distance_km" in first_airport

    async def test_cache_behavior(self, airport_client: AsyncClient):
        """
        Scénario e2e : Vérifie le comportement du cache.

        Deux requêtes identiques consécutives :
        - Première devrait hit l'API (ou cache si déjà appelé)
        - Deuxième devrait hit le cache MongoDB
        """
        # Premier appel
        response1 = await airport_client.get("/api/v1/airports/JFK")
        assert response1.status_code == 200
        data1 = response1.json()

        # Deuxième appel immédiat (devrait venir du cache)
        response2 = await airport_client.get("/api/v1/airports/JFK")
        assert response2.status_code == 200
        data2 = response2.json()

        # Vérifie que les données sont identiques
        assert data1 == data2
        assert data1["iata_code"] == "JFK"
