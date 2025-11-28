"""
Client pour le Gateway Aviationstack.

Responsabilités :
- Appels HTTP vers le Gateway (pas directement Aviationstack)
- Conversion des réponses en modèles domaine
- Logging des appels

Note: Le Gateway gère le rate limiting, cache, circuit breaker et coalescing.
Ce client est simplifié car toute la logique complexe est centralisée dans le Gateway.
"""

import httpx
import asyncio
from typing import List, Optional, Dict, Any
import logging

from config.settings import settings
from models import Airport, Flight

logger = logging.getLogger(__name__)


class AviationstackError(Exception):
    """Erreur spécifique à l'API Aviationstack/Gateway."""
    pass


class AviationstackClient:
    """
    Client asynchrone pour le Gateway Aviationstack.

    Le Gateway (port 8004) centralise :
    - Rate limiting (10000 calls/mois)
    - Cache MongoDB
    - Circuit breaker
    - Request coalescing

    Usage:
        async with AviationstackClient() as client:
            airport = await client.get_airport_by_iata("CDG")
    """

    def __init__(self):
        """Initialise le client vers le Gateway."""
        self.base_url = settings.gateway_url
        self.timeout = settings.aviationstack_timeout

        logger.info(f"🌐 AviationstackClient -> Gateway: {self.base_url}")

        # Client HTTP réutilisable avec pool de connexions
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            ),
            headers={
                "User-Agent": f"HelloMira-Airport-Service/{settings.app_version}"
            }
        )

    async def __aenter__(self):
        """Context manager : entrée."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager : sortie, ferme le client."""
        await self.close()

    async def close(self):
        """Ferme le client HTTP proprement."""
        await self.client.aclose()

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Fait une requête au Gateway avec retry automatique.

        Args:
            endpoint: Endpoint (ex: "airports", "flights")
            params: Paramètres de la requête
            retry_count: Nombre de tentatives

        Returns:
            Dict avec la réponse JSON

        Raises:
            AviationstackError: Si le Gateway retourne une erreur
        """
        url = f"{self.base_url}/{endpoint}"

        if params is None:
            params = {}

        logger.info(f"Gateway call: GET {endpoint} params={params}")

        # Retry loop avec exponential backoff
        last_error = None
        for attempt in range(retry_count):
            try:
                response = await self.client.get(url, params=params)

                # Gestion des codes HTTP spéciaux du Gateway
                if response.status_code == 429:
                    # Rate limit exceeded (Gateway)
                    raise AviationstackError("Quota API mensuel atteint (rate limit)")

                if response.status_code == 503:
                    # Circuit breaker open
                    data = response.json()
                    detail = data.get("detail", {})
                    retry_after = detail.get("retry_after") if isinstance(detail, dict) else None
                    raise AviationstackError(
                        f"Service temporairement indisponible (circuit breaker). "
                        f"Retry après: {retry_after}"
                    )

                response.raise_for_status()
                data = response.json()

                # Vérifie les erreurs API
                if "error" in data:
                    error_info = data["error"]
                    if isinstance(error_info, dict):
                        error_code = error_info.get("code", "UNKNOWN")
                        error_msg = error_info.get("message", "Unknown error")
                    else:
                        error_code = "UNKNOWN"
                        error_msg = str(error_info)
                    raise AviationstackError(f"Erreur API [{error_code}]: {error_msg}")

                # Succès
                result_count = len(data.get('data', []))
                logger.info(f"Gateway success: {endpoint} returned {result_count} results")

                return data

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    raise AviationstackError("Quota API mensuel atteint (rate limit)")
                elif attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{retry_count}), "
                        f"status {e.response.status_code}, retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {retry_count} attempts: {e}")

            except httpx.RequestError as e:
                last_error = e
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Network error (attempt {attempt + 1}/{retry_count}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Network error after {retry_count} attempts: {e}")

        raise AviationstackError(f"Échec après {retry_count} tentatives : {last_error}")

    # ========================================================================
    # AIRPORTS
    # ========================================================================

    async def get_airport_by_iata(self, iata_code: str) -> Optional[Airport]:
        """
        Récupère un aéroport par son code IATA.

        Args:
            iata_code: Code IATA (ex: "CDG")

        Returns:
            Airport ou None si non trouvé
        """
        try:
            response = await self._make_request(
                "airports",
                params={"iata_code": iata_code.upper()}
            )

            if response.get("data") and len(response["data"]) > 0:
                return Airport.from_api_response(response["data"][0])

            logger.warning(f"Aucun aéroport trouvé pour le code IATA : {iata_code}")
            return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'aéroport {iata_code}: {e}")
            raise

    async def search_airports(
        self,
        query: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 10
    ) -> List[Airport]:
        """
        Recherche des aéroports.

        Args:
            query: Texte de recherche (nom, ville)
            country: Code pays ISO2 (ex: "FR")
            limit: Nombre max de résultats

        Returns:
            Liste d'aéroports (peut être vide)
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}

        if query:
            params["search"] = query
        if country:
            params["country_iso2"] = country.upper()

        response = await self._make_request("airports", params)

        airports = []
        for airport_data in response.get("data", []):
            try:
                airports.append(Airport.from_api_response(airport_data))
            except Exception as e:
                logger.warning(f"Échec du parsing d'un aéroport : {e}")
                continue

        logger.info(f"Recherche aéroports : {len(airports)} résultats")
        return airports

    # ========================================================================
    # FLIGHTS
    # ========================================================================

    async def get_flights(
        self,
        flight_iata: Optional[str] = None,
        dep_iata: Optional[str] = None,
        arr_iata: Optional[str] = None,
        airline_iata: Optional[str] = None,
        flight_status: Optional[str] = None,
        limit: int = 10
    ) -> List[Flight]:
        """
        Récupère des vols avec filtres.

        Args:
            flight_iata: Code IATA du vol (ex: "AF123")
            dep_iata: Code IATA aéroport départ
            arr_iata: Code IATA aéroport arrivée
            airline_iata: Code IATA compagnie (ex: "AF")
            flight_status: Status (scheduled, active, landed, cancelled)
            limit: Nombre max de résultats

        Returns:
            Liste de vols (peut être vide)
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}

        if flight_iata:
            params["flight_iata"] = flight_iata.upper()
        if dep_iata:
            params["dep_iata"] = dep_iata.upper()
        if arr_iata:
            params["arr_iata"] = arr_iata.upper()
        if airline_iata:
            params["airline_iata"] = airline_iata.upper()
        if flight_status:
            params["flight_status"] = flight_status.lower()

        response = await self._make_request("flights", params)

        flights = []
        for flight_data in response.get("data", []):
            try:
                flights.append(Flight.from_api_response(flight_data))
            except Exception as e:
                logger.warning(f"Échec du parsing d'un vol : {e}")
                continue

        logger.info(f"Recherche vols : {len(flights)} résultats")
        return flights

    async def get_departures(self, airport_iata: str, limit: int = 10) -> List[Flight]:
        """Récupère les vols au départ d'un aéroport."""
        return await self.get_flights(dep_iata=airport_iata, limit=limit)

    async def get_arrivals(self, airport_iata: str, limit: int = 10) -> List[Flight]:
        """Récupère les vols à l'arrivée d'un aéroport."""
        return await self.get_flights(arr_iata=airport_iata, limit=limit)
