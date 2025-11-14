"""
Export des modèles.

Usage:
    # Pour les modèles API (structure exacte)
    from models.api import AirportApiResponse, FlightApiResponse
    
    # Pour les modèles domaine (simplifiés)
    from models import Airport, Flight
"""

# Exports principaux (domaine)
from .domain.airport import Airport, Coordinates
from .domain.flight import Flight, FlightSchedule
from .enums import FlightStatus

# Exports API
from .api.airport import AirportApiResponse
from .api.flight import FlightApiResponse

__all__ = [
    # Domaine
    "Airport",
    "Flight",
    "Coordinates",
    "FlightSchedule",
    "FlightStatus",
    # API
    "AirportApiResponse", 
    "FlightApiResponse"
]