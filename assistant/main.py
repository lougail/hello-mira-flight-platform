"""
Point d'entrée du microservice Assistant.

Lance l'application FastAPI avec :
- Routes /assistant/interpret et /assistant/answer
- LangGraph StateGraph pour orchestration
- Mistral AI pour function calling et génération de réponses
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import assistant_router

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# =============================================================================
# LIFESPAN EVENTS
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le lifecycle de l'application.

    Startup : Initialise le graph LangGraph
    Shutdown : Cleanup des ressources
    """
    # Startup
    logger.info("🚀 Starting Assistant microservice")
    logger.info(f"Mistral Model: {settings.mistral_model}")
    logger.info(f"Airport API: {settings.airport_api_url}")
    logger.info(f"Flight API: {settings.flight_api_url}")

    yield

    # Shutdown
    logger.info("👋 Shutting down Assistant microservice")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Hello Mira - Assistant API",
    description="""
    Microservice d'assistant IA conversationnel pour la recherche de vols et aéroports.

    **Architecture :**
    - LangGraph StateGraph pour orchestration multi-agents
    - Mistral AI pour function calling et génération de réponses
    - Microservices Airport et Flight pour les données

    **Endpoints principaux :**
    - `POST /api/v1/assistant/interpret` : Détecte l'intention
    - `POST /api/v1/assistant/answer` : Répond en langage naturel

    **Exemples de prompts :**
    - "Je suis sur le vol AF282, à quelle heure j'arrive ?"
    - "Quels vols partent de CDG cet après-midi ?"
    - "Trouve-moi l'aéroport le plus proche de Lille"
    """,
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ROUTES
# =============================================================================

# Health check
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Vérifie que le service est opérationnel.

    Returns:
        Status du service
    """
    return {
        "status": "healthy",
        "service": "assistant",
        "version": "1.0.0",
        "mistral_model": settings.mistral_model
    }


# Assistant routes
app.include_router(assistant_router, prefix="/api/v1")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.debug
    )