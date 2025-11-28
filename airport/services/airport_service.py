"""
Service métier principal pour les aéroports.

Responsabilités :
- Orchestrer les appels au client Gateway/Aviationstack
- Trouver l'aéroport le plus proche (coordonnées ou adresse)
- Lister les vols (départs/arrivées)

Note: Le cache est géré par le Gateway, ce service ne fait que de la logique métier.
"""

import logging
import time
from typing import List, Optional

from clients.aviationstack_client import AviationstackClient
from models import Airport, Flight
from .geocoding_service import GeocodingService
from monitoring.metrics import (
    airport_lookups,
    airport_lookup_latency,
    airports_found,
    flight_queries,
    flight_query_latency,
    flights_returned,
    nearest_airport_distance,
)

logger = logging.getLogger(__name__)


class AirportService:
    """
    Service principal pour gérer les aéroports.

    Usage:
        service = AirportService(client, geocoding_service)
        airport = await service.get_airport_by_iata("CDG")
    """

    def __init__(
        self,
        aviationstack_client: AviationstackClient,
        geocoding_service: Optional[GeocodingService] = None
    ):
        """
        Initialise le service avec ses dépendances.

        Args:
            aviationstack_client: Client pour le Gateway Aviationstack
            geocoding_service: Service de géocodage (optionnel)
        """
        self.client = aviationstack_client
        self.geocoding = geocoding_service or GeocodingService()

    # ========================================================================
    # RECHERCHE D'AÉROPORTS
    # ========================================================================

    async def get_airport_by_iata(self, iata_code: str) -> Optional[Airport]:
        """
        Récupère un aéroport par son code IATA.

        Args:
            iata_code: Code IATA (ex: "CDG")

        Returns:
            Airport ou None si non trouvé
        """
        iata_code = iata_code.upper()
        start_time = time.time()
        logger.info(f"Récupération de l'aéroport {iata_code}")

        try:
            airport = await self.client.get_airport_by_iata(iata_code)
            latency = time.time() - start_time

            if not airport:
                logger.warning(f"Aéroport {iata_code} non trouvé")
                airport_lookups.labels(type="iata", status="not_found").inc()
                airport_lookup_latency.labels(type="iata").observe(latency)
                return None

            airport_lookups.labels(type="iata", status="success").inc()
            airport_lookup_latency.labels(type="iata").observe(latency)
            return airport

        except Exception as e:
            airport_lookups.labels(type="iata", status="error").inc()
            raise

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
        """
        start_time = time.time()
        logger.info(f"Recherche d'aéroports avec nom: '{name}'")

        try:
            airports = await self.client.search_airports(query=name, limit=limit)
            latency = time.time() - start_time

            status = "success" if airports else "not_found"
            airport_lookups.labels(type="name", status=status).inc()
            airport_lookup_latency.labels(type="name").observe(latency)
            airports_found.labels(type="name").observe(len(airports))

            logger.info(f"Trouvé {len(airports)} aéroports pour '{name}'")
            return airports

        except Exception as e:
            airport_lookups.labels(type="name", status="error").inc()
            raise

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
        """
        start_time = time.time()

        # Valide les coordonnées
        if not self.geocoding.validate_coordinates(latitude, longitude):
            logger.error(f"Coordonnées invalides : ({latitude}, {longitude})")
            airport_lookups.labels(type="nearest", status="error").inc()
            return None

        logger.info(
            f"Recherche de l'aéroport le plus proche de ({latitude}, {longitude})"
        )

        try:
            # Récupère les aéroports à comparer
            airports = await self.client.search_airports(
                country=country_code,
                limit=limit
            )

            if not airports:
                logger.warning("Aucun aéroport trouvé pour la comparaison")
                latency = time.time() - start_time
                airport_lookups.labels(type="nearest", status="not_found").inc()
                airport_lookup_latency.labels(type="nearest").observe(latency)
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

            nearest_airport, nearest_dist = airports_with_distance[0]

            # Metrics
            latency = time.time() - start_time
            airport_lookups.labels(type="nearest", status="success").inc()
            airport_lookup_latency.labels(type="nearest").observe(latency)
            nearest_airport_distance.set(nearest_dist)

            logger.info(
                f"Aéroport le plus proche : {nearest_airport.iata_code} "
                f"({nearest_airport.name}) à {nearest_dist:.1f} km"
            )

            return nearest_airport

        except Exception as e:
            airport_lookups.labels(type="nearest", status="error").inc()
            raise

    async def find_nearest_airport_by_address(
        self,
        address: str,
        country_code: Optional[str] = None
    ) -> Optional[Airport]:
        """
        Trouve l'aéroport le plus proche d'une adresse.

        Args:
            address: Adresse (ex: "Lille, France", "10 rue de Rivoli Paris")
            country_code: Optionnel, filtre par pays (ex: "FR")

        Returns:
            Airport le plus proche ou None
        """
        start_time = time.time()

        # 1. Géocode l'adresse
        logger.info(f"Recherche d'aéroport proche de l'adresse : {address}")
        coords = await self.geocoding.geocode_address(address)

        if not coords:
            logger.error(f"Impossible de géocoder l'adresse : {address}")
            airport_lookups.labels(type="nearest_by_address", status="error").inc()
            return None

        # 2. Trouve l'aéroport le plus proche
        result = await self.find_nearest_airport(
            coords[0],
            coords[1],
            country_code=country_code
        )

        # Metrics
        latency = time.time() - start_time
        status = "success" if result else "not_found"
        airport_lookups.labels(type="nearest_by_address", status=status).inc()
        airport_lookup_latency.labels(type="nearest_by_address").observe(latency)

        return result

    async def search_airports_by_location(
        self,
        location_name: str,
        country_code: str,
        limit: int = 10
    ) -> List[Airport]:
        """
        Recherche des aéroports par nom de lieu (ville, région, etc.).

        Args:
            location_name: Nom du lieu (ex: "Paris", "Lyon", "Provence")
            country_code: Code pays ISO (ex: "FR")
            limit: Nombre max de résultats (défaut: 10)

        Returns:
            Liste d'aéroports triés par distance (peut être vide)
        """
        start_time = time.time()

        # 1. Géocode le nom de lieu
        search_query = f"{location_name} airport, {country_code}"
        logger.info(f"Géocodage de : {search_query}")

        coords = await self.geocoding.geocode_address(search_query)

        if not coords:
            logger.warning(f"Impossible de géocoder : {search_query}")
            # Fallback: essayer sans "airport"
            coords = await self.geocoding.geocode_address(f"{location_name}, {country_code}")

            if not coords:
                logger.error(f"Géocodage échoué pour : {location_name}")
                airport_lookups.labels(type="location", status="error").inc()
                return []

        latitude, longitude = coords
        logger.info(f"Coordonnées trouvées : ({latitude}, {longitude})")

        try:
            # 2. Récupère les aéroports du pays
            airports = await self.client.search_airports(
                country=country_code,
                limit=100  # Récupère plus pour filtrer ensuite
            )

            if not airports:
                logger.warning(f"Aucun aéroport trouvé pour {country_code}")
                latency = time.time() - start_time
                airport_lookups.labels(type="location", status="not_found").inc()
                airport_lookup_latency.labels(type="location").observe(latency)
                return []

            # 3. Calcule la distance pour chaque aéroport
            airports_with_distance = []
            for airport in airports:
                distance = self.geocoding.calculate_distance(
                    latitude,
                    longitude,
                    airport.coordinates.latitude,
                    airport.coordinates.longitude
                )
                airports_with_distance.append((airport, distance))

            # 4. Trie par distance croissante
            airports_with_distance.sort(key=lambda x: x[1])

            # 5. Retourne les N premiers
            result = [airport for airport, _ in airports_with_distance[:limit]]

            # Metrics
            latency = time.time() - start_time
            airport_lookups.labels(type="location", status="success").inc()
            airport_lookup_latency.labels(type="location").observe(latency)
            airports_found.labels(type="location").observe(len(result))

            logger.info(
                f"Trouvé {len(result)} aéroports près de {location_name} "
                f"(premier: {result[0].iata_code if result else 'N/A'})"
            )

            return result

        except Exception as e:
            airport_lookups.labels(type="location", status="error").inc()
            raise

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
        """
        start_time = time.time()
        logger.info(f"Récupération des départs de {airport_iata}")

        try:
            flights = await self.client.get_departures(
                airport_iata.upper(),
                limit=limit
            )

            # Metrics
            latency = time.time() - start_time
            flight_queries.labels(type="departures", status="success").inc()
            flight_query_latency.labels(type="departures").observe(latency)
            flights_returned.labels(type="departures").observe(len(flights))

            logger.info(f"Trouvé {len(flights)} départs pour {airport_iata}")
            return flights

        except Exception as e:
            flight_queries.labels(type="departures", status="error").inc()
            raise

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
        """
        start_time = time.time()
        logger.info(f"Récupération des arrivées à {airport_iata}")

        try:
            flights = await self.client.get_arrivals(
                airport_iata.upper(),
                limit=limit
            )

            # Metrics
            latency = time.time() - start_time
            flight_queries.labels(type="arrivals", status="success").inc()
            flight_query_latency.labels(type="arrivals").observe(latency)
            flights_returned.labels(type="arrivals").observe(len(flights))

            logger.info(f"Trouvé {len(flights)} arrivées pour {airport_iata}")
            return flights

        except Exception as e:
            flight_queries.labels(type="arrivals", status="error").inc()
            raise
