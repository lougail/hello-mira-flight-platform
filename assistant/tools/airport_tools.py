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
async def search_airports_tool(name: str, country_code: str) -> dict:
    """
    Recherche des aéroports par nom de lieu (ville, région).

    Args:
        name: Nom de la ville ou région (ex: Paris, London, Tokyo)
        country_code: Code pays ISO REQUIS (ex: FR, US, JP, GB, DE)

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
    Récupère les vols au départ d'un aéroport avec pays de destination.

    Args:
        iata: Code IATA de l'aéroport (ex: CDG)
        limit: Nombre maximum de vols à retourner (défaut: 20, max: 100)

    Returns:
        Liste des vols au départ avec leurs statuts et pays de destination
    """
    async with AirportClient(settings.airport_api_url, settings.http_timeout, settings.demo_mode) as client:
        # 1. Récupère les vols au départ
        result = await client.get_departures(iata, limit=min(limit, 100))

        # 2. Extrait les codes IATA uniques des destinations
        flights = result.get("flights", result.get("data", []))
        unique_arrival_iatas = set()
        for flight in flights:
            # Structure FlightListResponse ou mock data
            arrival_iata = flight.get("arrival_iata") or flight.get("arrival", {}).get("iata")
            if arrival_iata:
                unique_arrival_iatas.add(arrival_iata)

        # 3. Récupère les infos pays pour chaque destination
        iata_to_country = {}
        for arrival_iata in unique_arrival_iatas:
            try:
                airport_data = await client.get_airport_by_iata(arrival_iata)
                if airport_data and "error" not in airport_data:
                    # Gère différentes structures de réponse
                    data = airport_data.get("data", airport_data)
                    country = data.get("country") or data.get("country_name")
                    country_code = data.get("country_code") or data.get("country_iso2")
                    if country:
                        iata_to_country[arrival_iata] = {
                            "country": country,
                            "country_code": country_code
                        }
                        logger.info(f"Enriched {arrival_iata} -> {country}")
            except Exception as e:
                logger.warning(f"Could not get country for {arrival_iata}: {e}")

        # 4. Enrichit chaque vol avec le pays de destination
        for flight in flights:
            arrival_iata = flight.get("arrival_iata") or flight.get("arrival", {}).get("iata")
            if arrival_iata and arrival_iata in iata_to_country:
                flight["arrival_country"] = iata_to_country[arrival_iata]["country"]
                flight["arrival_country_code"] = iata_to_country[arrival_iata]["country_code"]

        logger.info(f"Enriched {len(flights)} flights with country info from {len(iata_to_country)} airports")
        return result


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