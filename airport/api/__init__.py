"""
Module API REST du microservice Airport.

Structure :
- responses.py : Modèles de réponse (contrat API)
- routes/ : Endpoints FastAPI (à créer)
"""

from .responses import (
    # Aéroports
    CoordinatesResponse,
    AirportResponse,
    AirportListResponse,
    
    # Vols
    FlightScheduleResponse,
    FlightResponse,
    FlightListResponse,
    
    # Erreurs
    ErrorResponse,
)

__all__ = [
    # Aéroports
    "CoordinatesResponse",
    "AirportResponse",
    "AirportListResponse",
    
    # Vols
    "FlightScheduleResponse",
    "FlightResponse",
    "FlightListResponse",
    
    # Erreurs
    "ErrorResponse",
]