"""
Client asynchrone pour l'API Aviationstack.

Responsabilités :
- Appels HTTP vers l'API
- Gestion des erreurs et retry
- Conversion des réponses en modèles domaine
- Logging des appels (sans exposer les secrets)
- Rate limiting pour respecter les quotas API
"""

import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from config.settings import settings
from models import Airport, Flight
from monitoring.metrics import api_calls

logger = logging.getLogger(__name__)


class AviationstackError(Exception):
    """Erreur spécifique à l'API Aviationstack."""
    pass


class RateLimiter:
    """
    Limiteur simple pour l'API gratuite (100 calls/mois).
    
    Note: En production, utiliser Redis pour partager entre instances.
    """
    
    def __init__(self, max_calls: int = 100, period_days: int = 30):
        self.max_calls = max_calls
        self.period_days = period_days
        self.calls = []
    
    async def check_and_add(self):
        """
        Vérifie si on peut faire un appel et l'enregistre.
        
        Raises:
            AviationstackError: Si limite atteinte
        """
        now = datetime.now()
        cutoff = now - timedelta(days=self.period_days)
        
        # Garde seulement les appels récents
        self.calls = [c for c in self.calls if c > cutoff]
        
        if len(self.calls) >= self.max_calls:
            raise AviationstackError(
                f"Rate limit atteinte : {self.max_calls} appels/{self.period_days} jours. "
                f"Prochain appel possible dans {self._time_until_next_call()}"
            )
        
        self.calls.append(now)
        logger.debug(f"API calls: {len(self.calls)}/{self.max_calls} dans les {self.period_days} derniers jours")
    
    def _time_until_next_call(self) -> str:
        """Calcule le temps jusqu'au prochain appel possible."""
        if not self.calls:
            return "maintenant"
        
        oldest_call = min(self.calls)
        next_available = oldest_call + timedelta(days=self.period_days)
        delta = next_available - datetime.now()
        
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}min"


class AviationstackClient:
    """
    Client asynchrone pour l'API Aviationstack.
    
    Usage:
        async with AviationstackClient() as client:
            airport = await client.get_airport_by_iata("CDG")
    """
    
    def __init__(self, enable_rate_limit: bool = True):
        """
        Initialise le client avec les settings.
        
        Args:
            enable_rate_limit: Active/désactive le rate limiting (utile pour tests)
        """
        self.api_key = settings.aviationstack_api_key
        self.base_url = settings.aviationstack_base_url
        self.timeout = settings.aviationstack_timeout
        
        # Rate limiter (100 calls/mois pour l'API gratuite)
        self.rate_limiter = RateLimiter() if enable_rate_limit else None
        
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
        logger.debug("Opening Aviationstack client")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager : sortie, ferme le client."""
        await self.close()
        
    async def close(self):
        """Ferme le client HTTP proprement."""
        logger.debug("Closing Aviationstack client")
        await self.client.aclose()
        
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Fait une requête à l'API avec retry automatique.
        
        Args:
            endpoint: Endpoint de l'API (ex: "airports", "flights")
            params: Paramètres de la requête
            retry_count: Nombre de tentatives
            
        Returns:
            Dict avec la réponse JSON
            
        Raises:
            AviationstackError: Si l'API retourne une erreur ou limite atteinte
        """
        # Vérifie le rate limit
        if self.rate_limiter:
            await self.rate_limiter.check_and_add()
        
        url = f"{self.base_url}/{endpoint}"
        
        # Ajoute toujours la clé API
        if params is None:
            params = {}
        params["access_key"] = self.api_key
        
        # Log de la requête SANS la clé complète
        safe_params = {k: v for k, v in params.items() if k != "access_key"}
        safe_params["access_key"] = f"{self.api_key[:8]}..."
        logger.info(f"API call: GET {endpoint} with params: {safe_params}")
        
        # Retry loop avec exponential backoff
        last_error = None
        for attempt in range(retry_count):
            try:
                response = await self.client.get(url, params=params)
                
                # Log le status HTTP
                logger.debug(f"Response status: {response.status_code}")
                
                # Vérifie le status HTTP
                response.raise_for_status()
                
                # Parse JSON
                data = response.json()
                
                # Vérifie les erreurs API
                if "error" in data:
                    error_info = data["error"]
                    error_code = error_info.get("code", "UNKNOWN")
                    error_msg = error_info.get("message", "Unknown error")
                    
                    # Gestion spécifique par code d'erreur
                    if error_code == 211:  # Quota exceeded
                        raise AviationstackError(f"Quota API dépassé : {error_msg}")
                    elif error_code == 101:  # Invalid API key
                        raise AviationstackError(f"Clé API invalide : {error_msg}")
                    else:
                        raise AviationstackError(f"Erreur API [{error_code}]: {error_msg}")
                
                # Log succès
                result_count = len(data.get('data', []))
                logger.info(f"API success: {endpoint} returned {result_count} results")

                # Métrique Prometheus : appel API réussi
                api_calls.labels(service="airport", endpoint=endpoint, status="success").inc()

                return data
                
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:  # Rate limited
                    wait_time = min(60, 2 ** (attempt + 2))  # Max 60s
                    logger.warning(f"Rate limited (429), waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
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
                    
        # Si on arrive ici, toutes les tentatives ont échoué
        # Métrique Prometheus : appel API échoué
        api_calls.labels(service="airport", endpoint=endpoint, status="error").inc()
        raise AviationstackError(f"Échec après {retry_count} tentatives : {last_error}")
    
    async def get_airport_by_iata(self, iata_code: str) -> Optional[Airport]:
        """
        Récupère un aéroport par son code IATA.
        
        Args:
            iata_code: Code IATA (ex: "CDG")
            
        Returns:
            Airport ou None si non trouvé
            
        Example:
            >>> airport = await client.get_airport_by_iata("CDG")
            >>> print(airport.name)  # "Charles de Gaulle"
        """
        try:
            response = await self._make_request(
                "airports",
                params={"iata_code": iata_code.upper()}
            )
            
            if response.get("data") and len(response["data"]) > 0:
                # Convertit directement en modèle domaine
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
                
            Example:
                >>> airports = await client.search_airports(query="Paris", country="FR")
                >>> for airport in airports:
                ...     print(f"{airport.iata_code}: {airport.name}")
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
                
            Example:
                >>> flights = await client.get_flights(
                ...     dep_iata="CDG",
                ...     flight_status="scheduled"
                ... )
            """
            params: Dict[str, Any] = {"limit": min(limit, 100)}
            
            # Ajoute les filtres si fournis
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
        """
        Récupère les vols au départ d'un aéroport.
        
        Raccourci pour get_flights(dep_iata=airport_iata)
        
        Args:
            airport_iata: Code IATA de l'aéroport
            limit: Nombre max de résultats
            
        Returns:
            Liste des vols au départ
        """
        logger.debug(f"Récupération des départs de {airport_iata}")
        return await self.get_flights(dep_iata=airport_iata, limit=limit)

    async def get_arrivals(self, airport_iata: str, limit: int = 10) -> List[Flight]:
        """
        Récupère les vols à l'arrivée d'un aéroport.
        
        Raccourci pour get_flights(arr_iata=airport_iata)
        
        Args:
            airport_iata: Code IATA de l'aéroport
            limit: Nombre max de résultats
            
        Returns:
            Liste des vols à l'arrivée
        """
        logger.debug(f"Récupération des arrivées à {airport_iata}")
        return await self.get_flights(arr_iata=airport_iata, limit=limit)