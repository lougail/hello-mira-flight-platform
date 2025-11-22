"""
LangGraph tools pour le microservice Airport.

Chaque tool est une fonction async décorée avec @tool qui peut être
appelée par Mistral AI via function calling.
"""

from langchain_core.tools import tool
from typing import Optional
import logging

from clients import AirportClient
from config import settings

logger = logging.getLogger(__name__)


@tool
async def get_airport_by_iata_tool(iata: str) -> dict:
    """
    Recherche un aéroport par son code IATA.

    Args:
        iata: Code IATA de l'aéroport (ex: CDG, JFK, LHR)

    Returns:
        Informations complètes sur l'aéroport
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        return await client.get_airport_by_iata(iata)


@tool
async def search_airports_tool(name: str, country_code: Optional[str] = None) -> dict:
    """
    Recherche des aéroports par nom de lieu (ville, région).

    Args:
        name: Nom de la ville ou région (ex: Paris, London, Tokyo)
        country_code: Code pays ISO optionnel (ex: FR, US, JP)

    Returns:
        Liste d'aéroports correspondant à la recherche
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        return await client.search_airports_by_name(name, country_code)


@tool
async def get_nearest_airport_tool(
    address: str,
    country_code: str
) -> dict:
    """
    Trouve l'aéroport le plus proche d'une adresse ou d'un lieu.

    Args:
        address: Adresse ou nom de lieu (ex: "Lille", "Tour Eiffel, Paris")
        country_code: Code pays ISO (ex: FR, US)

    Returns:
        Aéroport le plus proche avec distance
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        return await client.get_nearest_airport_by_address(address, country_code)


@tool
async def get_departures_tool(iata: str, limit: int = 20) -> dict:
    """
    Récupère les vols au départ d'un aéroport.

    Args:
        iata: Code IATA de l'aéroport (ex: CDG)
        limit: Nombre maximum de vols à retourner (défaut: 20, max: 100)

    Returns:
        Liste des vols au départ avec leurs statuts
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        return await client.get_departures(iata, limit=min(limit, 100))


@tool
async def get_arrivals_tool(iata: str, limit: int = 20) -> dict:
    """
    Récupère les vols à l'arrivée d'un aéroport.

    Args:
        iata: Code IATA de l'aéroport (ex: CDG)
        limit: Nombre maximum de vols à retourner (défaut: 20, max: 100)

    Returns:
        Liste des vols à l'arrivée avec leurs statuts
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        return await client.get_arrivals(iata, limit=min(limit, 100))