"""
Services metier du microservice Flight.

Architecture simplifiee :
- FlightService : Orchestration principale (appels Gateway + historique MongoDB)

Note: Le cache est gere par le Gateway, pas par ce service.

Usage:
    from services import FlightService
"""

from .flight_service import FlightService, FlightStatistics

__all__ = [
    "FlightService",
    "FlightStatistics",
]
