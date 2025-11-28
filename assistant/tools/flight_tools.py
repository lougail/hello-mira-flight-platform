"""
LangGraph tools pour le microservice Flight.

Chaque tool est une fonction async décorée avec @tool qui peut être
appelée par Mistral AI via function calling.
"""

from langchain_core.tools import tool
import logging

from clients import FlightClient
from config import settings

logger = logging.getLogger(__name__)


@tool
async def get_flight_status_tool(flight_iata: str) -> dict:
    """
    Récupère le statut en temps réel d'un vol.

    Args:
        flight_iata: Code IATA du vol (ex: AF447, BA117, LH400)

    Returns:
        Statut actuel du vol avec horaires prévus, estimés, et retards
    """
    async with FlightClient(settings.flight_api_url, settings.http_timeout) as client:
        return await client.get_flight_status(flight_iata)


@tool
async def get_flight_statistics_tool(
    flight_iata: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    Récupère les statistiques de ponctualité d'un vol sur une période.

    Args:
        flight_iata: Code IATA du vol (ex: AF447)
        start_date: Date de début au format YYYY-MM-DD
        end_date: Date de fin au format YYYY-MM-DD

    Returns:
        Statistiques agrégées (taux de ponctualité, retards moyens, etc.)
    """
    async with FlightClient(settings.flight_api_url, settings.http_timeout) as client:
        return await client.get_flight_statistics(flight_iata, start_date, end_date)