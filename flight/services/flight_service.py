"""
Service metier principal pour les vols.

Responsabilites :
- Orchestrer les appels au client Aviationstack (via Gateway)
- Consulter le statut d'un vol en temps reel
- Recuperer l'historique d'un vol sur une periode
- Calculer des statistiques agregeees (taux de retard, duree moyenne, etc.)

Architecture :
Ce service ORCHESTRE et delegue :
- Appels API -> AviationstackClient (via Gateway)
- Stockage local -> MongoDB (pour historique)

Note: Le cache est gere par le Gateway, pas par ce service.
"""

import logging
import time
from typing import List, Optional
from datetime import datetime
from statistics import mean

from clients.aviationstack_client import AviationstackClient
from models import Flight
from monitoring.metrics import (
    flight_lookups,
    flight_lookup_latency,
    mongodb_operations,
    flights_stored,
    history_flights_count,
    statistics_calculated,
    statistics_flights_analyzed,
    last_on_time_rate,
    last_delay_rate,
    last_average_delay,
)

logger = logging.getLogger(__name__)


class FlightStatistics:
    """
    Statistiques agregeees pour un vol.

    Attributes:
        flight_iata: Numero de vol (ex: "AF447")
        total_flights: Nombre total de vols dans la periode
        on_time_count: Nombre de vols a l'heure
        delayed_count: Nombre de vols en retard
        cancelled_count: Nombre de vols annules
        on_time_rate: Taux de ponctualite (%)
        delay_rate: Taux de retard (%)
        cancellation_rate: Taux d'annulation (%)
        average_delay_minutes: Retard moyen en minutes
        max_delay_minutes: Retard maximum en minutes
        average_duration_minutes: Duree de vol moyenne en minutes
    """

    def __init__(
        self,
        flight_iata: str,
        total_flights: int,
        on_time_count: int,
        delayed_count: int,
        cancelled_count: int,
        average_delay_minutes: Optional[float] = None,
        max_delay_minutes: Optional[int] = None,
        average_duration_minutes: Optional[float] = None
    ):
        self.flight_iata = flight_iata
        self.total_flights = total_flights
        self.on_time_count = on_time_count
        self.delayed_count = delayed_count
        self.cancelled_count = cancelled_count
        self.on_time_rate = (on_time_count / total_flights * 100) if total_flights > 0 else 0
        self.delay_rate = (delayed_count / total_flights * 100) if total_flights > 0 else 0
        self.cancellation_rate = (cancelled_count / total_flights * 100) if total_flights > 0 else 0
        self.average_delay_minutes = average_delay_minutes
        self.max_delay_minutes = max_delay_minutes
        self.average_duration_minutes = average_duration_minutes

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour l'API."""
        return {
            "flight_iata": self.flight_iata,
            "total_flights": self.total_flights,
            "on_time_count": self.on_time_count,
            "delayed_count": self.delayed_count,
            "cancelled_count": self.cancelled_count,
            "on_time_rate": round(self.on_time_rate, 2),
            "delay_rate": round(self.delay_rate, 2),
            "cancellation_rate": round(self.cancellation_rate, 2),
            "average_delay_minutes": round(self.average_delay_minutes, 2) if self.average_delay_minutes else None,
            "max_delay_minutes": self.max_delay_minutes,
            "average_duration_minutes": round(self.average_duration_minutes, 2) if self.average_duration_minutes else None
        }


