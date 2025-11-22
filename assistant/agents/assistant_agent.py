"""
Agent LangGraph principal pour l'Assistant IA.

Implémente un StateGraph avec 3 nodes :
1. interpret_node : Détection d'intention via Mistral AI function calling
2. execute_node : Exécution parallèle des tools
3. respond_node : Génération de réponse en langage naturel
"""

import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from models.domain.state import AssistantState
from config import settings
from tools import (
    get_airport_by_iata_tool,
    search_airports_tool,
    get_nearest_airport_tool,
    get_departures_tool,
    get_arrivals_tool,
    get_flight_status_tool,
    get_flight_statistics_tool,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION DES TOOLS
# =============================================================================

ALL_TOOLS = [
    # Airport tools
    get_airport_by_iata_tool,
    search_airports_tool,
    get_nearest_airport_tool,
    get_departures_tool,
    get_arrivals_tool,
    # Flight tools
    get_flight_status_tool,
    get_flight_statistics_tool,
]


# =============================================================================
# NODES DU GRAPH
# =============================================================================

async def interpret_intent_node(state: AssistantState) -> Dict[str, Any]:
    """
    Node 1 : Interprétation de l'intention via Mistral AI.

    Utilise le function calling de Mistral AI pour détecter :
    - Quels tools appeler
    - Avec quels paramètres
    - Intention de l'utilisateur

    Args:
        state: État actuel du graph

    Returns:
        État mis à jour avec tools_to_call
    """
    logger.info(f"[INTERPRET] Processing prompt: {state['prompt']}")

    # Initialise Mistral AI avec function calling
    llm = ChatMistralAI(
        model=settings.mistral_model,
        temperature=settings.mistral_temperature,
        api_key=settings.mistral_api_key,
    )

    # Bind tools pour function calling (parallel_tool_calls activé par défaut)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # Crée le message utilisateur
    messages = [HumanMessage(content=state["prompt"])]

    # Appelle Mistral AI
    response = await llm_with_tools.ainvoke(messages)

    # Extrait les tool calls
    tools_to_call = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        tools_to_call = response.tool_calls
        logger.info(f"[INTERPRET] Detected {len(tools_to_call)} tools to call")
        for tool_call in tools_to_call:
            logger.info(f"  - {tool_call['name']} with args {tool_call['args']}")

    # Détecte l'intention (basé sur le premier tool appelé)
    intent = "unknown"
    entities = {}
    confidence = 0.8

    if tools_to_call:
        first_tool = tools_to_call[0]
        intent = first_tool["name"].replace("_tool", "")
        entities = first_tool["args"]
        confidence = 0.95

    return {
        "messages": messages + [response],
        "tools_to_call": tools_to_call,
        "intent": intent,
        "entities": entities,
        "confidence": confidence,
    }


async def execute_tools_node(state: AssistantState) -> Dict[str, Any]:
    """
    Node 2 : Exécution des tools en parallèle.

    Utilise ToolNode de LangGraph pour exécuter automatiquement
    les tools détectés par Mistral AI.

    Args:
        state: État avec tools_to_call

    Returns:
        État mis à jour avec tool_results
    """
    logger.info(f"[EXECUTE] Executing {len(state.get('tools_to_call', []))} tools")

    if not state.get("tools_to_call"):
        logger.warning("[EXECUTE] No tools to execute")
        return {"tool_results": {}}

    # Utilise ToolNode de LangGraph pour exécuter les tools
    tool_node = ToolNode(ALL_TOOLS)

    # Exécute les tools (LangGraph gère le parallélisme automatiquement)
    result = await tool_node.ainvoke(state)

    logger.info(f"[EXECUTE] Tools executed successfully")

    return {"tool_results": result}


async def generate_answer_node(state: AssistantState) -> Dict[str, Any]:
    """
    Node 3 : Génération de la réponse en langage naturel.

    Utilise Mistral AI pour transformer les résultats des tools
    en une réponse claire et concise en français.

    Args:
        state: État avec tool_results

    Returns:
        État mis à jour avec final_answer
    """
    logger.info("[RESPOND] Generating natural language response")

    # Initialise Mistral AI (sans tools cette fois)
    llm = ChatMistralAI(
        model=settings.mistral_model,
        temperature=0.3,  # Un peu plus créatif pour la réponse
        api_key=settings.mistral_api_key,
        max_tokens=settings.max_tokens,
    )

    # Construit le prompt pour la génération de réponse
    system_prompt = """Tu es un assistant virtuel spécialisé dans les vols et aéroports.

Ton rôle :
- Répondre en français de manière claire et concise
- Extraire les informations clés des données fournies
- Utiliser un ton professionnel mais naturel
- Inclure les heures, retards et détails importants

Format de réponse :
- 1-3 phrases maximum
- Mettre en avant les informations essentielles
- Utiliser les horaires en format 24h (ex: 21h47)
"""

    user_prompt = f"""Question de l'utilisateur : {state['prompt']}

Données récupérées : {state.get('tool_results', {})}

Réponds à la question de l'utilisateur en français de manière claire et concise."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Génère la réponse
    response = await llm.ainvoke(messages)

    final_answer = response.content

    logger.info(f"[RESPOND] Generated answer: {final_answer[:100]}...")

    return {"final_answer": final_answer}


# =============================================================================
# ROUTING
# =============================================================================

def should_execute_tools(state: AssistantState) -> str:
    """
    Décide si on doit exécuter les tools ou passer directement à la réponse.

    Args:
        state: État actuel

    Returns:
        "execute" si tools détectés, "respond" sinon
    """
    if state.get("tools_to_call"):
        return "execute"
    return "respond"


# =============================================================================
# CONSTRUCTION DU GRAPH
# =============================================================================

def create_assistant_graph() -> StateGraph:
    """
    Crée et compile le StateGraph de l'Assistant.

    Architecture :
        START → interpret → [execute → respond] → END
                          ↘ respond (si pas de tools) → END

    Returns:
        Graph compilé prêt à être invoqué
    """
    logger.info("Building Assistant StateGraph")

    # Crée le graph
    graph = StateGraph(AssistantState)

    # Ajoute les nodes
    graph.add_node("interpret", interpret_intent_node)
    graph.add_node("execute", execute_tools_node)
    graph.add_node("respond", generate_answer_node)

    # Définit le point d'entrée
    graph.set_entry_point("interpret")

    # Ajoute les edges conditionnels
    graph.add_conditional_edges(
        "interpret",
        should_execute_tools,
        {
            "execute": "execute",
            "respond": "respond"
        }
    )

    # Edges fixes
    graph.add_edge("execute", "respond")
    graph.add_edge("respond", END)

    # Compile le graph
    compiled_graph = graph.compile()

    logger.info("StateGraph compiled successfully")

    return compiled_graph