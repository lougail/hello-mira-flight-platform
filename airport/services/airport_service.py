"""
Service métier principal pour les aéroports.

Responsabilités :
- Orchestrer les appels au client Aviationstack
- Utiliser le cache pour optimiser les appels API
- Trouver l'aéroport le plus proche (coordonnées ou adresse)
- Lister les vols (départs/arrivées)

Architecture :
Ce service ORCHESTRE et délègue :
- Cache → CacheService
- Géocodage/Distance → GeocodingService
- Appels API → AviationstackClient
"""

import logging
from typing import List, Optional

from clients.aviationstack_client import AviationstackClient
from models import Airport, Flight
from .cache_service import CacheService
from .geocoding_service import GeocodingService

logger = logging.getLogger(__name__)


class AirportService:
    """
    Service principal pour gérer les aéroports.
    
    Usage:
        service = AirportService(client, cache_service, geocoding_service)
        airport = await service.get_airport_by_iata("CDG")
    """
    
    def __init__(
        self,
        aviationstack_client: AviationstackClient,
        cache_service: Optional[CacheService] = None,
        geocoding_service: Optional[GeocodingService] = None
    ):
        """
        Initialise le service avec ses dépendances.
        
        Args:
            aviationstack_client: Client pour l'API Aviationstack
            cache_service: Service de cache (optionnel)
            geocoding_service: Service de géocodage (optionnel)
        """
        self.client = aviationstack_client
        self.cache = cache_service
        self.geocoding = geocoding_service or GeocodingService()
    
    # ========================================================================
    # RECHERCHE D'AÉROPORTS
    # ========================================================================
    
    async def get_airport_by_iata(self, iata_code: str) -> Optional[Airport]:
        """
        Récupère un aéroport par son code IATA.
        
        Utilise le cache si disponible pour optimiser.
        
        Args:
            iata_code: Code IATA (ex: "CDG")
            
        Returns:
            Airport ou None si non trouvé
            
        Example:
            >>> airport = await service.get_airport_by_iata("CDG")
            >>> if airport:
            ...     print(f"{airport.name} - {airport.city}")
        """
        iata_code = iata_code.upper()
        cache_key = f"airport:{iata_code}"
        
        # 1. Essaye le cache
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Airport {iata_code} trouvé dans le cache")
                return Airport(**cached_data)
        
        # 2. Appelle l'API
        logger.info(f"Récupération de l'aéroport {iata_code} depuis l'API")
        airport = await self.client.get_airport_by_iata(iata_code)
        
        if not airport:
            logger.warning(f"Aéroport {iata_code} non trouvé")
            return None
        
        # 3. Met en cache
        if self.cache:
            await self.cache.set(cache_key, airport.model_dump())
        
        return airport
    
    async def search_airports_by_name(
        self,
        name: str,
        limit: int = 10
    ) -> List[Airport]:
        """
        Recherche des aéroports par nom.
        
        Args:
            name: Nom à rechercher (ex: "Paris", "Charles")
            limit: Nombre max de résultats (défaut: 10)
            
        Returns:
            Liste d'aéroports (peut être vide)
            
        Example:
            >>> airports = await service.search_airports_by_name("Paris")
            >>> for ap in airports:
            ...     print(f"{ap.iata_code}: {ap.name}")
        """
        logger.info(f"Recherche d'aéroports avec nom: '{name}'")
        
        # Note: On ne cache pas les recherches (résultats variables)
        airports = await self.client.search_airports(query=name, limit=limit)
        
        logger.info(f"Trouvé {len(airports)} aéroports pour '{name}'")
        return airports
    
    # ========================================================================
    # AÉROPORT LE PLUS PROCHE
    # ========================================================================
    
    async def find_nearest_airport(
        self,
        latitude: float,
        longitude: float,
        country_code: Optional[str] = None,
        limit: int = 100
    ) -> Optional[Airport]:
        """
        Trouve l'aéroport le plus proche de coordonnées GPS.
        
        Args:
            latitude: Latitude du point
            longitude: Longitude du point
            country_code: Optionnel, filtre par pays (ex: "FR")
            limit: Nombre d'aéroports à comparer (défaut: 100)
            
        Returns:
            Airport le plus proche ou None
            
        Example:
            >>> # Trouve l'aéroport le plus proche de Paris centre
            >>> airport = await service.find_nearest_airport(48.8566, 2.3522)
            >>> print(f"{airport.iata_code} à {distance:.1f} km")
        """
        # Valide les coordonnées
        if not self.geocoding.validate_coordinates(latitude, longitude):
            logger.error(f"Coordonnées invalides : ({latitude}, {longitude})")
            return None
        
        logger.info(
            f"Recherche de l'aéroport le plus proche de ({latitude}, {longitude})"
        )
        
        # Récupère les aéroports à comparer
        airports = await self.client.search_airports(
            country=country_code,
            limit=limit
        )
        
        if not airports:
            logger.warning("Aucun aéroport trouvé pour la comparaison")
            return None
        
        # Calcule la distance pour chaque aéroport
        airports_with_distance = []
        for airport in airports:
            distance = self.geocoding.calculate_distance(
                latitude,
                longitude,
                airport.coordinates.latitude,
                airport.coordinates.longitude
            )
            airports_with_distance.append((airport, distance))
        
        # Trie par distance croissante
        airports_with_distance.sort(key=lambda x: x[1])
        
        nearest_airport, nearest_distance = airports_with_distance[0]
        
        logger.info(
            f"Aéroport le plus proche : {nearest_airport.iata_code} "
            f"({nearest_airport.name}) à {nearest_distance:.1f} km"
        )
        
        return nearest_airport
    
    async def find_nearest_airport_by_address(
        self,
        address: str,
        country_code: Optional[str] = None
    ) -> Optional[Airport]:
        """
        Trouve l'aéroport le plus proche d'une adresse.
        
        Combine géocodage + recherche du plus proche.
        
        Args:
            address: Adresse (ex: "Lille, France", "10 rue de Rivoli Paris")
            country_code: Optionnel, filtre par pays (ex: "FR")
            
        Returns:
            Airport le plus proche ou None
            
        Example:
            >>> airport = await service.find_nearest_airport_by_address(
            ...     "Lille, France"
            ... )
            >>> print(f"Aéroport : {airport.iata_code}")
        """
        # 1. Géocode l'adresse
        logger.info(f"Recherche d'aéroport proche de l'adresse : {address}")
        coords = await self.geocoding.geocode_address(address)
        
        if not coords:
            logger.error(f"Impossible de géocoder l'adresse : {address}")
            return None
        
        # 2. Trouve l'aéroport le plus proche
        return await self.find_nearest_airport(
            coords[0],
            coords[1],
            country_code=country_code
        )
    
    # ========================================================================
    # VOLS (DÉPARTS ET ARRIVÉES)
    # ========================================================================
    
    async def get_departures(
        self,
        airport_iata: str,
        limit: int = 10
    ) -> List[Flight]:
        """
        Récupère les vols au départ d'un aéroport.
        
        Args:
            airport_iata: Code IATA de l'aéroport
            limit: Nombre max de vols (défaut: 10)
            
        Returns:
            Liste de vols
            
        Example:
            >>> flights = await service.get_departures("CDG", limit=5)
            >>> for flight in flights:
            ...     print(f"{flight.flight_iata}: → {flight.arrival_iata}")
        """
        logger.info(f"Récupération des départs de {airport_iata}")
        
        flights = await self.client.get_departures(
            airport_iata.upper(),
            limit=limit
        )
        
        logger.info(f"Trouvé {len(flights)} départs pour {airport_iata}")
        return flights
    
    async def get_arrivals(
        self,
        airport_iata: str,
        limit: int = 10
    ) -> List[Flight]:
        """
        Récupère les vols à l'arrivée d'un aéroport.
        
        Args:
            airport_iata: Code IATA de l'aéroport
            limit: Nombre max de vols (défaut: 10)
            
        Returns:
            Liste de vols
            
        Example:
            >>> flights = await service.get_arrivals("CDG", limit=5)
            >>> for flight in flights:
            ...     print(f"{flight.flight_iata}: {flight.departure_iata} →")
        """
        logger.info(f"Récupération des arrivées à {airport_iata}")
        
        flights = await self.client.get_arrivals(
            airport_iata.upper(),
            limit=limit
        )
        
        logger.info(f"Trouvé {len(flights)} arrivées pour {airport_iata}")
        return flights