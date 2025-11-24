"""
Client HTTP asynchrone pour le microservice Flight.

Encapsule tous les appels HTTP vers l'API Flight.
Supporte le mode DEMO avec données mockées.
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
        demo_mode: Si True, retourne des données mockées au lieu d'appeler l'API
    """

    def __init__(self, base_url: str, timeout: int = 30, demo_mode: bool = False):
        """
        Initialise le client Flight.

        Args:
            base_url: URL du microservice Flight (ex: http://flight:8002/api/v1)
            timeout: Timeout des requêtes en secondes
            demo_mode: Active le mode démo avec données mockées
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.demo_mode = demo_mode
        self._client: Optional[httpx.AsyncClient] = None

        if self.demo_mode:
            logger.info("FlightClient initialized in DEMO MODE - using mock data")

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
            Réponse JSON parsée

        Raises:
            httpx.HTTPError: Erreur HTTP
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Flight API call: GET {url} with params {params}")

        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        response = await self._client.get(url, params=params)
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
        # Mode DEMO : retourner données mockées
        if self.demo_mode:
            from tools.mock_data import MOCK_FLIGHTS
            flight_data = MOCK_FLIGHTS.get(flight_iata.upper())
            if flight_data:
                logger.info(f"DEMO MODE: Returning mock data for flight {flight_iata}")
                return {"data": flight_data}
            else:
                logger.warning(f"DEMO MODE: No mock data for flight {flight_iata}")
                return {"error": f"Flight {flight_iata} not found in mock data"}

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
        # Mode DEMO : retourner statistiques mockées
        if self.demo_mode:
            from tools.mock_data import MOCK_FLIGHT_STATISTICS
            stats_data = MOCK_FLIGHT_STATISTICS.get(flight_iata.upper())
            if stats_data:
                logger.info(f"DEMO MODE: Returning mock statistics for flight {flight_iata}")
                return {"data": stats_data}
            else:
                logger.warning(f"DEMO MODE: No mock statistics for flight {flight_iata}")
                return {"error": f"Statistics for flight {flight_iata} not found in mock data"}

        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._get(f"/flights/{flight_iata.upper()}/statistics", params=params)