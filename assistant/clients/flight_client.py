"""
Client HTTP asynchrone pour le microservice Flight.

Encapsule tous les appels HTTP vers l'API Flight.
"""

import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FlightClient:
    """
    Client HTTP pour le microservice Flight.

    Attributes:
        base_url: URL de base de l'API Flight
        timeout: Timeout des requêtes HTTP (en secondes)
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialise le client Flight.

        Args:
            base_url: URL du microservice Flight (ex: http://flight:8002/api/v1)
            timeout: Timeout des requêtes en secondes
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête GET vers l'API Flight.

        Args:
            endpoint: Endpoint à appeler (ex: /flights/AF447)
            params: Paramètres de query string

        Returns:
            Réponse JSON parsée, ou dict avec "error" si 404

        Raises:
            httpx.HTTPError: Erreur HTTP (sauf 404)
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Flight API call: GET {url} with params {params}")

        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        response = await self._client.get(url, params=params)

        # Gestion gracieuse des 404 pour LangGraph 1.0 compatibility
        # L'assistant doit pouvoir dire "vol non trouvé" au lieu de crasher
        if response.status_code == 404:
            logger.warning(f"Flight API returned 404 for {endpoint}")
            return {"error": f"Resource not found: {endpoint}"}

        response.raise_for_status()
        return response.json()

    async def get_flight_status(self, flight_iata: str) -> Dict[str, Any]:
        """
        Récupère le statut en temps réel d'un vol.

        Args:
            flight_iata: Code IATA du vol (ex: AF447)

        Returns:
            Statut du vol
        """
        return await self._get(f"/flights/{flight_iata.upper()}")

    async def get_flight_history(
        self,
        flight_iata: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Récupère l'historique d'un vol sur une période.

        Args:
            flight_iata: Code IATA du vol
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)

        Returns:
            Historique du vol
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._get(f"/flights/{flight_iata.upper()}/history", params=params)

    async def get_flight_statistics(
        self,
        flight_iata: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Récupère les statistiques d'un vol sur une période.

        Args:
            flight_iata: Code IATA du vol
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)

        Returns:
            Statistiques du vol
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._get(f"/flights/{flight_iata.upper()}/statistics", params=params)