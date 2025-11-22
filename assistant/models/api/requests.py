"""
Modèles Pydantic pour les requêtes API de l'Assistant.
"""

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """
    Requête pour les endpoints /interpret et /answer.

    Attributes:
        prompt: Question de l'utilisateur en langage naturel
    """

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Question en langage naturel",
        examples=[
            "Je suis sur le vol AV15, à quelle heure vais-je arriver ?",
            "Quels vols partent de CDG cet après-midi ?",
            "Trouve-moi l'aéroport le plus proche de Lille"
        ]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Je suis sur le vol AF282, à quelle heure j'arrive ?"
            }
        }