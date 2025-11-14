"""
Modèle Airport pour notre domaine métier.
Simplifié et avec les bons types Python.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Coordinates(BaseModel):
    """Coordonnées GPS avec validation."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class Airport(BaseModel):
    """Notre modèle Airport simplifié pour l'application."""
    
    # Codes essentiels
    iata_code: str = Field(..., pattern="^[A-Z]{3}$")
    icao_code: str = Field(..., pattern="^[A-Z]{4}$")
    
    # Informations
    name: str
    city: str
    country: str
    country_code: str = Field(..., pattern="^[A-Z]{2}$")
    
    # Localisation
    coordinates: Coordinates
    timezone: str
    
    @field_validator('iata_code', 'icao_code', 'country_code', mode='before')
    @classmethod
    def uppercase_codes(cls, v: str) -> str:
        """Force les codes en majuscules AVANT validation du pattern."""
        if isinstance(v, str):
            return v.upper()
        return v
    
    @classmethod
    def from_api_response(cls, api_data: dict) -> "Airport":
        """Crée une instance depuis la réponse API."""
        return cls(
            iata_code=api_data["iata_code"],
            icao_code=api_data["icao_code"],
            name=api_data["airport_name"],
            city=api_data["city_iata_code"],  # On utilise ça comme ville
            country=api_data["country_name"],
            country_code=api_data["country_iso2"],
            coordinates=Coordinates(
                latitude=float(api_data["latitude"]),
                longitude=float(api_data["longitude"])
            ),
            timezone=api_data["timezone"]
        )