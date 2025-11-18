"""
Endpoints de santé du microservice Airport.

Conventions :
- /health : Santé basique (toujours répond)
- /ready : Readiness probe (vérifie dépendances)
- /metrics : Métriques Prometheus (optionnel, Partie 3)

Utilisés par :
- Kubernetes/Docker health checks
- Monitoring (Prometheus, Datadog, etc.)
- Load balancers
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service unavailable"}
    }
)


class HealthResponse(BaseModel):
    """Réponse pour l'endpoint /health."""
    status: str
    service: str
    version: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "service": "airport",
                "version": "1.0.0",
                "timestamp": "2025-11-14T15:30:00Z"
            }
        }


class ReadinessResponse(BaseModel):
    """Réponse pour l'endpoint /ready."""
    ready: bool
    checks: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "ready": True,
                "checks": {
                    "aviationstack_api": "ok",
                    "mongodb": "ok",
                    "geocoding_api": "ok"
                }
            }
        }


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="""
    Vérifie que le service est en vie.
    
    **Liveness probe** : Utilisé par Kubernetes pour savoir si le pod doit être redémarré.
    
    Retourne toujours 200 OK si le service répond.
    Ne vérifie PAS les dépendances externes (voir /ready pour ça).
    """
)
async def health_check():
    """
    Health check basique (liveness).
    
    Returns:
        HealthResponse: Status du service
    """
    from config.settings import settings
    
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="""
    Vérifie que le service est prêt à recevoir du trafic.
    
    **Readiness probe** : Utilisé par Kubernetes pour savoir si le pod peut recevoir du trafic.
    
    Vérifie :
    - API Aviationstack accessible
    - MongoDB accessible
    - API de géocodage accessible
    
    Retourne 503 si une dépendance est indisponible.
    """
)
async def readiness_check():
    """
    Readiness check (vérifie les dépendances).
    
    Returns:
        ReadinessResponse: État des dépendances
        
    Raises:
        HTTPException 503: Si une dépendance est KO
    """
    from fastapi import HTTPException
    
    checks = {
        "aviationstack_api": "ok",  # TODO: Vérifier vraiment l'API
        "mongodb": "ok",             # TODO: Vérifier vraiment MongoDB
        "geocoding_api": "ok"        # TODO: Vérifier vraiment Nominatim
    }
    
    # TODO: Implémenter les vrais checks
    # Exemple :
    # try:
    #     await mongodb_client.admin.command('ping')
    #     checks["mongodb"] = "ok"
    # except Exception as e:
    #     checks["mongodb"] = f"error: {e}"
    
    all_ok = all(check == "ok" for check in checks.values())
    
    if not all_ok:
        logger.warning(f"Readiness check failed: {checks}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "checks": checks}
        )
    
    return ReadinessResponse(
        ready=True,
        checks=checks
    )