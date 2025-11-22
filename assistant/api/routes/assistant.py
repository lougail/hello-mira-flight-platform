"""
Routes FastAPI pour l'Assistant IA conversationnel.

Endpoints :
- POST /assistant/interpret : Détecte l'intention sans exécuter d'actions
- POST /assistant/answer : Orchestration complète (interpret → execute → respond)
"""

from fastapi import APIRouter, HTTPException, status
import logging

from models.api.requests import PromptRequest
from models.api.responses import InterpretResponse, AnswerResponse, ErrorResponse
from agents import create_assistant_graph

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


# =============================================================================
# GRAPH SINGLETON
# =============================================================================

# Crée le graph une seule fois au démarrage
_assistant_graph = None


def get_assistant_graph():
    """Récupère l'instance singleton du graph."""
    global _assistant_graph
    if _assistant_graph is None:
        _assistant_graph = create_assistant_graph()
    return _assistant_graph


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/interpret",
    response_model=InterpretResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret user intent",
    description="""
    Interprète l'intention de l'utilisateur sans exécuter d'actions.

    **Fonctionnalités :**
    - Détection d'intention via Mistral AI
    - Extraction d'entités (codes IATA, lieux, dates, etc.)
    - Niveau de confiance de l'interprétation

    **Cas d'usage :**
    - Validation de l'intention avant exécution
    - Debugging de l'interprétation
    - Interface de prévisualisation

    **Exemples d'intentions détectées :**
    - `get_flight_status` : Statut d'un vol
    - `search_airports` : Recherche d'aéroports
    - `get_departures` : Vols au départ
    - `get_nearest_airport` : Aéroport le plus proche
    """,
    response_description="Intent and entities extracted from prompt"
)
async def interpret(request: PromptRequest):
    """
    Interprète l'intention de l'utilisateur.

    Args:
        request: Prompt en langage naturel

    Returns:
        InterpretResponse: Intention, entités et confiance

    Raises:
        HTTPException 500: Erreur d'interprétation
    """
    try:
        logger.info(f"POST /assistant/interpret - prompt: {request.prompt}")

        # Récupère le graph
        graph = get_assistant_graph()

        # Prépare l'état initial
        initial_state = {
            "messages": [],
            "prompt": request.prompt,
            "tools_to_call": None,
            "tool_results": None,
            "final_answer": None,
            "intent": None,
            "entities": None,
            "confidence": None,
        }

        # Exécute UNIQUEMENT le node interpret
        result = await graph.ainvoke(initial_state)

        # Construit la réponse
        return InterpretResponse(
            intent=result.get("intent", "unknown"),
            entities=result.get("entities", {}),
            confidence=result.get("confidence", 0.5)
        )

    except Exception as e:
        logger.error(f"Error interpreting prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to interpret prompt"
        )


@router.post(
    "/answer",
    response_model=AnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get natural language answer",
    description="""
    Orchestration complète : interprétation → exécution → réponse.

    **Fonctionnalités :**
    - Détection automatique de l'intention
    - Appel(s) aux microservices appropriés
    - Génération d'une réponse en langage naturel

    **Flow complet :**
    1. **Interpret** : Mistral AI détecte l'intention et les paramètres
    2. **Execute** : Appels en parallèle aux microservices Airport/Flight
    3. **Respond** : Génération de la réponse en français

    **Exemples de prompts supportés :**
    - "Je suis sur le vol AF282, à quelle heure j'arrive ?"
    - "Quels vols partent de CDG cet après-midi ?"
    - "Trouve-moi l'aéroport le plus proche de Lille"
    - "Donne-moi les statistiques du vol BA117"

    **Format de réponse :**
    - `answer` : Réponse en langage naturel (1-3 phrases)
    - `data` : Données structurées brutes des microservices
    """,
    response_description="Natural language answer with structured data"
)
async def answer(request: PromptRequest):
    """
    Répond à la question de l'utilisateur en langage naturel.

    Args:
        request: Prompt en langage naturel

    Returns:
        AnswerResponse: Réponse textuelle + données structurées

    Raises:
        HTTPException 500: Erreur d'orchestration
    """
    try:
        logger.info(f"POST /assistant/answer - prompt: {request.prompt}")

        # Récupère le graph
        graph = get_assistant_graph()

        # Prépare l'état initial
        initial_state = {
            "messages": [],
            "prompt": request.prompt,
            "tools_to_call": None,
            "tool_results": None,
            "final_answer": None,
            "intent": None,
            "entities": None,
            "confidence": None,
        }

        # Exécute le graph complet (interpret → execute → respond)
        result = await graph.ainvoke(initial_state)

        # Construit la réponse
        return AnswerResponse(
            answer=result.get("final_answer", "Je n'ai pas pu répondre à votre question."),
            data=result.get("tool_results")
        )

    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer"
        )