class FlightService:
    """
    Service principal pour gerer les vols.

    Usage:
        service = FlightService(client, flights_collection)
        flight = await service.get_flight_status("AF447")
        history = await service.get_flight_history("AF447", "2024-11-01", "2024-11-13")
        stats = await service.get_flight_statistics("AF447", "2024-10-01", "2024-11-13")
    """

    def __init__(
        self,
        aviationstack_client: AviationstackClient,
        flights_collection=None
    ):
        """
        Initialise le service avec ses dependances.

        Args:
            aviationstack_client: Client pour l'API Aviationstack (via Gateway)
            flights_collection: Collection MongoDB pour stocker l'historique (optionnel)
        """
        self.client = aviationstack_client
        self.flights_collection = flights_collection

    # ========================================================================
    # STATUT EN TEMPS REEL
    # ========================================================================

    async def get_flight_status(self, flight_iata: str) -> Optional[Flight]:
        """
        Recupere le statut en temps reel d'un vol.

        Appelle le Gateway (qui gere le cache) pour obtenir le vol en cours ou prevu.

        Args:
            flight_iata: Numero de vol (ex: "AF447", "BA117")

        Returns:
            Flight ou None si non trouve

        Example:
            >>> flight = await service.get_flight_status("AF447")
            >>> if flight:
            ...     print(f"{flight.flight_iata}: {flight.flight_status}")
            ...     print(f"Depart: {flight.departure.scheduled_time}")
        """
        flight_iata = flight_iata.upper()
        start_time = time.time()

        try:
            # Appelle le Gateway (qui gere le cache)
            logger.info(f"Recuperation du statut de {flight_iata} depuis le Gateway")
            flights = await self.client.get_flights(flight_iata=flight_iata, limit=100)

            if not flights:
                logger.warning(f"Vol {flight_iata} non trouve")
                # Metrics: recherche sans resultat
                latency = time.time() - start_time
                flight_lookups.labels(type="status", status="not_found").inc()
                flight_lookup_latency.labels(type="status").observe(latency)
                return None

            # Le premier vol est le plus récent (celui qu'on retourne)
            current_flight = flights[0]

            # Stocke TOUS les vols dans MongoDB pour construire l'historique
            # L'API retourne 2-3 vols (aujourd'hui + jours précédents)
            if self.flights_collection is not None:
                try:
                    queried_at = datetime.utcnow()
                    stored_count = 0

                    for flight in flights:
                        # Utilise upsert pour éviter les doublons (clé unique: flight_iata + flight_date)
                        await self.flights_collection.update_one(
                            {
                                "flight_iata": flight.flight_iata,
                                "flight_date": flight.flight_date
                            },
                            {
                                "$set": {
                                    **flight.model_dump(),
                                    "queried_at": queried_at
                                }
                            },
                            upsert=True
                        )
                        stored_count += 1

                    # Metrics: vols stockes
                    flights_stored.inc(stored_count)
                    mongodb_operations.labels(operation="store", status="success").inc()
                    logger.info(f"Stocke {stored_count} vols de {flight_iata} dans l'historique MongoDB")
                except Exception as e:
                    mongodb_operations.labels(operation="store", status="error").inc()
                    logger.error(f"Erreur stockage vols {flight_iata}: {e}")

            # Metrics: recherche reussie
            latency = time.time() - start_time
            flight_lookups.labels(type="status", status="success").inc()
            flight_lookup_latency.labels(type="status").observe(latency)

            return current_flight

        except Exception as e:
            # Metrics: erreur
            latency = time.time() - start_time
            flight_lookups.labels(type="status", status="error").inc()
            flight_lookup_latency.labels(type="status").observe(latency)
            raise

    # ========================================================================
    # HISTORIQUE
    # ========================================================================

    async def get_flight_history(
        self,
        flight_iata: str,
        start_date: str,
        end_date: str
    ) -> List[Flight]:
        """
        Recupere l'historique d'un vol depuis MongoDB (snapshots accumules).

        IMPORTANT: Cette méthode lit l'historique depuis MongoDB, pas depuis l'API.
        Les données sont accumulées au fil du temps via get_flight_status().

        Note sur l'API Aviationstack:
        - flight_iata seul retourne ~40-45% des vols disponibles (échantillon partiel)
        - flight_date + flight_iata permet de récupérer des vols spécifiques
        - L'API elle-même ne possède qu'un historique partiel (~45% des vols réels)

        Stratégie actuelle: Utiliser flight_iata pour accumuler l'historique.
        Suffisant pour des statistiques fiables sur 15-30 jours.

        Args:
            flight_iata: Numero de vol
            start_date: Date de debut (format: "YYYY-MM-DD")
            end_date: Date de fin (format: "YYYY-MM-DD")

        Returns:
            Liste de vols (peut etre vide si aucun vol trouve)

        Example:
            >>> history = await service.get_flight_history(
            ...     "AF447",
            ...     "2024-11-01",
            ...     "2024-11-07"
            ... )
            >>> print(f"Trouve {len(history)} vols")
        """
        flight_iata = flight_iata.upper()
        start_time = time.time()

        # Parse les dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Format de date invalide: {e}")
            flight_lookups.labels(type="history", status="error").inc()
            return []

        # Valide la periode
        if start > end:
            logger.error("Date de debut apres date de fin")
            flight_lookups.labels(type="history", status="error").inc()
            return []

        logger.info(
            f"Recuperation de l'historique de {flight_iata} depuis MongoDB "
            f"du {start_date} au {end_date}"
        )

        # Vérifie que la collection MongoDB est disponible
        if self.flights_collection is None:
            logger.warning("Collection MongoDB non disponible, historique vide")
            flight_lookups.labels(type="history", status="error").inc()
            return []

        try:
            # Requête MongoDB pour récupérer les vols dans la période
            # On filtre par flight_iata et flight_date
            query = {
                "flight_iata": flight_iata,
                "flight_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            # Tri par date
            cursor = self.flights_collection.find(query).sort("flight_date", 1)
            flights_data = await cursor.to_list(length=None)

            # Metrics: operation MongoDB reussie
            mongodb_operations.labels(operation="retrieve", status="success").inc()

            # Convertit en objets Flight
            all_flights = []
            seen_dates = set()  # Pour éviter les doublons (si consulté plusieurs fois le même jour)

            for data in flights_data:
                # Retire les champs MongoDB internes
                data.pop("_id", None)
                data.pop("queried_at", None)

                # Évite les doublons pour le même jour
                flight_date = data.get("flight_date")
                if flight_date in seen_dates:
                    continue
                seen_dates.add(flight_date)

                try:
                    flight = Flight(**data)
                    all_flights.append(flight)
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion du vol: {e}")
                    continue

            logger.info(f"Trouve {len(all_flights)} vols pour {flight_iata} dans MongoDB")

            # Metrics: recherche terminee
            latency = time.time() - start_time
            status = "success" if all_flights else "not_found"
            flight_lookups.labels(type="history", status=status).inc()
            flight_lookup_latency.labels(type="history").observe(latency)
            history_flights_count.observe(len(all_flights))

            # Si aucun historique trouvé, suggère de consulter le vol d'abord
            if not all_flights:
                logger.info(
                    f"Aucun historique pour {flight_iata}. "
                    f"Consultez d'abord GET /flights/{flight_iata} pour accumuler des données."
                )

            return all_flights

        except Exception as e:
            mongodb_operations.labels(operation="retrieve", status="error").inc()
            flight_lookups.labels(type="history", status="error").inc()
            logger.error(f"Erreur MongoDB: {e}")
            raise

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    async def get_flight_statistics(
        self,
        flight_iata: str,
        start_date: str,
        end_date: str
    ) -> Optional[FlightStatistics]:
        """
        Calcule des statistiques agregeees pour un vol sur une periode.

        Statistiques calculees :
        - Taux de ponctualite (on-time rate)
        - Taux de retard (delay rate)
        - Taux d'annulation (cancellation rate)
        - Retard moyen et maximum
        - Duree de vol moyenne

        Args:
            flight_iata: Numero de vol
            start_date: Date de debut (format: "YYYY-MM-DD")
            end_date: Date de fin (format: "YYYY-MM-DD")

        Returns:
            FlightStatistics ou None si pas assez de donnees

        Example:
            >>> stats = await service.get_flight_statistics(
            ...     "AF447",
            ...     "2024-10-01",
            ...     "2024-11-13"
            ... )
            >>> print(f"Taux de ponctualite: {stats.on_time_rate}%")
            >>> print(f"Retard moyen: {stats.average_delay_minutes} min")
        """
        # 1. Recupere l'historique
        flights = await self.get_flight_history(flight_iata, start_date, end_date)

        if not flights:
            logger.warning(f"Pas de donnees pour calculer les statistiques de {flight_iata}")
            flight_lookups.labels(type="statistics", status="not_found").inc()
            return None

        # 2. Calcule les metriques
        total = len(flights)
        on_time = 0
        delayed = 0
        cancelled = 0
        delays = []
        durations = []

        for flight in flights:
            # Comptage par statut
            if flight.flight_status == "cancelled":
                cancelled += 1
            elif flight.flight_status in ["active", "landed", "scheduled"]:
                # Calcule le retard
                if flight.departure and flight.departure.delay_minutes:
                    delay_min = flight.departure.delay_minutes
                    if delay_min > 15:  # Plus de 15 min = retard
                        delayed += 1
                        delays.append(delay_min)
                    else:
                        on_time += 1
                else:
                    on_time += 1  # Pas de retard enregistre = a l'heure

                # Calcule la duree de vol
                if (flight.departure and flight.arrival and
                    flight.departure.scheduled_time and flight.arrival.scheduled_time):
                    try:
                        dep_time = datetime.fromisoformat(
                            flight.departure.scheduled_time.replace("Z", "+00:00")
                        )
                        arr_time = datetime.fromisoformat(
                            flight.arrival.scheduled_time.replace("Z", "+00:00")
                        )
                        duration = (arr_time - dep_time).total_seconds() / 60
                        if duration > 0:
                            durations.append(duration)
                    except Exception as e:
                        logger.debug(f"Erreur calcul duree: {e}")

        # 3. Calcule les moyennes
        avg_delay = mean(delays) if delays else None
        max_delay = max(delays) if delays else None
        avg_duration = mean(durations) if durations else None

        # 4. Cree l'objet statistiques
        stats = FlightStatistics(
            flight_iata=flight_iata,
            total_flights=total,
            on_time_count=on_time,
            delayed_count=delayed,
            cancelled_count=cancelled,
            average_delay_minutes=avg_delay,
            max_delay_minutes=max_delay,
            average_duration_minutes=avg_duration
        )

        # Metrics: enregistre les statistiques calculees
        statistics_calculated.inc()
        statistics_flights_analyzed.observe(total)

        # Metrics: gauges pour les dernieres statistiques par vol
        last_on_time_rate.labels(flight_iata=flight_iata).set(stats.on_time_rate)
        last_delay_rate.labels(flight_iata=flight_iata).set(stats.delay_rate)
        if avg_delay is not None:
            last_average_delay.labels(flight_iata=flight_iata).set(avg_delay)

        # Metrics: recherche statistiques reussie
        flight_lookups.labels(type="statistics", status="success").inc()

        logger.info(
            f"Statistiques {flight_iata}: {total} vols, "
            f"{stats.on_time_rate:.1f}% a l'heure, "
            f"{stats.delay_rate:.1f}% en retard"
        )

        return stats
