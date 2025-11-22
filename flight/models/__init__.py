"""
Export des modeles.

Usage:
    # Pour les modeles domaine
    from models import Airport, Flight, Departure, Arrival
"""

# Exports principaux (domaine)
from .domain.airport import Airport, Coordinates
from .domain.flight import Flight, Departure, Arrival
from .enums import FlightStatus

__all__ = [
    # Domaine
    "Airport",
    "Flight",
    "Departure",
    "Arrival",
    "Coordinates",
    "FlightStatus",
]
