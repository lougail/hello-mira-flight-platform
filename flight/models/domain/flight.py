"""
Modele Flight pour le microservice Flight.

Structure adaptee pour la Partie 2 du test technique Hello Mira.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..enums import FlightStatus


class Departure(BaseModel):
    """
    Informations de depart d'un vol.

    Combine aeroport + horaires + terminal/gate.
    """
    # Aeroport
    airport_iata: str = Field(..., description="Code IATA aeroport de depart")
    airport_name: Optional[str] = Field(None, description="Nom aeroport de depart")

    # Horaires
    scheduled_time: Optional[str] = Field(None, description="Heure prevue (ISO 8601)")
    estimated_time: Optional[str] = Field(None, description="Heure estimee (ISO 8601)")
    actual_time: Optional[str] = Field(None, description="Heure reelle (ISO 8601)")
    delay_minutes: Optional[int] = Field(None, description="Retard en minutes")

    # Terminal et porte
    terminal: Optional[str] = Field(None, description="Terminal")
    gate: Optional[str] = Field(None, description="Porte d'embarquement")

    @classmethod
    def from_api_data(cls, api_data: dict) -> "Departure":
        """Cree une instance depuis les donnees API."""
        return cls(
            airport_iata=api_data.get("iata", ""),
            airport_name=api_data.get("airport"),
            scheduled_time=api_data.get("scheduled"),
            estimated_time=api_data.get("estimated"),
            actual_time=api_data.get("actual"),
            delay_minutes=api_data.get("delay"),
            terminal=api_data.get("terminal"),
            gate=api_data.get("gate")
        )


class Arrival(BaseModel):
    """
    Informations d'arrivee d'un vol.

    Combine aeroport + horaires + terminal/gate.
    """
    # Aeroport
    airport_iata: str = Field(..., description="Code IATA aeroport d'arrivee")
    airport_name: Optional[str] = Field(None, description="Nom aeroport d'arrivee")

    # Horaires
    scheduled_time: Optional[str] = Field(None, description="Heure prevue (ISO 8601)")
    estimated_time: Optional[str] = Field(None, description="Heure estimee (ISO 8601)")
    actual_time: Optional[str] = Field(None, description="Heure reelle (ISO 8601)")
    delay_minutes: Optional[int] = Field(None, description="Retard en minutes")

    # Terminal et porte
    terminal: Optional[str] = Field(None, description="Terminal")
    gate: Optional[str] = Field(None, description="Porte d'embarquement")

    @classmethod
    def from_api_data(cls, api_data: dict) -> "Arrival":
        """Cree une instance depuis les donnees API."""
        return cls(
            airport_iata=api_data.get("iata", ""),
            airport_name=api_data.get("airport"),
            scheduled_time=api_data.get("scheduled"),
            estimated_time=api_data.get("estimated"),
            actual_time=api_data.get("actual"),
            delay_minutes=api_data.get("delay"),
            terminal=api_data.get("terminal"),
            gate=api_data.get("gate")
        )


class Flight(BaseModel):
    """
    Modele Flight complet pour le microservice Flight.

    Contient toutes les informations necessaires pour :
    - Statut en temps reel
    - Historique
    - Statistiques
    """

    # Identification
    flight_iata: str = Field(..., description="Code IATA complet (ex: AF447)")
    flight_number: str = Field(..., description="Numero de vol (ex: 447)")
    flight_date: str = Field(..., description="Date du vol (YYYY-MM-DD)")
    flight_status: str = Field(..., description="Statut : scheduled, active, landed, cancelled, etc.")

    # Depart et arrivee
    departure: Departure
    arrival: Arrival

    # Compagnie aerienne
    airline_name: Optional[str] = Field(None, description="Nom de la compagnie")
    airline_iata: Optional[str] = Field(None, description="Code IATA compagnie")
    airline_icao: Optional[str] = Field(None, description="Code ICAO compagnie")

    @classmethod
    def from_api_response(cls, api_data: dict) -> "Flight":
        """
        Cree une instance depuis la reponse API Aviationstack.

        Args:
            api_data: Dictionnaire de la reponse API

        Returns:
            Flight instance
        """
        return cls(
            flight_iata=api_data["flight"]["iata"],
            flight_number=api_data["flight"]["number"],
            flight_date=api_data["flight_date"],
            flight_status=api_data["flight_status"],
            departure=Departure.from_api_data(api_data["departure"]),
            arrival=Arrival.from_api_data(api_data["arrival"]),
            airline_name=api_data.get("airline", {}).get("name"),
            airline_iata=api_data.get("airline", {}).get("iata"),
            airline_icao=api_data.get("airline", {}).get("icao")
        )
