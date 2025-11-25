"""
Point d'entrée du microservice Airport.

Architecture :
- FastAPI avec async/await
- MongoDB pour le cache
- API Aviationstack pour les données
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
from pymongo import AsyncMongoClient

from config.settings import settings
from clients.aviationstack_client import AviationstackClient
from services import CacheService, GeocodingService, AirportService
from api.routes import router
from prometheus_fastapi_instrumentator import Instrumentator

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

from typing import Optional

# Ces variables seront initialisées au startup
aviationstack_client: Optional[AviationstackClient] = None
cache_service: Optional[CacheService] = None
geocoding_service: Optional[GeocodingService] = None
airport_service: Optional[AirportService] = None
mongo_client: Optional[AsyncMongoClient] = None


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.
    
    Startup :
    - Connecte MongoDB
    - Initialise les services
    - Configure les dépendances
    
    Shutdown :
    - Ferme les connexions proprement
    """
    global aviationstack_client, cache_service, geocoding_service, airport_service, mongo_client
    
    # ========================================================================
    # STARTUP
    # ========================================================================
    
    logger.info("=" * 70)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 70)
    
    # 1. Connecte MongoDB
    try:
        logger.info(f"📦 Connecting to MongoDB: {settings.mongodb_uri_safe}")
        mongo_client = AsyncMongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=settings.mongodb_timeout
        )
        
        # Vérifie la connexion
        await mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connected successfully")
        
        # Collection pour le cache
        cache_collection = mongo_client[settings.mongodb_database]["airport_cache"]
        
        # Crée un index TTL pour l'expiration automatique
        await cache_collection.create_index(
            "expires_at",
            expireAfterSeconds=0
        )
        logger.info(f"✅ Cache collection ready with TTL={settings.cache_ttl}s")
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        cache_collection = None
    
    # 2. Initialise le client Aviationstack
    logger.info("🛫 Initializing Aviationstack client")
    aviationstack_client = AviationstackClient(enable_rate_limit=True)
    logger.info("✅ Aviationstack client ready")
    
    # 3. Initialise les services
    logger.info("⚙️ Initializing services")
    
    cache_service = CacheService(
        collection=cache_collection,
        ttl=settings.cache_ttl
    ) if cache_collection is not None else None
    
    geocoding_service = GeocodingService()
    
    airport_service = AirportService(
        aviationstack_client=aviationstack_client,
        cache_service=cache_service,
        geocoding_service=geocoding_service
    )
    
    logger.info("✅ All services initialized")
    
    # 4. Log de la configuration
    logger.info("📋 Configuration:")
    logger.info(f"   - Debug mode: {settings.debug}")
    logger.info(f"   - Cache TTL: {settings.cache_ttl}s")
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
    
    # Ferme le client Aviationstack
    if aviationstack_client:
        await aviationstack_client.close()
        logger.info("✅ Aviationstack client closed")
    
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

    ### Optimisations
    - Cache MongoDB avec TTL configurable
    - Rate limiting de l'API externe
    - Géocodage avec Nominatim (gratuit)

    ## Documentation

    - **Swagger UI** : [/docs](/docs)
    - **ReDoc** : [/redoc](/redoc)
    - **OpenAPI JSON** : [/openapi.json](/openapi.json)

    ## Test technique Hello Mira

    Ce microservice fait partie du test technique Hello Mira.
    - Partie 1 : Microservice Airport ✅
    - Partie 2 : Microservice Flight (à venir)
    - Partie 3 : Optimisation (à venir)
    - Partie 4 : Assistant IA (à venir)
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

# Configure Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)

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