"""
Modeles de reponse pour l'API REST du microservice Flight.

Ces modeles definissent le contrat de l'API exposee aux clients.
Ils sont construits a partir des modeles domain pour garantir la coherence.

Responsabilites :
- Definir la structure JSON retournee par chaque endpoint
- Fournir des exemples pour la documentation OpenAPI
- Convertir les modeles domain en reponses API via from_domain()
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# MODELES POUR LES VOLS
# ============================================================================

class FlightScheduleResponse(BaseModel):
    """
    Horaires d'un vol (depart ou arrivee).

    Versions detaillees pour le microservice Flight.
    """
    scheduled_time: Optional[str] = Field(None, description="Heure prevue (ISO 8601)")
    estimated_time: Optional[str] = Field(None, description="Heure estimee (ISO 8601)")
    actual_time: Optional[str] = Field(None, description="Heure reelle (ISO 8601)")
    delay_minutes: Optional[int] = Field(None, description="Retard en minutes")
    terminal: Optional[str] = Field(None, description="Terminal")
    gate: Optional[str] = Field(None, description="Porte d'embarquement")
    airport_iata: str = Field(..., description="Code IATA de l'aeroport")

    class Config:
        json_schema_extra = {
            "example": {
                "scheduled_time": "2025-11-14T10:30:00+00:00",
                "estimated_time": "2025-11-14T10:45:00+00:00",
                "actual_time": None,
                "delay_minutes": 15,
                "terminal": "2F",
                "gate": "K42",
                "airport_iata": "CDG"
            }
        }


class FlightResponse(BaseModel):
    """
    Reponse API pour un vol (version complete).

    Retourne par :
    - GET /flights/{flight_iata}
    - GET /flights/{flight_iata}/history (liste)

    Construit depuis models.domain.Flight
    """
    flight_iata: str = Field(..., description="Code IATA complet (ex: AF1234)")
    flight_number: str = Field(..., description="Numero de vol (ex: 1234)")
    flight_date: str = Field(..., description="Date du vol (YYYY-MM-DD)")
    flight_status: str = Field(..., description="Statut : scheduled, active, landed, cancelled, etc.")

    # Depart
    departure: FlightScheduleResponse

    # Arrivee
    arrival: FlightScheduleResponse

    # Compagnie
    airline_name: Optional[str] = Field(None, description="Nom de la compagnie")
    airline_iata: Optional[str] = Field(None, description="Code IATA compagnie")
    airline_icao: Optional[str] = Field(None, description="Code ICAO compagnie")

    class Config:
        json_schema_extra = {
            "example": {
                "flight_iata": "AF1234",
                "flight_number": "1234",
                "flight_date": "2025-11-14",
                "flight_status": "scheduled",
                "departure": {
                    "scheduled_time": "2025-11-14T10:30:00+00:00",
                    "estimated_time": "2025-11-14T10:30:00+00:00",
                    "actual_time": None,
                    "delay_minutes": 0,
                    "terminal": "2F",
                    "gate": "K42",
                    "airport_iata": "CDG"
                },
                "arrival": {
                    "scheduled_time": "2025-11-14T13:15:00+00:00",
                    "estimated_time": None,
                    "actual_time": None,
                    "delay_minutes": None,
                    "terminal": "4",
                    "gate": None,
                    "airport_iata": "JFK"
                },
                "airline_name": "Air France",
                "airline_iata": "AF",
                "airline_icao": "AFR"
            }
        }

    @classmethod
    def from_domain(cls, flight) -> "FlightResponse":
        """
        Construit une reponse API depuis un modele domain.Flight.

        Args:
            flight: Instance de models.domain.Flight

        Returns:
            FlightResponse
        """
        return cls(
            flight_iata=flight.flight_iata,
            flight_number=flight.flight_number,
            flight_date=flight.flight_date,
            flight_status=flight.flight_status,
            departure=FlightScheduleResponse(
                scheduled_time=flight.departure.scheduled_time if flight.departure else None,
                estimated_time=flight.departure.estimated_time if flight.departure else None,
                actual_time=flight.departure.actual_time if flight.departure else None,
                delay_minutes=flight.departure.delay_minutes if flight.departure else None,
                terminal=flight.departure.terminal if flight.departure else None,
                gate=flight.departure.gate if flight.departure else None,
                airport_iata=flight.departure.airport_iata if flight.departure else ""
            ),
            arrival=FlightScheduleResponse(
                scheduled_time=flight.arrival.scheduled_time if flight.arrival else None,
                estimated_time=flight.arrival.estimated_time if flight.arrival else None,
                actual_time=flight.arrival.actual_time if flight.arrival else None,
                delay_minutes=flight.arrival.delay_minutes if flight.arrival else None,
                terminal=flight.arrival.terminal if flight.arrival else None,
                gate=flight.arrival.gate if flight.arrival else None,
                airport_iata=flight.arrival.airport_iata if flight.arrival else ""
            ),
            airline_name=flight.airline_name,
            airline_iata=flight.airline_iata,
            airline_icao=flight.airline_icao
        )


class FlightHistoryResponse(BaseModel):
    """
    Liste paginee de vols (historique).

    Retourne par :
    - GET /flights/{flight_iata}/history
    """
    flight_iata: str = Field(..., description="Numero de vol")
    flights: List[FlightResponse] = Field(
        default_factory=list,
        description="Liste des vols"
    )
    total: int = Field(..., ge=0, description="Nombre total de vols")
    start_date: str = Field(..., description="Date de debut (YYYY-MM-DD)")
    end_date: str = Field(..., description="Date de fin (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "flight_iata": "AF1234",
                "flights": [
                    {
                        "flight_iata": "AF1234",
                        "flight_number": "1234",
                        "flight_date": "2025-11-14",
                        "flight_status": "landed",
                        "departure": {
                            "scheduled_time": "2025-11-14T10:30:00+00:00",
                            "estimated_time": "2025-11-14T10:30:00+00:00",
                            "actual_time": "2025-11-14T10:32:00+00:00",
                            "delay_minutes": 2,
                            "terminal": "2F",
                            "gate": "K42",
                            "airport_iata": "CDG"
                        },
                        "arrival": {
                            "scheduled_time": "2025-11-14T13:15:00+00:00",
                            "estimated_time": "2025-11-14T13:17:00+00:00",
                            "actual_time": "2025-11-14T13:20:00+00:00",
                            "delay_minutes": 5,
                            "terminal": "4",
                            "gate": "B22",
                            "airport_iata": "JFK"
                        },
                        "airline_name": "Air France",
                        "airline_iata": "AF",
                        "airline_icao": "AFR"
                    }
                ],
                "total": 7,
                "start_date": "2025-11-01",
                "end_date": "2025-11-14"
            }
        }


class FlightStatisticsResponse(BaseModel):
    """
    Statistiques agregeees pour un vol sur une periode.

    Retourne par :
    - GET /flights/{flight_iata}/statistics
    """
    flight_iata: str = Field(..., description="Numero de vol")
    total_flights: int = Field(..., ge=0, description="Nombre total de vols")
    on_time_count: int = Field(..., ge=0, description="Nombre de vols a l'heure")
    delayed_count: int = Field(..., ge=0, description="Nombre de vols en retard")
    cancelled_count: int = Field(..., ge=0, description="Nombre de vols annules")
    on_time_rate: float = Field(..., ge=0, le=100, description="Taux de ponctualite (%)")
    delay_rate: float = Field(..., ge=0, le=100, description="Taux de retard (%)")
    cancellation_rate: float = Field(..., ge=0, le=100, description="Taux d'annulation (%)")
    average_delay_minutes: Optional[float] = Field(None, description="Retard moyen (minutes)")
    max_delay_minutes: Optional[int] = Field(None, description="Retard maximum (minutes)")
    average_duration_minutes: Optional[float] = Field(None, description="Duree moyenne (minutes)")
    start_date: str = Field(..., description="Date de debut (YYYY-MM-DD)")
    end_date: str = Field(..., description="Date de fin (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "flight_iata": "AF1234",
                "total_flights": 30,
                "on_time_count": 22,
                "delayed_count": 6,
                "cancelled_count": 2,
                "on_time_rate": 73.33,
                "delay_rate": 20.0,
                "cancellation_rate": 6.67,
                "average_delay_minutes": 18.5,
                "max_delay_minutes": 45,
                "average_duration_minutes": 480.2,
                "start_date": "2025-10-01",
                "end_date": "2025-11-14"
            }
        }


# ============================================================================
# MODELES D'ERREUR
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Reponse standardisee pour les erreurs.

    Retournee par tous les endpoints en cas d'erreur.
    """
    error: str = Field(..., description="Message d'erreur principal")
    detail: Optional[str] = Field(None, description="Details supplementaires")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Flight not found",
                "detail": "No flight found with IATA code: AF9999"
            }
        }
