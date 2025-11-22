"""
Module de données mockées pour le mode DEMO.

Ce module fournit des données fictives cohérentes pour démontrer
le fonctionnement de l'Assistant sans dépendre de l'API Aviationstack.
"""

from .flights import MOCK_FLIGHTS, MOCK_FLIGHT_STATISTICS
from .airports import MOCK_AIRPORTS, MOCK_DEPARTURES, MOCK_ARRIVALS

__all__ = [
    "MOCK_FLIGHTS",
    "MOCK_FLIGHT_STATISTICS",
    "MOCK_AIRPORTS",
    "MOCK_DEPARTURES",
    "MOCK_ARRIVALS",
]