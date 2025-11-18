"""
Modèles de réponse pour l'API REST du microservice Airport.

Ces modèles définissent le contrat de l'API exposée aux clients.
Ils sont construits à partir des modèles domain pour garantir la cohérence.

Responsabilités :
- Définir la structure JSON retournée par chaque endpoint
- Fournir des exemples pour la documentation OpenAPI
- Convertir les modèles domain en réponses API via from_domain()
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# MODÈLES POUR LES AÉROPORTS
# ============================================================================

class CoordinatesResponse(BaseModel):
    """
    Coordonnées GPS d'un aéroport.
    
    Note : L'API Aviationstack retourne des strings, mais on les convertit
    en floats dans le modèle domain avant de les exposer ici.
    """
    latitude: float = Field(..., description="Latitude en degrés décimaux")
    longitude: float = Field(..., description="Longitude en degrés décimaux")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 49.0097,
                "longitude": 2.5479
            }
        }


class AirportResponse(BaseModel):
    """
    Réponse API pour un aéroport.
    
    Retourné par :
    - GET /airports/{iata_code}
    - GET /airports/nearest
    
    Construit depuis models.domain.Airport
    """
    iata_code: str = Field(..., description="Code IATA 3 lettres (ex: CDG)")
    icao_code: str = Field(..., description="Code ICAO 4 lettres (ex: LFPG)")
    name: str = Field(..., description="Nom complet de l'aéroport")
    city: str = Field(..., description="Ville ou code ville")
    country: str = Field(..., description="Nom du pays")
    country_code: str = Field(..., description="Code ISO pays (ex: FR)")
    timezone: str = Field(..., description="Fuseau horaire (ex: Europe/Paris)")
    coordinates: CoordinatesResponse

    class Config:
        json_schema_extra = {
            "example": {
                "iata_code": "CDG",
                "icao_code": "LFPG",
                "name": "Charles de Gaulle International Airport",
                "city": "PAR",
                "country": "France",
                "country_code": "FR",
                "timezone": "Europe/Paris",
                "coordinates": {
                    "latitude": 49.0097,
                    "longitude": 2.5479
                }
            }
        }

    @classmethod
    def from_domain(cls, airport) -> "AirportResponse":
        """
        Construit une réponse API depuis un modèle domain.Airport.
        
        Args:
            airport: Instance de models.domain.Airport
            
        Returns:
            AirportResponse
        """
        return cls(
            iata_code=airport.iata_code,
            icao_code=airport.icao_code,
            name=airport.name,
            city=airport.city,
            country=airport.country,
            country_code=airport.country_code,
            timezone=airport.timezone,
            coordinates=CoordinatesResponse(
                latitude=airport.coordinates.latitude,
                longitude=airport.coordinates.longitude
            )
        )


class AirportListResponse(BaseModel):
    """
    Liste d'aéroports avec métadonnées de pagination.
    
    Retourné par :
    - GET /airports/search?name=...
    
    Suit la convention Aviationstack (limit/offset).
    """
    airports: List[AirportResponse] = Field(
        default_factory=list,
        description="Liste des aéroports"
    )
    total: int = Field(..., ge=0, description="Nombre total de résultats")
    limit: int = Field(..., ge=1, description="Nombre max par page")
    offset: int = Field(..., ge=0, description="Décalage (pagination)")

    class Config:
        json_schema_extra = {
            "example": {
                "airports": [
                    {
                        "iata_code": "CDG",
                        "icao_code": "LFPG",
                        "name": "Charles de Gaulle International Airport",
                        "city": "PAR",
                        "country": "France",
                        "country_code": "FR",
                        "timezone": "Europe/Paris",
                        "coordinates": {
                            "latitude": 49.0097,
                            "longitude": 2.5479
                        }
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }


# ============================================================================
# MODÈLES POUR LES VOLS
# ============================================================================

class FlightScheduleResponse(BaseModel):
    """
    Horaires d'un vol (départ ou arrivée).
    
    Simplifié pour le microservice Airport.
    Le microservice Flight aura plus de détails.
    """
    scheduled: Optional[datetime] = Field(None, description="Heure prévue (UTC)")
    estimated: Optional[datetime] = Field(None, description="Heure estimée (UTC)")
    actual: Optional[datetime] = Field(None, description="Heure réelle (UTC)")
    delay_minutes: Optional[int] = Field(None, description="Retard en minutes")

    class Config:
        json_schema_extra = {
            "example": {
                "scheduled": "2025-11-14T10:30:00Z",
                "estimated": "2025-11-14T10:45:00Z",
                "actual": None,
                "delay_minutes": 15
            }
        }


class FlightResponse(BaseModel):
    """
    Réponse API pour un vol (version simplifiée).
    
    Retourné par :
    - GET /airports/{iata}/departures
    - GET /airports/{iata}/arrivals
    
    Construit depuis models.domain.Flight
    
    Note : Le microservice Flight (Partie 2) aura un modèle plus complet
    avec historique et statistiques.
    """
    flight_number: str = Field(..., description="Numéro de vol (ex: 1234)")
    flight_iata: str = Field(..., description="Code IATA complet (ex: AF1234)")
    flight_date: str = Field(..., description="Date du vol (YYYY-MM-DD)")
    status: str = Field(..., description="Statut : scheduled, active, landed, etc.")
    
    # Départ
    departure_airport: str = Field(..., description="Nom aéroport de départ")
    departure_iata: str = Field(..., description="Code IATA départ")
    departure_schedule: FlightScheduleResponse
    
    # Arrivée
    arrival_airport: str = Field(..., description="Nom aéroport d'arrivée")
    arrival_iata: str = Field(..., description="Code IATA arrivée")
    arrival_schedule: FlightScheduleResponse
    
    # Compagnie
    airline_name: str = Field(..., description="Nom de la compagnie")
    airline_iata: Optional[str] = Field(None, description="Code IATA compagnie")

    class Config:
        json_schema_extra = {
            "example": {
                "flight_number": "1234",
                "flight_iata": "AF1234",
                "flight_date": "2025-11-14",
                "status": "scheduled",
                "departure_airport": "Charles de Gaulle International Airport",
                "departure_iata": "CDG",
                "departure_schedule": {
                    "scheduled": "2025-11-14T10:30:00Z",
                    "estimated": "2025-11-14T10:30:00Z",
                    "actual": None,
                    "delay_minutes": 0
                },
                "arrival_airport": "John F Kennedy International Airport",
                "arrival_iata": "JFK",
                "arrival_schedule": {
                    "scheduled": "2025-11-14T13:15:00Z",
                    "estimated": None,
                    "actual": None,
                    "delay_minutes": None
                },
                "airline_name": "Air France",
                "airline_iata": "AF"
            }
        }

    @classmethod
    def from_domain(cls, flight) -> "FlightResponse":
        """
        Construit une réponse API depuis un modèle domain.Flight.
        
        Args:
            flight: Instance de models.domain.Flight
            
        Returns:
            FlightResponse
        """
        return cls(
            flight_number=flight.flight_number,
            flight_iata=flight.flight_iata,
            flight_date=flight.flight_date,
            status=flight.status.value,  # Convertit l'enum en string
            departure_airport=flight.departure_airport,
            departure_iata=flight.departure_iata,
            departure_schedule=FlightScheduleResponse(
                scheduled=flight.departure_schedule.scheduled,
                estimated=flight.departure_schedule.estimated,
                actual=flight.departure_schedule.actual,
                delay_minutes=flight.departure_schedule.delay_minutes
            ),
            arrival_airport=flight.arrival_airport,
            arrival_iata=flight.arrival_iata,
            arrival_schedule=FlightScheduleResponse(
                scheduled=flight.arrival_schedule.scheduled,
                estimated=flight.arrival_schedule.estimated,
                actual=flight.arrival_schedule.actual,
                delay_minutes=flight.arrival_schedule.delay_minutes
            ),
            airline_name=flight.airline_name,
            airline_iata=flight.airline_iata
        )


class FlightListResponse(BaseModel):
    """
    Liste paginée de vols.
    
    Retourné par :
    - GET /airports/{iata}/departures
    - GET /airports/{iata}/arrivals
    """
    flights: List[FlightResponse] = Field(
        default_factory=list,
        description="Liste des vols"
    )
    total: int = Field(..., ge=0, description="Nombre total de résultats")
    limit: int = Field(..., ge=1, description="Nombre max par page")
    offset: int = Field(..., ge=0, description="Décalage (pagination)")
    airport_iata: str = Field(..., description="Code IATA de l'aéroport concerné")

    class Config:
        json_schema_extra = {
            "example": {
                "flights": [
                    {
                        "flight_number": "1234",
                        "flight_iata": "AF1234",
                        "flight_date": "2025-11-14",
                        "status": "scheduled",
                        "departure_airport": "Charles de Gaulle International Airport",
                        "departure_iata": "CDG",
                        "departure_schedule": {
                            "scheduled": "2025-11-14T10:30:00Z",
                            "estimated": "2025-11-14T10:30:00Z",
                            "actual": None,
                            "delay_minutes": 0
                        },
                        "arrival_airport": "John F Kennedy International Airport",
                        "arrival_iata": "JFK",
                        "arrival_schedule": {
                            "scheduled": "2025-11-14T13:15:00Z",
                            "estimated": None,
                            "actual": None,
                            "delay_minutes": None
                        },
                        "airline_name": "Air France",
                        "airline_iata": "AF"
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0,
                "airport_iata": "CDG"
            }
        }


# ============================================================================
# MODÈLES D'ERREUR
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Réponse standardisée pour les erreurs.
    
    Retournée par tous les endpoints en cas d'erreur.
    """
    error: str = Field(..., description="Message d'erreur principal")
    detail: Optional[str] = Field(None, description="Détails supplémentaires")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Airport not found",
                "detail": "No airport found with IATA code: XYZ"
            }
        }