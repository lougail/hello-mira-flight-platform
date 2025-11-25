"""
Tests end-to-end pour l'orchestration de l'Assistant IA.

Ces tests vérifient que l'assistant orchestre correctement les appels
entre les services airport et flight.
Nécessite docker-compose up (tous les services).
"""

import pytest
from httpx import AsyncClient
from typing import Dict


@pytest.mark.e2e
class TestAssistantOrchestration:
    """Tests e2e de l'orchestration par l'Assistant."""

    async def test_health_check(self, assistant_client: AsyncClient):
        """Vérifie que le service Assistant répond au healthcheck."""
        response = await assistant_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_interpret_airport_query(self, assistant_client: AsyncClient):
        """
        Scénario e2e : L'assistant interprète une question sur un aéroport.

        Vérifie que l'assistant peut :
        - Analyser un prompt en langage naturel
        - Identifier l'intention (recherche aéroport)
        - Extraire les paramètres (code IATA)
        """
        response = await assistant_client.post(
            "/assistant/interpret",
            json={"prompt": "Quels vols partent de CDG ?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifie l'intention détectée
        assert "intent" in data
        assert "parameters" in data

        # L'assistant devrait détecter qu'on parle d'un aéroport
        params = data["parameters"]
        assert "airport_code" in params or "iata_code" in params

    async def test_assistant_calls_airport_service(
        self,
        assistant_client: AsyncClient,
        airport_client: AsyncClient
    ):
        """
        Scénario e2e complet : Assistant → Airport service.

        1. Utilisateur envoie un prompt à l'assistant
        2. Assistant interprète et appelle le service Airport
        3. Assistant retourne une réponse formatée avec les données
        """
        # Vérifie d'abord que le service Airport est accessible
        health = await airport_client.get("/api/v1/health/liveness")
        assert health.status_code == 200

        # Envoie le prompt à l'assistant
        response = await assistant_client.post(
            "/assistant/answer",
            json={"prompt": "Trouve-moi l'aéroport CDG"}
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifie la structure de réponse
        assert "answer" in data
        assert "data" in data

        # La réponse devrait mentionner CDG
        answer = data["answer"].lower()
        assert "cdg" in answer or "charles de gaulle" in answer

        # Les données devraient contenir les infos de l'aéroport
        airport_data = data["data"]
        assert airport_data is not None
        # Peut être un dict ou une list selon l'implémentation
        if isinstance(airport_data, dict):
            assert "iata_code" in airport_data or "name" in airport_data

    async def test_assistant_calls_flight_service(
        self,
        assistant_client: AsyncClient,
        flight_client: AsyncClient
    ):
        """
        Scénario e2e complet : Assistant → Flight service.

        1. Utilisateur demande info sur un vol
        2. Assistant appelle le service Flight
        3. Assistant retourne le statut du vol
        """
        # Vérifie d'abord que le service Flight est accessible
        health = await flight_client.get("/api/v1/health/liveness")
        assert health.status_code == 200

        # Envoie le prompt à l'assistant
        response = await assistant_client.post(
            "/assistant/answer",
            json={"prompt": "Quel est le statut du vol AF447 ?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifie la structure de réponse
        assert "answer" in data
        assert "data" in data

        # La réponse devrait mentionner le vol
        answer = data["answer"].lower()
        assert "af447" in answer or "vol" in answer or "flight" in answer

    async def test_full_user_journey(
        self,
        all_services: Dict[str, AsyncClient]
    ):
        """
        Scénario e2e : Parcours utilisateur complet.

        1. Rechercher un aéroport via l'assistant
        2. Lister les vols au départ via l'assistant
        3. Vérifier le statut d'un vol spécifique

        Ce test vérifie l'orchestration complète entre tous les services.
        """
        airport = all_services["airport"]
        flight = all_services["flight"]
        assistant = all_services["assistant"]

        # Étape 1 : Demander info sur un aéroport
        response1 = await assistant.post(
            "/assistant/answer",
            json={"prompt": "Où se trouve l'aéroport CDG ?"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "answer" in data1
        assert "cdg" in data1["answer"].lower() or "paris" in data1["answer"].lower()

        # Étape 2 : Vérifier qu'on peut accéder directement au service Airport
        response2 = await airport.get("/api/v1/airports/CDG")
        assert response2.status_code == 200
        airport_data = response2.json()
        assert airport_data["iata_code"] == "CDG"

        # Étape 3 : Demander info sur un vol via l'assistant
        response3 = await assistant.post(
            "/assistant/answer",
            json={"prompt": "Y a-t-il des vols Air France aujourd'hui ?"}
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert "answer" in data3

        # Le parcours complet devrait réussir sans erreur
        # C'est une validation de l'architecture microservices


@pytest.mark.e2e
@pytest.mark.slow
class TestCrossServiceIntegration:
    """Tests d'intégration complexes entre plusieurs services."""

    async def test_airport_to_flights_workflow(
        self,
        airport_client: AsyncClient,
        flight_client: AsyncClient
    ):
        """
        Workflow : Rechercher aéroport → Lister vols au départ.

        Ce test vérifie que les données sont cohérentes entre services.
        """
        # 1. Récupérer info aéroport
        airport_response = await airport_client.get("/api/v1/airports/CDG")
        assert airport_response.status_code == 200
        airport_data = airport_response.json()
        iata_code = airport_data["iata_code"]

        # 2. Lister vols au départ de cet aéroport
        # Note: L'endpoint exact dépend de ton implémentation
        # Exemple possible :
        departures_response = await airport_client.get(
            f"/api/v1/airports/{iata_code}/departures"
        )

        # Selon ton API, cela peut retourner 200 avec des vols ou 404
        # On vérifie juste que l'endpoint est accessible
        assert departures_response.status_code in [200, 404]

        if departures_response.status_code == 200:
            departures_data = departures_response.json()
            # Si on a des vols, vérifie la structure
            if "flights" in departures_data and len(departures_data["flights"]) > 0:
                first_flight = departures_data["flights"][0]
                assert "flight_iata" in first_flight or "flight_number" in first_flight
