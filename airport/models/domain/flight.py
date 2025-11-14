"""
Modèle Flight pour notre domaine métier.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..enums import FlightStatus


class FlightSchedule(BaseModel):
    """Horaires d'un vol."""
    scheduled: Optional[datetime] = None
    estimated: Optional[datetime] = None
    actual: Optional[datetime] = None
    delay_minutes: Optional[int] = None
    
    @classmethod
    def from_api_data(cls, api_data: dict) -> "FlightSchedule":
        """Parse les dates string de l'API."""
        return cls(
            scheduled=cls._parse_datetime(api_data.get("scheduled")),
            estimated=cls._parse_datetime(api_data.get("estimated")),
            actual=cls._parse_datetime(api_data.get("actual")),
            delay_minutes=api_data.get("delay")
        )
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse une datetime string ou retourne None."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None


class Flight(BaseModel):
    """Notre modèle Flight simplifié."""
    
    # Identification
    flight_number: str
    flight_iata: str
    flight_date: str  # Format: "2025-11-14"
    
    # Status
    status: FlightStatus
    
    # Aéroports (simplifiés)
    departure_airport: str
    departure_iata: str
    arrival_airport: str
    arrival_iata: str
    
    # Horaires
    departure_schedule: FlightSchedule
    arrival_schedule: FlightSchedule
    
    # Compagnie
    airline_name: str
    airline_iata: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, api_data: dict) -> "Flight":
        """Crée une instance depuis la réponse API."""
        return cls(
            flight_number=api_data["flight"]["number"],
            flight_iata=api_data["flight"]["iata"],
            flight_date=api_data["flight_date"],
            status=FlightStatus(api_data["flight_status"]),
            departure_airport=api_data["departure"]["airport"],
            departure_iata=api_data["departure"]["iata"],
            arrival_airport=api_data["arrival"]["airport"],
            arrival_iata=api_data["arrival"]["iata"],
            departure_schedule=FlightSchedule.from_api_data(api_data["departure"]),
            arrival_schedule=FlightSchedule.from_api_data(api_data["arrival"]),
            airline_name=api_data["airline"]["name"],
            airline_iata=api_data["airline"].get("iata")
        )