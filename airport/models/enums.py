"""
Énumérations pour le service Airport.
"""
from enum import Enum


class FlightStatus(str, Enum):
    """Statuts possibles d'un vol selon Aviationstack."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    LANDED = "landed"
    CANCELLED = "cancelled"
    INCIDENT = "incident"
    DIVERTED = "diverted"
    
    @classmethod
    def _missing_(cls, value):
        """Gère les valeurs inconnues de l'API."""
        # Si l'API retourne un statut inconnu, on le garde tel quel
        return value