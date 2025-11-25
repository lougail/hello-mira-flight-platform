"""
Tests d'intégration pour les endpoints Airport.

Tests les endpoints avec FastAPI TestClient contre l'application réelle.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestAirportsEndpoints:
    """Tests d'intégration des endpoints /airports."""

    @pytest.mark.asyncio
    async def test_get_airport_by_iata_success(self, async_client: AsyncClient):
        """
        Test GET /airports/{iata_code} avec code valide.

        Vérifie :
        - Status 200
        - Structure réponse correcte
        - Données aéroport présentes
        """
        response = await async_client.get("/api/v1/airports/CDG")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["iata_code"] == "CDG"
        assert "name" in data
        assert "city" in data
        assert "country" in data
        assert "coordinates" in data

    @pytest.mark.asyncio
    async def test_get_airport_by_iata_not_found(self, async_client: AsyncClient):
        """
        Test GET /airports/{iata_code} avec code invalide.

        Vérifie :
        - Status 404
        - Message d'erreur approprié
        """
        response = await async_client.get("/api/v1/airports/XXX")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        error = response.json()
        assert "detail" in error

    @pytest.mark.asyncio
    async def test_search_airports_by_city(self, async_client: AsyncClient):
        """
        Test GET /airports/search avec paramètre city.

        Vérifie :
        - Status 200
        - Liste de résultats
        - Filtrage par ville
        """
        response = await async_client.get("/api/v1/airports/search", params={"city": "Paris"})

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Vérifie que tous les résultats contiennent Paris
        for airport in data:
            assert "Paris" in airport["city"] or "Paris" in airport["name"]

    @pytest.mark.asyncio
    async def test_search_airports_by_coordinates(self, async_client: AsyncClient):
        """
        Test GET /airports/search/nearby avec coordonnées GPS.

        Vérifie :
        - Status 200
        - Aéroports triés par distance
        - Distance calculée
        """
        # Coordonnées de Paris (près de CDG/ORY)
        response = await async_client.get(
            "/api/v1/airports/search/nearby",
            params={"latitude": 48.8566, "longitude": 2.3522, "limit": 5}
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Vérifie structure
        for airport in data:
            assert "distance_km" in airport
            assert airport["distance_km"] >= 0

    @pytest.mark.asyncio
    async def test_search_airports_by_address(self, async_client: AsyncClient):
        """
        Test GET /airports/search/by-address avec géocodage.

        Vérifie :
        - Status 200
        - Géocodage Nominatim fonctionne
        - Résultats pertinents
        """
        response = await async_client.get(
            "/api/v1/airports/search/by-address",
            params={"address": "Tour Eiffel, Paris", "limit": 3}
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Devrait trouver CDG ou ORY
        iata_codes = [airport["iata_code"] for airport in data]
        assert "CDG" in iata_codes or "ORY" in iata_codes


class TestFlightsEndpoints:
    """Tests d'intégration des endpoints /airports/{iata}/departures|arrivals."""

    @pytest.mark.asyncio
    async def test_get_departures_success(self, async_client: AsyncClient):
        """
        Test GET /airports/{iata}/departures.

        Vérifie :
        - Status 200
        - Liste de vols
        - Structure vol correcte
        """
        response = await async_client.get("/api/v1/airports/CDG/departures", params={"limit": 5})

        # Peut être 200 avec liste vide (pas de vols) ou 200 avec données
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)

        # Si des vols existent, vérifie structure
        if len(data) > 0:
            flight = data[0]
            assert "flight_iata" in flight
            assert "departure" in flight
            assert "arrival" in flight

    @pytest.mark.asyncio
    async def test_get_arrivals_success(self, async_client: AsyncClient):
        """
        Test GET /airports/{iata}/arrivals.

        Vérifie :
        - Status 200
        - Liste de vols
        """
        response = await async_client.get("/api/v1/airports/JFK/arrivals", params={"limit": 5})

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_departures_invalid_iata(self, async_client: AsyncClient):
        """
        Test GET /airports/{iata}/departures avec code invalide.

        Vérifie :
        - Gestion d'erreur appropriée
        """
        response = await async_client.get("/api/v1/airports/INVALID/departures")

        # Peut être 404 ou 200 avec liste vide selon implémentation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestHealthEndpoints:
    """Tests des endpoints de santé."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """
        Test GET /health.

        Vérifie :
        - Status 200
        - Service healthy
        """
        response = await async_client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """
        Test GET /ready.

        Vérifie :
        - Status 200
        - Service ready
        - Dépendances OK
        """
        response = await async_client.get("/api/v1/ready")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "ready"
        assert "mongodb" in data
        assert "aviationstack" in data
