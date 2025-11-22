"""
Routes pour la ressource Flight (Partie 2 - Microservice Flight).

Endpoints :
- GET /flights/{flight_iata}                    : Statut en temps reel d'un vol
- GET /flights/{flight_iata}/history            : Historique sur une periode
- GET /flights/{flight_iata}/statistics         : Statistiques agregeees

Conventions REST :
- GET : Lecture seule, idempotent, cacheable
- Codes status : 200 (ok), 404 (not found), 400 (bad request), 500 (error)
- Validation automatique par Pydantic
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Path, status
from typing import Optional
import logging
from datetime import datetime, timedelta

from api.responses import (
    FlightResponse,
    FlightHistoryResponse,
    FlightStatisticsResponse,
    ErrorResponse
)
from services import FlightService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/flights",
    tags=["Flights"],
    responses={
        404: {"model": ErrorResponse, "description": "Flight not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


# ============================================================================
# DEPENDANCE - Injection du service
# ============================================================================

async def get_flight_service() -> FlightService:
    """
    Dependance FastAPI pour injecter le service Flight.

    Cette fonction sera configuree dans main.py avec la vraie instance.
    Pattern : Dependency Injection
    """
    # TODO: Sera remplace dans main.py
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service not configured"
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/{flight_iata}",
    response_model=FlightResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flight status in real-time",
    description="""
    Recupere le statut en temps reel d'un vol.

    **Fonctionnalites :**
    - Statut actuel (scheduled, active, landed, cancelled, etc.)
    - Horaires : prevu, estime, reel
    - Retards en minutes
    - Informations aeroports de depart et arrivee
    - Terminaux et portes d'embarquement

    **Optimisations :**
    - Utilise le cache MongoDB (TTL court pour temps reel)
    - Stocke automatiquement dans l'historique

    **Exemples :**
    - `AF447` -> Vol Air France 447
    - `BA117` -> Vol British Airways 117
    - `LH400` -> Vol Lufthansa 400

    **Note :**
    Si vous cherchez l'historique d'un vol, utilisez GET /flights/{flight_iata}/history
    """,
    response_description="Flight status information"
)
async def get_flight_status(
    flight_iata: str = Path(
        ...,
        min_length=2,
        max_length=10,
        description="Flight IATA code (ex: AF447, BA117)",
        example="AF447"
    ),
    service: FlightService = Depends(get_flight_service)
):
    """
    Recupere le statut en temps reel d'un vol.

    Args:
        flight_iata: Code IATA du vol (ex: AF447)

    Returns:
        FlightResponse: Informations completes du vol

    Raises:
        HTTPException 404: Vol non trouve
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /flights/{flight_iata}")

        flight = await service.get_flight_status(flight_iata)

        if not flight:
            logger.warning(f"Flight not found: {flight_iata}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flight not found with IATA code: {flight_iata}"
            )

        return FlightResponse.from_domain(flight)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving flight {flight_iata}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{flight_iata}/history",
    response_model=FlightHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flight history over a period",
    description="""
    Recupere l'historique d'un vol sur une periode donnee.

    **Fonctionnalites :**
    - Historique jour par jour
    - Periode max : 3 mois (limitation API Basic Plan)
    - Cache intelligent pour eviter les appels API redondants
    - Stockage local pour historique long terme

    **Parametres :**
    - `start_date` : Date de debut (YYYY-MM-DD)
    - `end_date` : Date de fin (YYYY-MM-DD)

    **Limites :**
    - Periode max : 90 jours
    - Donnees historiques : 3 mois en arriere (API Aviationstack Basic Plan)

    **Exemples :**
    - `/flights/AF447/history?start_date=2025-11-01&end_date=2025-11-14`
    - `/flights/BA117/history?start_date=2025-10-15&end_date=2025-11-15`

    **Cas d'usage :**
    - Analyser la ponctualite d'un vol regulier
    - Verifier les tendances de retard
    - Preparer un rapport pour un vol frequent
    """,
    response_description="Flight history"
)
async def get_flight_history(
    flight_iata: str = Path(
        ...,
        min_length=2,
        max_length=10,
        description="Flight IATA code",
        example="AF447"
    ),
    start_date: str = Query(
        ...,
        regex=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)",
        example="2025-11-01"
    ),
    end_date: str = Query(
        ...,
        regex=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)",
        example="2025-11-14"
    ),
    service: FlightService = Depends(get_flight_service)
):
    """
    Recupere l'historique d'un vol sur une periode.

    Args:
        flight_iata: Code IATA du vol
        start_date: Date de debut (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)

    Returns:
        FlightHistoryResponse: Liste de vols avec metadata

    Raises:
        HTTPException 400: Dates invalides
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(
            f"GET /flights/{flight_iata}/history?"
            f"start_date={start_date}&end_date={end_date}"
        )

        # Valide les dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        if start_dt > end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date"
            )

        # Recupere l'historique
        flights = await service.get_flight_history(
            flight_iata=flight_iata,
            start_date=start_date,
            end_date=end_date
        )

        # Convertit en reponses API
        flight_responses = [
            FlightResponse.from_domain(flight)
            for flight in flights
        ]

        return FlightHistoryResponse(
            flight_iata=flight_iata.upper(),
            flights=flight_responses,
            total=len(flight_responses),
            start_date=start_date,
            end_date=end_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving history for {flight_iata}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{flight_iata}/statistics",
    response_model=FlightStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flight statistics over a period",
    description="""
    Calcule des statistiques agregeees pour un vol sur une periode.

    **Statistiques calculees :**
    - Taux de ponctualite (on-time rate)
    - Taux de retard (delay rate)
    - Taux d'annulation (cancellation rate)
    - Retard moyen et maximum
    - Duree de vol moyenne

    **Parametres :**
    - `start_date` : Date de debut (YYYY-MM-DD)
    - `end_date` : Date de fin (YYYY-MM-DD)

    **Limites :**
    - Periode max : 90 jours
    - Donnees historiques : 3 mois en arriere (API Aviationstack Basic Plan)

    **Exemples :**
    - `/flights/AF447/statistics?start_date=2025-10-01&end_date=2025-11-14`
    - `/flights/BA117/statistics?start_date=2025-09-01&end_date=2025-11-30`

    **Cas d'usage :**
    - Comparer la fiabilite de plusieurs vols
    - Choisir le vol le plus ponctuel
    - Analyser les tendances saisonnieres
    - Generer des rapports de performance
    """,
    response_description="Flight statistics"
)
async def get_flight_statistics(
    flight_iata: str = Path(
        ...,
        min_length=2,
        max_length=10,
        description="Flight IATA code",
        example="AF447"
    ),
    start_date: str = Query(
        ...,
        regex=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)",
        example="2025-10-01"
    ),
    end_date: str = Query(
        ...,
        regex=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)",
        example="2025-11-14"
    ),
    service: FlightService = Depends(get_flight_service)
):
    """
    Calcule des statistiques agregeees pour un vol.

    Args:
        flight_iata: Code IATA du vol
        start_date: Date de debut (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)

    Returns:
        FlightStatisticsResponse: Statistiques agregeees

    Raises:
        HTTPException 400: Dates invalides
        HTTPException 404: Pas de donnees disponibles
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(
            f"GET /flights/{flight_iata}/statistics?"
            f"start_date={start_date}&end_date={end_date}"
        )

        # Valide les dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        if start_dt > end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date"
            )

        # Calcule les statistiques
        stats = await service.get_flight_statistics(
            flight_iata=flight_iata,
            start_date=start_date,
            end_date=end_date
        )

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data available for flight {flight_iata} in the specified period"
            )

        # Convertit en reponse API
        return FlightStatisticsResponse(
            flight_iata=stats.flight_iata,
            total_flights=stats.total_flights,
            on_time_count=stats.on_time_count,
            delayed_count=stats.delayed_count,
            cancelled_count=stats.cancelled_count,
            on_time_rate=stats.on_time_rate,
            delay_rate=stats.delay_rate,
            cancellation_rate=stats.cancellation_rate,
            average_delay_minutes=stats.average_delay_minutes,
            max_delay_minutes=stats.max_delay_minutes,
            average_duration_minutes=stats.average_duration_minutes,
            start_date=start_date,
            end_date=end_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error calculating statistics for {flight_iata}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
