"""
État du StateGraph LangGraph pour l'Assistant.

L'état est partagé entre tous les nodes du graph et persiste
les informations nécessaires à l'orchestration.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AssistantState(TypedDict):
    """
    État persisté tout au long du graph LangGraph.

    Attributes:
        messages: Historique des messages LangChain
        prompt: Prompt original de l'utilisateur
        tools_to_call: Liste des tools détectés par Mistral AI
        tool_results: Résultats des appels aux tools
        final_answer: Réponse finale en langage naturel
        intent: Intention détectée (flight_status, airport_search, etc.)
        entities: Entités extraites du prompt
        confidence: Niveau de confiance de l'interprétation
    """

    # Messages LangChain (pour historique conversationnel)
    messages: List[BaseMessage]

    # Prompt utilisateur
    prompt: str

    # Tools à appeler (détectés par Mistral AI)
    tools_to_call: Optional[List[Dict[str, Any]]]

    # Résultats des tools
    tool_results: Optional[Dict[str, Any]]

    # Réponse finale
    final_answer: Optional[str]

    # Métadonnées d'interprétation
    intent: Optional[str]
    entities: Optional[Dict[str, Any]]
    confidence: Optional[float]