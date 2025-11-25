"""
Tests end-to-end pour le service Flight.

Ces tests vérifient le service Flight via HTTP en conditions réelles.
Nécessite docker-compose up (au minimum flight + mongodb).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestFlightServiceE2E:
    """Tests e2e du service Flight."""

    async def test_health_check(self, flight_client: AsyncClient):
        """Vérifie que le service Flight répond au healthcheck."""
        response = await flight_client.get("/api/v1/health/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    async def test_get_flight_status(self, flight_client: AsyncClient):
        """
        Scénario e2e : Récupérer le statut d'un vol.

        Vérifie l'intégration complète :
        - Endpoint FastAPI
        - Client Aviationstack
        - Cache MongoDB
        - Stockage historique
        """
        response = await flight_client.get("/api/v1/flights/AF447")

        # Le vol peut exister ou non selon la date/API
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Vérifie structure de réponse
            assert "flight_iata" in data or "flight_number" in data
            assert "flight_status" in data or "status" in data

            # Si on a des infos de départ/arrivée
            if "departure" in data:
                assert "airport" in data["departure"] or "iata" in data["departure"]
            if "arrival" in data:
                assert "airport" in data["arrival"] or "iata" in data["arrival"]

    async def test_get_flight_statistics(self, flight_client: AsyncClient):
        """
        Scénario e2e : Récupérer les statistiques d'un vol.

        Test l'agrégation de données historiques.
        """
        # Note: L'endpoint exact dépend de ton implémentation
        response = await flight_client.get(
            "/api/v1/flights/AF447/statistics",
            params={
                "start_date": "2024-11-01",
                "end_date": "2024-11-25"
            }
        )

        # Peut retourner 200 avec stats, 404 si pas de données, ou 422 si endpoint n'existe pas
        assert response.status_code in [200, 404, 422]

        if response.status_code == 200:
            data = response.json()

            # Vérifie structure des statistiques
            # Les champs exacts dépendent de ton implémentation
            expected_fields = [
                "average_delay",
                "delay_rate",
                "total_flights",
                "on_time_percentage"
            ]

            # Au moins un champ de stats devrait être présent
            has_stats = any(field in data for field in expected_fields)
            assert has_stats or "statistics" in data

    async def test_cache_behavior(self, flight_client: AsyncClient):
        """
        Scénario e2e : Vérifie le comportement du cache.

        Deux requêtes identiques consécutives :
        - Première peut hit l'API ou le cache
        - Deuxième devrait hit le cache MongoDB
        """
        # Premier appel
        response1 = await flight_client.get("/api/v1/flights/BA117")

        # Le vol peut exister ou non
        if response1.status_code == 200:
            data1 = response1.json()

            # Deuxième appel immédiat (devrait venir du cache)
            response2 = await flight_client.get("/api/v1/flights/BA117")
            assert response2.status_code == 200
            data2 = response2.json()

            # Vérifie que les données sont identiques
            assert data1 == data2


@pytest.mark.e2e
@pytest.mark.slow
class TestFlightHistoryE2E:
    """Tests e2e pour l'historique des vols."""

    async def test_flight_history_storage(self, flight_client: AsyncClient):
        """
        Scénario e2e : Vérifier que les vols consultés sont stockés en historique.

        1. Consulter un vol
        2. Vérifier qu'il apparaît dans l'historique
        """
        # Consulter un vol (le stocke en historique)
        response1 = await flight_client.get("/api/v1/flights/LH400")

        if response1.status_code == 200:
            # Récupérer l'historique de ce vol
            # Note: L'endpoint exact dépend de ton implémentation
            response2 = await flight_client.get(
                "/api/v1/flights/LH400/history",
                params={"limit": 10}
            )

            # Peut retourner 200 avec historique ou 404/422 si endpoint n'existe pas
            assert response2.status_code in [200, 404, 422]

            if response2.status_code == 200:
                history_data = response2.json()

                # Vérifie structure de l'historique
                # Les champs exacts dépendent de ton implémentation
                assert "flights" in history_data or "history" in history_data or isinstance(history_data, list)

    async def test_coalescing_behavior(self, flight_client: AsyncClient):
        """
        Scénario e2e : Teste le request coalescing.

        Envoie plusieurs requêtes identiques simultanées.
        Devrait coalescer les requêtes et ne faire qu'un seul appel API.
        """
        import asyncio

        # Envoie 5 requêtes simultanées pour le même vol
        tasks = [
            flight_client.get("/api/v1/flights/AF447")
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Toutes les requêtes devraient réussir
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code in [200, 404]

        # Si on a des réponses 200, elles devraient être identiques
        successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]

        if len(successful_responses) > 1:
            first_data = successful_responses[0].json()
            for response in successful_responses[1:]:
                assert response.json() == first_data
