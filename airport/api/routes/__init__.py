"""
Routers FastAPI pour le microservice Airport.

Combine tous les routers en un seul pour simplifier l'import dans main.py.

Structure :
- airports : Recherche d'aéroports
- flights : Vols (départs/arrivées)
- health : Santé du service
"""

from fastapi import APIRouter
from .airports import router as airports_router
from .flights import router as flights_router
from .health import router as health_router

# Router principal qui combine tous les sous-routers
router = APIRouter()

# Inclut les routers
router.include_router(airports_router)
router.include_router(flights_router)
router.include_router(health_router)

__all__ = ["router"]