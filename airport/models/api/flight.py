"""
Modèle Flight correspondant EXACTEMENT à l'API Aviationstack.
"""
from pydantic import BaseModel
from typing import Optional


class DepartureArrivalApi(BaseModel):
    """Info de départ ou arrivée depuis l'API."""
    airport: str
    timezone: str
    iata: Optional[str] = None
    icao: Optional[str] = None
    terminal: Optional[str] = None
    gate: Optional[str] = None
    delay: Optional[int] = None
    scheduled: Optional[str] = None  # String datetime
    estimated: Optional[str] = None
    actual: Optional[str] = None
    estimated_runway: Optional[str] = None
    actual_runway: Optional[str] = None
    baggage: Optional[str] = None  # Seulement pour arrival
    
    class Config:
        extra = "ignore"


class AirlineApi(BaseModel):
    """Info compagnie aérienne depuis l'API."""
    name: str
    iata: Optional[str] = None
    icao: Optional[str] = None


class CodesharedApi(BaseModel):
    """Info de partage de code."""
    airline_name: str
    airline_iata: str
    airline_icao: str
    flight_number: str
    flight_iata: str
    flight_icao: str


class FlightInfoApi(BaseModel):
    """Info d'identification du vol."""
    number: str
    iata: str
    icao: str
    codeshared: Optional[CodesharedApi] = None


class FlightApiResponse(BaseModel):
    """Structure EXACTE retournée par /flights."""
    flight_date: str
    flight_status: str
    departure: DepartureArrivalApi
    arrival: DepartureArrivalApi
    airline: AirlineApi
    flight: FlightInfoApi
    aircraft: Optional[dict] = None
    live: Optional[dict] = None
    
    class Config:
        extra = "ignore"