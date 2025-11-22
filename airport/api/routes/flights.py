"""
Routes pour les vols liés aux aéroports.

Note : Ces endpoints font partie du microservice Airport (Partie 1).
Le microservice Flight (Partie 2) aura d'autres endpoints pour :
- Détails d'un vol spécifique
- Historique d'un vol
- Statistiques

Endpoints :
- GET /airports/{iata}/departures    : Vols au départ
- GET /airports/{iata}/arrivals      : Vols à l'arrivée

Conventions :
- Pagination avec limit/offset
- Tri par heure de départ/arrivée
- Filtres optionnels (status, airline)
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Path, status
import logging

from api.responses import FlightListResponse, ErrorResponse, FlightResponse
from services import AirportService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/airports",
    tags=["Airport Flights"],
    responses={
        404: {"model": ErrorResponse, "description": "Airport not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


# ============================================================================
# DÉPENDANCE
# ============================================================================

async def get_airport_service() -> AirportService:
    """Injection du service Airport."""
    # TODO: Configuré dans main.py
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service not configured"
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/{iata_code}/departures",
    response_model=FlightListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get departing flights",
    description="""
    Liste les vols au départ d'un aéroport avec leurs statuts en temps réel.
    
    **Informations retournées :**
    - Numéro de vol et compagnie aérienne
    - Horaires (prévu, estimé, réel)
    - Retards en minutes
    - Aéroport de destination
    - Statut (scheduled, active, landed, cancelled, etc.)
    
    **Limites API externe :**
    - Plan gratuit Aviationstack : données limitées
    - Pagination max : 100 vols
    
    **Pour plus de détails sur un vol :**
    Utilisez le microservice Flight (Partie 2) : GET /flights/{flight_iata}
    """,
    response_description="List of departing flights"
)
async def get_departures(
    iata_code: str = Path(
        ...,
        min_length=3,
        max_length=3,
        regex="^[A-Z]{3}$",
        description="IATA code of the airport",
        example="CDG"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Max number of flights (1-100)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset for pagination"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Liste les vols au départ d'un aéroport.
    
    Args:
        iata_code: Code IATA de l'aéroport
        limit: Nombre max de vols
        offset: Décalage pour pagination
        
    Returns:
        FlightListResponse: Liste paginée de vols
        
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/{iata_code}/departures?limit={limit}&offset={offset}")
        
        # Récupère les vols
        flights = await service.get_departures(
            airport_iata=iata_code,
            limit=limit + offset
        )
        
        # Applique la pagination
        paginated = flights[offset:offset + limit]
        
        # Convertit en réponses API
        flight_responses = [
            FlightResponse.from_domain(flight)
            for flight in paginated
        ]
        
        return FlightListResponse(
            flights=flight_responses,
            total=len(flights),
            limit=limit,
            offset=offset,
            airport_iata=iata_code.upper()
        )
        
    except Exception as e:
        logger.error(f"Error retrieving departures for {iata_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{iata_code}/arrivals",
    response_model=FlightListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get arriving flights",
    description="""
    Liste les vols à l'arrivée d'un aéroport avec leurs statuts en temps réel.
    
    **Informations retournées :**
    - Numéro de vol et compagnie aérienne
    - Horaires (prévu, estimé, réel)
    - Retards en minutes
    - Aéroport de départ
    - Statut (scheduled, active, landed, cancelled, etc.)
    
    **Limites API externe :**
    - Plan gratuit Aviationstack : données limitées
    - Pagination max : 100 vols
    
    **Pour plus de détails sur un vol :**
    Utilisez le microservice Flight (Partie 2) : GET /flights/{flight_iata}
    """,
    response_description="List of arriving flights"
)
async def get_arrivals(
    iata_code: str = Path(
        ...,
        min_length=3,
        max_length=3,
        regex="^[A-Z]{3}$",
        description="IATA code of the airport",
        example="CDG"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Max number of flights (1-100)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset for pagination"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Liste les vols à l'arrivée d'un aéroport.
    
    Args:
        iata_code: Code IATA de l'aéroport
        limit: Nombre max de vols
        offset: Décalage pour pagination
        
    Returns:
        FlightListResponse: Liste paginée de vols
        
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/{iata_code}/arrivals?limit={limit}&offset={offset}")
        
        # Récupère les vols
        flights = await service.get_arrivals(
            airport_iata=iata_code,
            limit=limit + offset
        )
        
        # Applique la pagination
        paginated = flights[offset:offset + limit]
        
        # Convertit en réponses API
        flight_responses = [
            FlightResponse.from_domain(flight)
            for flight in paginated
        ]
        
        return FlightListResponse(
            flights=flight_responses,
            total=len(flights),
            limit=limit,
            offset=offset,
            airport_iata=iata_code.upper()
        )
        
    except Exception as e:
        logger.error(f"Error retrieving arrivals for {iata_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )