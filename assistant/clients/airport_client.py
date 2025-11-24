"""
Client HTTP asynchrone pour le microservice Airport.

Encapsule tous les appels HTTP vers l'API Airport.
Supporte le mode DEMO avec données mockées.
"""

import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AirportClient:
    """
    Client HTTP pour le microservice Airport.

    Attributes:
        base_url: URL de base de l'API Airport
        timeout: Timeout des requêtes HTTP (en secondes)
        demo_mode: Si True, retourne des données mockées au lieu d'appeler l'API
    """

    def __init__(self, base_url: str, timeout: int = 30, demo_mode: bool = False):
        """
        Initialise le client Airport.

        Args:
            base_url: URL du microservice Airport (ex: http://airport:8001/api/v1)
            timeout: Timeout des requêtes en secondes
            demo_mode: Active le mode démo avec données mockées
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.demo_mode = demo_mode
        self._client: Optional[httpx.AsyncClient] = None

        if self.demo_mode:
            logger.info("AirportClient initialized in DEMO MODE - using mock data")

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
        Effectue une requête GET vers l'API Airport.

        Args:
            endpoint: Endpoint à appeler (ex: /airports/CDG)
            params: Paramètres de query string

        Returns:
            Réponse JSON parsée

        Raises:
            httpx.HTTPError: Erreur HTTP
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Airport API call: GET {url} with params {params}")

        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_airport_by_iata(self, iata: str) -> Dict[str, Any]:
        """
        Récupère un aéroport par code IATA.

        Args:
            iata: Code IATA de l'aéroport (ex: CDG)

        Returns:
            Données de l'aéroport
        """
        # Mode DEMO : retourner données mockées
        if self.demo_mode:
            from tools.mock_data import MOCK_AIRPORTS
            airport_data = MOCK_AIRPORTS.get(iata.upper())
            if airport_data:
                logger.info(f"DEMO MODE: Returning mock data for airport {iata}")
                return {"data": airport_data}
            else:
                logger.warning(f"DEMO MODE: No mock data for airport {iata}")
                return {"error": f"Airport {iata} not found in mock data"}

        return await self._get(f"/airports/{iata.upper()}")

    async def search_airports_by_name(
        self,
        name: str,
        country_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche des aéroports par nom de lieu.

        Args:
            name: Nom de ville ou région
            country_code: Code pays ISO (ex: FR)

        Returns:
            Liste d'aéroports
        """
        params = {"name": name}
        if country_code:
            params["country_code"] = country_code.upper()

        return await self._get("/airports/search", params=params)

    async def get_nearest_airport_by_coords(
        self,
        latitude: float,
        longitude: float,
        country_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trouve l'aéroport le plus proche de coordonnées GPS.

        Args:
            latitude: Latitude
            longitude: Longitude
            country_code: Code pays ISO

        Returns:
            Aéroport le plus proche
        """
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        if country_code:
            params["country_code"] = country_code.upper()

        return await self._get("/airports/nearest-by-coords", params=params)

    async def get_nearest_airport_by_address(
        self,
        address: str,
        country_code: str
    ) -> Dict[str, Any]:
        """
        Trouve l'aéroport le plus proche d'une adresse.

        Args:
            address: Adresse textuelle
            country_code: Code pays ISO (requis)

        Returns:
            Aéroport le plus proche
        """
        # Mode DEMO : retourner données mockées
        if self.demo_mode:
            from tools.mock_data import MOCK_AIRPORTS
            # Détecte si c'est une recherche sur Lille
            if "lille" in address.lower():
                airport_data = MOCK_AIRPORTS.get("nearest_lille")
                if airport_data:
                    logger.info(f"DEMO MODE: Returning mock nearest airport for {address}")
                    return {"data": airport_data}

            logger.warning(f"DEMO MODE: No mock data for address {address}")
            return {"error": f"No mock data for address {address}"}

        params = {
            "address": address,
            "country_code": country_code.upper()
        }
        return await self._get("/airports/nearest-by-address", params=params)

    async def get_departures(
        self,
        iata: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère les vols au départ d'un aéroport.

        Args:
            iata: Code IATA de l'aéroport
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            Liste de vols au départ
        """
        # Mode DEMO : retourner données mockées
        if self.demo_mode:
            from tools.mock_data import MOCK_DEPARTURES
            departures_data = MOCK_DEPARTURES.get(iata.upper())
            if departures_data:
                logger.info(f"DEMO MODE: Returning mock departures for {iata}")
                # Applique limit et offset
                start = offset
                end = offset + limit
                return {"data": departures_data[start:end], "total": len(departures_data)}
            else:
                logger.warning(f"DEMO MODE: No mock departures for {iata}")
                return {"data": [], "total": 0}

        params = {
            "limit": limit,
            "offset": offset
        }
        return await self._get(f"/airports/{iata.upper()}/departures", params=params)

    async def get_arrivals(
        self,
        iata: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère les vols à l'arrivée d'un aéroport.

        Args:
            iata: Code IATA de l'aéroport
            limit: Nombre max de résultats
            offset: Décalage pour pagination

        Returns:
            Liste de vols à l'arrivée
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        return await self._get(f"/airports/{iata.upper()}/arrivals", params=params)