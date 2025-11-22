"""
Modèles Pydantic pour les réponses API de l'Assistant.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class InterpretResponse(BaseModel):
    """
    Réponse de l'endpoint /interpret.

    Retourne l'intention détectée sans exécuter d'actions.
    """

    intent: str = Field(
        ...,
        description="Type d'intention détectée (flight_status, airport_search, departures, etc.)"
    )

    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Entités extraites du prompt (codes IATA, dates, lieux, etc.)"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance de l'interprétation (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "flight_status",
                "entities": {
                    "flight_iata": "AF282"
                },
                "confidence": 0.95
            }
        }


class AnswerResponse(BaseModel):
    """
    Réponse de l'endpoint /answer.

    Retourne une réponse en langage naturel + données structurées.
    """

    answer: str = Field(
        ...,
        description="Réponse en langage naturel générée par l'IA"
    )

    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Données structurées retournées par les microservices"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Le vol AF282 est prévu à 21h47 (heure locale) avec un retard de 18 minutes.",
                "data": {
                    "flight_number": "AF282",
                    "scheduled_arrival": "2025-11-22T21:47:00Z",
                    "estimated_arrival": "2025-11-22T22:05:00Z",
                    "delay_minutes": 18
                }
            }
        }


class ErrorResponse(BaseModel):
    """Réponse d'erreur standard."""

    detail: str = Field(..., description="Message d'erreur")