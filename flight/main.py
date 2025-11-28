"""
Point d'entree du microservice Flight.

Architecture :
- FastAPI avec async/await
- Gateway pour les appels Aviationstack (cache, rate limiting, etc.)
- MongoDB pour l'historique des vols (stockage local)
- Logging structure
- CORS pour le frontend React

Lancement :
    uvicorn main:app --reload --port 8002

Documentation auto :
    http://localhost:8002/docs        (Swagger UI)
    http://localhost:8002/redoc       (ReDoc)
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import AsyncMongoClient

from config.settings import settings
from clients.aviationstack_client import AviationstackClient
from services import FlightService
from api.routes import flights
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
# VARIABLES GLOBALES (services partages)
# ============================================================================

# Ces variables seront initialisees au startup
aviationstack_client: Optional[AviationstackClient] = None
flight_service: Optional[FlightService] = None
mongo_client: Optional[AsyncMongoClient] = None


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gere le cycle de vie de l'application.

    Startup :
    - Connecte MongoDB (pour l'historique)
    - Initialise le client Gateway
    - Initialise les services

    Shutdown :
    - Ferme les connexions proprement
    """
    global aviationstack_client, flight_service, mongo_client

    # ========================================================================
    # STARTUP
    # ========================================================================

    logger.info("=" * 70)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 70)

    flights_collection = None

    # 1. Connecte MongoDB (pour l'historique des vols uniquement)
    try:
        logger.info(f"📦 Connecting to MongoDB: {settings.mongodb_uri_safe}")
        mongo_client = AsyncMongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=settings.mongodb_timeout
        )

        # Verifie la connexion
        await mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connected successfully")

        # Collection pour l'historique des vols (pas de cache, le Gateway le gere)
        mongo_db = mongo_client[settings.mongodb_database]
        flights_collection = mongo_db["flights"]

        # Cree des index pour l'historique
        await flights_collection.create_index("flight_iata")
        await flights_collection.create_index("flight_date")
        await flights_collection.create_index([("flight_iata", 1), ("flight_date", 1)])
        logger.info("✅ Flights collection ready with indexes")

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        flights_collection = None

    # 2. Initialise le client vers le Gateway
    logger.info(f"🛫 Initializing Gateway client -> {settings.gateway_url}")
    aviationstack_client = AviationstackClient()
    logger.info("✅ Gateway client ready")

    # 3. Initialise les services
    logger.info("⚙️ Initializing services")

    flight_service = FlightService(
        aviationstack_client=aviationstack_client,
        flights_collection=flights_collection
    )

    logger.info("✅ All services initialized")

    # 4. Log de la configuration
    logger.info("📋 Configuration:")
    logger.info(f"   - Gateway URL: {settings.gateway_url}")
    logger.info(f"   - Debug mode: {settings.debug}")
    logger.info(f"   - CORS origins: {settings.cors_origins}")
    logger.info(f"   - MongoDB history: {'enabled' if flights_collection is not None else 'disabled'}")

    logger.info("=" * 70)
    logger.info("✅ Application started successfully")
    logger.info(f"📚 API Documentation: http://localhost:8002/docs")
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

    # Ferme MongoDB
    if mongo_client:
        await mongo_client.close()
        logger.info("✅ MongoDB connection closed")

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
    Microservice Flight pour la plateforme Hello Mira.

    ## Fonctionnalites

    ### Statut en temps reel
    - Consulter le statut actuel d'un vol
    - Horaires : prevu, estime, reel
    - Retards et annulations
    - Informations aeroports et terminaux

    ### Historique
    - Historique jour par jour d'un vol
    - Periode : jusqu'a 3 mois en arriere
    - Stockage local MongoDB

    ### Statistiques
    - Taux de ponctualite (on-time rate)
    - Taux de retard et d'annulation
    - Retard moyen et maximum
    - Duree de vol moyenne

    ## Architecture

    - **Gateway** : cache, rate limiting, circuit breaker (port 8004)
    - **MongoDB** : stockage historique des vols
    - **Prometheus** : metriques sur /metrics

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
# INJECTION DE DEPENDANCES
# ============================================================================

def get_flight_service_override() -> FlightService:
    """
    Override pour la dependance get_flight_service.

    Retourne l'instance globale du service initialisee au startup.
    """
    if flight_service is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    return flight_service


# Configure l'override dans les routes
from api.routes.flights import get_flight_service

app.dependency_overrides[get_flight_service] = get_flight_service_override


# ============================================================================
# ROUTES
# ============================================================================

# Endpoint racine
@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Point d'entree de l'API Flight"
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


# Health check
@app.get(
    "/api/v1/health",
    tags=["Health"],
    summary="Health Check",
    description="Verifie l'etat de l'application"
)
async def health():
    """
    Endpoint de health check.

    Returns:
        Etat de l'application et des dependances
    """
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "connected" if mongo_client else "disconnected",
        "gateway": settings.gateway_url
    }

    return health_status


# Monte les routes avec prefixe /api/v1
app.include_router(flights.router, prefix="/api/v1")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global pour les exceptions non gerees.

    Log l'erreur et retourne une reponse 500 propre.
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
# POINT D'ENTREE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
