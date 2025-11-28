"""
Point d'entrée du microservice Airport.

Architecture :
- FastAPI avec async/await
- Gateway pour les appels Aviationstack (cache, rate limiting, etc.)
- Logging structuré
- CORS pour le frontend React

Lancement :
    uvicorn main:app --reload --port 8001

Documentation auto :
    http://localhost:8001/docs        (Swagger UI)
    http://localhost:8001/redoc       (ReDoc)
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from clients.aviationstack_client import AviationstackClient
from services import GeocodingService, AirportService
from api.routes import router
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# ============================================================================
# CONFIGURATION DU LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================================================
# VARIABLES GLOBALES (services partagés)
# ============================================================================

# Ces variables seront initialisées au startup
aviationstack_client: Optional[AviationstackClient] = None
geocoding_service: Optional[GeocodingService] = None
airport_service: Optional[AirportService] = None


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.

    Startup :
    - Initialise le client Gateway
    - Initialise les services

    Shutdown :
    - Ferme les connexions proprement
    """
    global aviationstack_client, geocoding_service, airport_service

    # ========================================================================
    # STARTUP
    # ========================================================================

    logger.info("=" * 70)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 70)

    # 1. Initialise le client vers le Gateway
    logger.info(f"🛫 Initializing Gateway client -> {settings.gateway_url}")
    aviationstack_client = AviationstackClient()
    logger.info("✅ Gateway client ready")

    # 2. Initialise les services
    logger.info("⚙️ Initializing services")

    geocoding_service = GeocodingService()

    airport_service = AirportService(
        aviationstack_client=aviationstack_client,
        geocoding_service=geocoding_service
    )

    logger.info("✅ All services initialized")

    # 3. Log de la configuration
    logger.info("📋 Configuration:")
    logger.info(f"   - Gateway URL: {settings.gateway_url}")
    logger.info(f"   - Debug mode: {settings.debug}")
    logger.info(f"   - CORS origins: {settings.cors_origins}")

    logger.info("=" * 70)
    logger.info("✅ Application started successfully")
    logger.info(f"📚 API Documentation: http://localhost:8001/docs")
    logger.info("=" * 70)

    yield  # L'application tourne ici

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    logger.info("=" * 70)
    logger.info("🛑 Shutting down application")
    logger.info("=" * 70)

    # Ferme le client Gateway
    if aviationstack_client:
        await aviationstack_client.close()
        logger.info("✅ Gateway client closed")

    logger.info("=" * 70)
    logger.info("✅ Application stopped cleanly")
    logger.info("=" * 70)


# ============================================================================
# APPLICATION FASTAPI
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Microservice Airport pour la plateforme Hello Mira.

    ## Fonctionnalités

    ### Recherche d'aéroports
    - Par code IATA (ex: CDG, JFK)
    - Par nom ou ville
    - Par proximité (coordonnées GPS ou adresse)

    ### Vols
    - Liste des départs d'un aéroport
    - Liste des arrivées d'un aéroport
    - Statuts en temps réel

    ### Architecture
    - Gateway centralise les appels Aviationstack
    - Cache, rate limiting, circuit breaker gérés par le Gateway
    - Géocodage avec Nominatim (gratuit)

    ## Documentation

    - **Swagger UI** : [/docs](/docs)
    - **ReDoc** : [/redoc](/redoc)
    - **OpenAPI JSON** : [/openapi.json](/openapi.json)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug
)


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Configure Prometheus Instrumentator avec buckets granulaires
instrumentator = Instrumentator(
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/docs", "/redoc", "/openapi.json"]
)

# Ajoute la métrique de latence avec buckets personnalisés
instrumentator.add(
    metrics.latency(
        buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
    )
)

instrumentator.instrument(app).expose(app, include_in_schema=False)

logger.info("✅ Prometheus metrics enabled on /metrics")


# ============================================================================
# MIDDLEWARE CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INJECTION DE DÉPENDANCES
# ============================================================================

def get_airport_service_override() -> AirportService:
    """
    Override pour la dépendance get_airport_service.

    Retourne l'instance globale du service initialisée au startup.
    """
    if airport_service is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    return airport_service


# Configure l'override dans les routes
from api.routes.airports import get_airport_service as get_airport_service_airports
from api.routes.flights import get_airport_service as get_airport_service_flights

app.dependency_overrides[get_airport_service_airports] = get_airport_service_override
app.dependency_overrides[get_airport_service_flights] = get_airport_service_override


# ============================================================================
# ROUTES
# ============================================================================

# Endpoint racine
@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Point d'entrée de l'API Airport"
)
async def root():
    """
    Endpoint racine de l'API.

    Returns:
        Informations sur l'API
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "gateway": settings.gateway_url,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Monte les routes avec préfixe /api/v1
app.include_router(router, prefix="/api/v1")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global pour les exceptions non gérées.

    Log l'erreur et retourne une réponse 500 propre.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
