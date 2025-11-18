"""
Routes pour la ressource Airport.

Endpoints :
- GET /airports/{iata_code}           : Récupérer un aéroport par code IATA
- GET /airports/search                : Rechercher par nom
- GET /airports/nearest               : Trouver le plus proche (coords ou adresse)

Conventions REST :
- GET : Lecture seule, idempotent, cacheable
- Codes status : 200 (ok), 404 (not found), 400 (bad request), 500 (error)
- Validation automatique par Pydantic
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
import logging

from api.responses import AirportResponse, AirportListResponse, ErrorResponse
from services import AirportService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/airports",
    tags=["Airports"],
    responses={
        404: {"model": ErrorResponse, "description": "Airport not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


# ============================================================================
# DÉPENDANCE - Injection du service
# ============================================================================

async def get_airport_service() -> AirportService:
    """
    Dépendance FastAPI pour injecter le service Airport.
    
    Cette fonction sera configurée dans main.py avec la vraie instance.
    Pattern : Dependency Injection
    """
    # TODO: Sera remplacé dans main.py
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service not configured"
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/{iata_code}",
    response_model=AirportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get airport by IATA code",
    description="""
    Récupère les informations complètes d'un aéroport à partir de son code IATA.
    
    **Optimisations :**
    - Utilise le cache MongoDB (TTL configurable)
    - Code IATA automatiquement converti en majuscules
    
    **Exemples :**
    - `CDG` → Charles de Gaulle International Airport
    - `JFK` → John F Kennedy International Airport
    - `LHR` → London Heathrow Airport
    """,
    response_description="Airport information"
)
async def get_airport(
    iata_code: str,
    service: AirportService = Depends(get_airport_service)
):
    """
    Récupère un aéroport par son code IATA.
    
    Args:
        iata_code: Code IATA 3 lettres (ex: CDG, JFK)
        
    Returns:
        AirportResponse: Informations complètes de l'aéroport
        
    Raises:
        HTTPException 404: Aéroport non trouvé
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/{iata_code}")
        
        airport = await service.get_airport_by_iata(iata_code)
        
        if not airport:
            logger.warning(f"Airport not found: {iata_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport not found with IATA code: {iata_code}"
            )
        
        return AirportResponse.from_domain(airport)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving airport {iata_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/search",
    response_model=AirportListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search airports by name",
    description="""
    Recherche des aéroports par nom, ville, ou pays.
    
    **Fonctionnalités :**
    - Recherche textuelle (min 2 caractères)
    - Pagination avec limit/offset
    - Tri par pertinence (API Aviationstack)
    
    **Exemples :**
    - `?name=Paris` → CDG, ORY, BVA...
    - `?name=Charles&limit=5` → Top 5 aéroports contenant "Charles"
    - `?name=London&limit=10&offset=10` → Résultats 11-20
    """,
    response_description="List of matching airports"
)
async def search_airports(
    name: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Search term (min 2 characters)",
        example="Paris"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Max number of results (1-100)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset for pagination"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Recherche des aéroports par nom.
    
    Args:
        name: Texte à rechercher
        limit: Nombre max de résultats
        offset: Décalage pour pagination
        
    Returns:
        AirportListResponse: Liste paginée d'aéroports
        
    Raises:
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/search?name={name}&limit={limit}&offset={offset}")
        
        # Récupère plus de résultats pour la pagination
        airports = await service.search_airports_by_name(
            name=name,
            limit=limit + offset
        )
        
        # Applique la pagination manuelle
        paginated = airports[offset:offset + limit]
        
        return AirportListResponse(
            airports=[AirportResponse.from_domain(ap) for ap in paginated],
            total=len(airports),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error searching airports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/nearest",
    response_model=AirportResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearest airport",
    description="""
    Trouve l'aéroport le plus proche soit par coordonnées GPS, soit par adresse.
    
    **Deux modes d'utilisation :**
    
    1. **Par coordonnées GPS** (latitude + longitude)
       - Exemple : `?lat=48.8566&lon=2.3522` (Paris)
       - Calcul de distance : Formule de Haversine
       
    2. **Par adresse** (géocodage automatique)
       - Exemple : `?address=Lille,France`
       - Géocodage : Nominatim (OpenStreetMap)
    
    **Filtres optionnels :**
    - `country_code` : Limite la recherche à un pays (ex: FR)
    
    **Performance :**
    - Compare jusqu'à 100 aéroports
    - Temps de réponse : ~500ms (géocodage) ou ~100ms (coords directes)
    """,
    response_description="Nearest airport"
)
async def get_nearest_airport(
    latitude: Optional[float] = Query(
        None,
        ge=-90,
        le=90,
        description="Latitude (-90 to 90)",
        example=48.8566
    ),
    longitude: Optional[float] = Query(
        None,
        ge=-180,
        le=180,
        description="Longitude (-180 to 180)",
        example=2.3522
    ),
    address: Optional[str] = Query(
        None,
        min_length=3,
        max_length=200,
        description="Address to geocode",
        example="Lille, France"
    ),
    country_code: Optional[str] = Query(
        None,
        min_length=2,
        max_length=2,
        regex="^[A-Z]{2}$",
        description="ISO country code filter (ex: FR)",
        example="FR"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Trouve l'aéroport le plus proche.
    
    Deux modes : coordonnées GPS ou adresse.
    
    Args:
        latitude: Latitude (-90 à 90)
        longitude: Longitude (-180 à 180)
        address: Adresse (géocodée automatiquement)
        country_code: Filtre optionnel par pays
        
    Returns:
        AirportResponse: Aéroport le plus proche
        
    Raises:
        HTTPException 400: Paramètres invalides
        HTTPException 404: Aucun aéroport trouvé
        HTTPException 500: Erreur serveur
    """
    try:
        # Validation des paramètres
        has_coords = latitude is not None and longitude is not None
        has_address = address is not None
        
        if not has_coords and not has_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either (latitude + longitude) or address must be provided"
            )
        
        if has_coords and has_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either coordinates OR address, not both"
            )
        
        # Mode 1: Coordonnées GPS
        if has_coords:
            # Assertion de type pour Pylance
            assert latitude is not None and longitude is not None, "Coordinates validated above"
            
            logger.info(f"GET /airports/nearest?lat={latitude}&lon={longitude}")
            airport = await service.find_nearest_airport(
                latitude=latitude,
                longitude=longitude,
                country_code=country_code
            )
        
        # Mode 2: Adresse (géocodage)
        else:
            # Assertion de type pour Pylance
            assert address is not None, "Address validated above"
            
            logger.info(f"GET /airports/nearest?address={address}")
            airport = await service.find_nearest_airport_by_address(
                address=address,
                country_code=country_code
            )
        
        if not airport:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No airport found"
            )
        
        return AirportResponse.from_domain(airport)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding nearest airport: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )