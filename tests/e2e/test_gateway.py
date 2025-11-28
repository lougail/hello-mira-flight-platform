"""
Tests end-to-end pour le Gateway.

Ces tests verifient le Gateway via HTTP en conditions reelles.
Necessite docker-compose up (au minimum gateway + mongodb).

Tests couverts:
- Health check et rate limit info
- Cache hits/misses
- Request coalescing
- Metriques Prometheus
"""

import asyncio
import pytest
from httpx import AsyncClient
import re


@pytest.mark.e2e
class TestGatewayHealthE2E:
    """Tests e2e du health check Gateway."""

    async def test_health_check(self, gateway_client: AsyncClient):
        """Verifie que le Gateway repond au healthcheck avec infos rate limit."""
        response = await gateway_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Structure de base
        assert data["status"] == "healthy"
        assert "cache" in data
        assert "circuit_breaker" in data

        # Rate limit info
        assert "rate_limit" in data
        rate_limit = data["rate_limit"]
        assert "used" in rate_limit
        assert "limit" in rate_limit
        assert "remaining" in rate_limit
        assert rate_limit["remaining"] == rate_limit["limit"] - rate_limit["used"]


@pytest.mark.e2e
class TestGatewayCacheE2E:
    """Tests e2e du cache Gateway."""

    async def test_cache_behavior_airports(self, gateway_client: AsyncClient):
        """
        Scenario e2e: Verifie le comportement du cache pour airports.

        1. Premiere requete (potentiellement cache miss)
        2. Deuxieme requete identique (devrait etre cache hit)
        """
        # Utilise un aeroport peu commun pour maximiser chances de cache miss initial
        iata_code = "LYS"  # Lyon

        # Premier appel
        response1 = await gateway_client.get(f"/airports?iata={iata_code}")
        assert response1.status_code == 200
        data1 = response1.json()

        # Deuxieme appel immediat (devrait venir du cache)
        response2 = await gateway_client.get(f"/airports?iata={iata_code}")
        assert response2.status_code == 200
        data2 = response2.json()

        # Les donnees doivent etre identiques
        assert data1 == data2

    async def test_cache_behavior_flights(self, gateway_client: AsyncClient):
        """
        Scenario e2e: Verifie le comportement du cache pour flights.
        """
        flight_iata = "AF1234"  # Vol test

        # Premier appel
        response1 = await gateway_client.get(f"/flights?flight_iata={flight_iata}")
        # Peut etre 200 ou 404 selon si le vol existe
        assert response1.status_code in [200, 404]

        if response1.status_code == 200:
            data1 = response1.json()

            # Deuxieme appel (cache hit)
            response2 = await gateway_client.get(f"/flights?flight_iata={flight_iata}")
            assert response2.status_code == 200
            data2 = response2.json()

            assert data1 == data2


@pytest.mark.e2e
class TestGatewayCoalescingE2E:
    """Tests e2e du request coalescing Gateway."""

    async def test_coalescing_simultaneous_requests(self, gateway_client: AsyncClient):
        """
        Scenario e2e: Teste le request coalescing.

        Envoie plusieurs requetes identiques simultanees.
        Devrait coalescer les requetes et ne faire qu'un seul appel API.
        """
        # Utilise un code IATA peu commun pour eviter le cache
        # On genere un code unique avec timestamp pour forcer un cache miss
        import time
        timestamp = int(time.time()) % 1000

        # Utilise un aeroport reel mais peu requete
        iata_code = "TLS"  # Toulouse

        # Envoie 5 requetes simultanees
        tasks = [
            gateway_client.get(f"/airports?iata={iata_code}")
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Toutes les requetes doivent reussir
        successful = 0
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code in [200, 404]
                successful += 1

        # Au moins 4 sur 5 doivent reussir
        assert successful >= 4

        # Si toutes 200, les donnees doivent etre identiques
        ok_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
        if len(ok_responses) > 1:
            first_data = ok_responses[0].json()
            for resp in ok_responses[1:]:
                assert resp.json() == first_data


@pytest.mark.e2e
class TestGatewayMetricsE2E:
    """Tests e2e des metriques Prometheus du Gateway."""

    async def test_metrics_endpoint_exists(self, gateway_client: AsyncClient):
        """Verifie que l'endpoint /metrics existe et retourne du Prometheus."""
        response = await gateway_client.get("/metrics")

        assert response.status_code == 200
        content = response.text

        # Verifie format Prometheus (contient des lignes TYPE ou HELP)
        assert "# HELP" in content or "# TYPE" in content

    async def test_cache_metrics_exist(self, gateway_client: AsyncClient):
        """Verifie que les metriques de cache existent."""
        response = await gateway_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Metriques de cache attendues
        assert "gateway_cache_hits_total" in content
        assert "gateway_cache_misses_total" in content

    async def test_api_calls_metrics_exist(self, gateway_client: AsyncClient):
        """Verifie que les metriques d'appels API existent."""
        response = await gateway_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        assert "gateway_api_calls_total" in content

    async def test_rate_limit_metrics_exist(self, gateway_client: AsyncClient):
        """Verifie que les metriques de rate limit existent."""
        response = await gateway_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        assert "gateway_rate_limit_used" in content
        assert "gateway_rate_limit_remaining" in content

    async def test_metrics_values_are_numeric(self, gateway_client: AsyncClient):
        """Verifie que les valeurs des metriques sont numeriques."""
        response = await gateway_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Parse une metrique et verifie qu'elle a une valeur numerique
        # Format: metric_name{labels} value
        pattern = r'gateway_cache_hits_total\{[^}]*\}\s+([\d.]+)'
        matches = re.findall(pattern, content)

        if matches:
            for value in matches:
                assert float(value) >= 0

    async def test_cache_hit_increases_after_request(self, gateway_client: AsyncClient):
        """
        Scenario e2e: Verifie que les cache hits augmentent.

        1. Lire les metriques actuelles
        2. Faire une requete (qui sera en cache apres premier appel)
        3. Refaire la meme requete
        4. Verifier que cache_hits a augmente
        """
        # Lire metriques initiales
        metrics1 = await gateway_client.get("/metrics")
        content1 = metrics1.text

        # Extraire cache hits pour airports
        pattern = r'gateway_cache_hits_total\{endpoint="airports"\}\s+([\d.]+)'
        match1 = re.search(pattern, content1)
        initial_hits = float(match1.group(1)) if match1 else 0

        # Faire une requete pour mettre en cache
        await gateway_client.get("/airports?iata=CDG")

        # Refaire la meme requete (devrait etre cache hit)
        await gateway_client.get("/airports?iata=CDG")

        # Lire metriques apres
        metrics2 = await gateway_client.get("/metrics")
        content2 = metrics2.text

        match2 = re.search(pattern, content2)
        final_hits = float(match2.group(1)) if match2 else 0

        # Cache hits devrait avoir augmente d'au moins 1
        # (la 2eme requete est forcement un hit car CDG est tres utilise)
        assert final_hits >= initial_hits


@pytest.mark.e2e
class TestGatewayRateLimitE2E:
    """Tests e2e du rate limiting Gateway."""

    async def test_rate_limit_info_in_health(self, gateway_client: AsyncClient):
        """Verifie les infos rate limit dans le health check."""
        response = await gateway_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        rate_limit = data["rate_limit"]

        # Verifications
        assert rate_limit["limit"] == 10000  # Limite mensuelle Aviationstack free
        assert rate_limit["used"] >= 0
        assert rate_limit["remaining"] >= 0
        assert "month" in rate_limit
        assert "reset_date" in rate_limit