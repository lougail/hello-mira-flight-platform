"""
Modèle Airport correspondant à l'API Aviationstack.

Structure de réponse :
{
  "id": "5514263",
  "gmt": "-10",
  "airport_id": "1",
  "iata_code": "AAA",
  "city_iata_code": "AAA",
  "icao_code": "NTGA",
  "country_iso2": "PF",
  "geoname_id": "6947726",
  "latitude": "-17.05",
  "longitude": "-145.41667",
  "airport_name": "Anaa",
  "country_name": "French Polynesia",
  "phone_number": null,
  "timezone": "Pacific/Tahiti"
}
"""
from pydantic import BaseModel, Field
from typing import Optional


class AirportApiResponse(BaseModel):
    """Modèle exact de la réponse API pour un aéroport."""
    
    # Identifiants
    id: str
    airport_id: str
    geoname_id: str
    
    # Codes
    iata_code: str
    city_iata_code: str
    icao_code: str
    country_iso2: str
    
    # Localisation (ATTENTION : strings dans l'API !)
    latitude: str
    longitude: str
    gmt: str
    timezone: str
    
    # Informations
    airport_name: str
    country_name: str
    phone_number: Optional[str] = None
    
    class Config:
        # Permet de parser directement depuis l'API
        extra = "ignore"  # Ignore les champs non définis