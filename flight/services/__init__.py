"""
Services metier du microservice Flight.

Architecture en 2 couches :
- CacheService : Gestion du cache MongoDB (reutilisable, copie depuis Airport)
- FlightService : Orchestration principale

Usage:
    from services import FlightService, CacheService
"""

from .cache_service import CacheService
from .flight_service import FlightService, FlightStatistics

__all__ = [
    "CacheService",
    "FlightService",
    "FlightStatistics",
]
