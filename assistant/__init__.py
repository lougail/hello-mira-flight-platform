"""
Assistant Microservice - Hello Mira Flight Platform

Microservice d'assistant IA conversationnel utilisant LangGraph et Mistral AI
pour orchestrer les appels aux microservices Airport et Flight.

Architecture:
- LangGraph StateGraph pour la gestion d'état
- Mistral AI pour le function calling
- FastAPI pour l'API REST
"""

__version__ = "1.0.0"