"""
Routes pour la ressource Airport.

Endpoints :
- GET /airports/{iata_code}           : Récupérer un aéroport par code IATA
- GET /airports/search                : Rechercher par nom de lieu (géocodage OpenStreetMap)
- GET /airports/nearest-by-coords     : Trouver le plus proche par coordonnées GPS
- GET /airports/nearest-by-address    : Trouver le plus proche par adresse

Conventions REST :
- GET : Lecture seule, idempotent, cacheable
- Codes status : 200 (ok), 404 (not found), 400 (bad request), 500 (error)
- Validation automatique par Pydantic
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
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
# IMPORTANT: Les routes spécifiques (/search, /nearest) DOIVENT être déclarées
# AVANT les routes avec path parameters (/{iata_code}) pour éviter les conflits

@router.get(
    "/search",
    response_model=AirportListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search airports by location name",
    description="""
    Recherche des aéroports par nom de lieu (ville, région, etc.).

    **Fonctionnement :**
    1. Géocode le nom de lieu via OpenStreetMap
    2. Récupère les aéroports du pays spécifié
    3. Calcule la distance de chaque aéroport au lieu recherché
    4. Retourne les aéroports triés par distance

    **Paramètres requis :**
    - `name` : Nom du lieu (min 2 caractères)
    - `country_code` : Code pays ISO (ex: FR, US, GB)

    **Avantages :**
    - Tolérant aux fautes de frappe
    - Fonctionne avec villes, régions, quartiers
    - Résultats triés par pertinence géographique

    **Exemples :**
    - `?name=Paris&country_code=FR` → CDG, ORY, BVA (triés par distance au centre de Paris)
    - `?name=Lyon&country_code=FR&limit=3` → Top 3 aéroports près de Lyon
    - `?name=Provence&country_code=FR` → Aéroports de la région
    """,
    response_description="List of airports sorted by distance"
)
async def search_airports(
    name: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Location name (city, region, etc.)",
        example="Paris"
    ),
    country_code: str = Query(
        ...,
        min_length=2,
        max_length=2,
        regex="^[A-Z]{2}$",
        description="ISO country code (required, ex: FR)",
        example="FR"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Max number of results (1-50)"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset for pagination"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Recherche des aéroports par nom de lieu.

    Args:
        name: Nom du lieu à rechercher
        country_code: Code pays ISO requis (ex: FR, US, GB)
        limit: Nombre max de résultats
        offset: Décalage pour pagination

    Returns:
        AirportListResponse: Liste d'aéroports triés par distance

    Raises:
        HTTPException 400: Géocodage échoué
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/search?name={name}&country_code={country_code}&limit={limit}&offset={offset}")

        # Récupère plus de résultats pour la pagination
        airports = await service.search_airports_by_location(
            location_name=name,
            country_code=country_code,
            limit=limit + offset
        )

        if not airports:
            logger.warning(f"No airports found for location: {name}")
            return AirportListResponse(
                airports=[],
                total=0,
                limit=limit,
                offset=offset
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
        logger.error(f"Error searching airports by location: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/nearest-by-coords",
    response_model=AirportResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearest airport by GPS coordinates",
    description="""
    Trouve l'aéroport le plus proche à partir de coordonnées GPS.

    **Fonctionnement :**
    - Récupère les aéroports du pays spécifié
    - Calcule la distance avec la formule de Haversine
    - Retourne l'aéroport le plus proche

    **Paramètres requis :**
    - `latitude` et `longitude` : Coordonnées GPS
    - `country_code` : Code pays ISO (ex: FR, US, GB) pour filtrer les résultats

    **Performance :**
    - Compare jusqu'à 100 aéroports du pays
    - Temps de réponse : ~100ms

    **Exemples :**
    - `?latitude=48.8566&longitude=2.3522&country_code=FR` → ORY (Paris Orly)
    - `?latitude=50.6292&longitude=3.0573&country_code=FR` → LIL (Lille Lesquin)
    """,
    response_description="Nearest airport"
)
async def get_nearest_airport_by_coords(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Latitude (-90 to 90)",
        example=48.8566
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Longitude (-180 to 180)",
        example=2.3522
    ),
    country_code: str = Query(
        ...,
        min_length=2,
        max_length=2,
        regex="^[A-Z]{2}$",
        description="ISO country code (required, ex: FR)",
        example="FR"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Trouve l'aéroport le plus proche par coordonnées GPS.

    Args:
        latitude: Latitude (-90 à 90)
        longitude: Longitude (-180 à 180)
        country_code: Code pays ISO requis (ex: FR, US, GB)

    Returns:
        AirportResponse: Aéroport le plus proche

    Raises:
        HTTPException 404: Aucun aéroport trouvé
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/nearest-by-coords?lat={latitude}&lon={longitude}&country={country_code}")

        airport = await service.find_nearest_airport(
            latitude=latitude,
            longitude=longitude,
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
        logger.error(f"Error finding nearest airport by coords: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/nearest-by-address",
    response_model=AirportResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearest airport by address",
    description="""
    Trouve l'aéroport le plus proche à partir d'une adresse.

    **Fonctionnement :**
    1. Géocode l'adresse via Nominatim (OpenStreetMap)
    2. Récupère les aéroports du pays spécifié
    3. Calcule la distance avec la formule de Haversine
    4. Retourne l'aéroport le plus proche

    **Paramètres requis :**
    - `address` : Adresse textuelle (ville, rue, etc.)
    - `country_code` : Code pays ISO (ex: FR, US, GB) pour filtrer les résultats

    **Performance :**
    - Temps de réponse : ~500ms (incluant géocodage)

    **Exemples :**
    - `?address=Lille,France&country_code=FR` → LIL (Lille Lesquin)
    - `?address=10 rue de Rivoli Paris&country_code=FR` → ORY ou CDG (selon distance)
    """,
    response_description="Nearest airport"
)
async def get_nearest_airport_by_address(
    address: str = Query(
        ...,
        min_length=3,
        max_length=200,
        description="Address to geocode",
        example="Lille, France"
    ),
    country_code: str = Query(
        ...,
        min_length=2,
        max_length=2,
        regex="^[A-Z]{2}$",
        description="ISO country code (required, ex: FR)",
        example="FR"
    ),
    service: AirportService = Depends(get_airport_service)
):
    """
    Trouve l'aéroport le plus proche par adresse.

    Args:
        address: Adresse (géocodée automatiquement)
        country_code: Code pays ISO requis (ex: FR, US, GB)

    Returns:
        AirportResponse: Aéroport le plus proche

    Raises:
        HTTPException 400: Géocodage échoué
        HTTPException 404: Aucun aéroport trouvé
        HTTPException 500: Erreur serveur
    """
    try:
        logger.info(f"GET /airports/nearest-by-address?address={address}&country={country_code}")

        airport = await service.find_nearest_airport_by_address(
            address=address,
            country_code=country_code
        )

        if not airport:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No airport found or geocoding failed"
            )

        return AirportResponse.from_domain(airport)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding nearest airport by address: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


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