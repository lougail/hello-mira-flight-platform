# ============================================================================
# DOCKERFILE - Assistant Microservice
# ============================================================================
#
# Microservice d'assistant IA conversationnel avec LangGraph + Mistral AI
#
# Architecture :
# - Python 3.13 slim (image légère)
# - FastAPI + LangGraph + Mistral AI
# - Port 8003
# - User non-root (UID 1000)
#
# ============================================================================

# Image de base Python 3.13 slim
FROM python:3.13-slim

# Métadonnées
LABEL maintainer="Louis <https://github.com/lougail>"
LABEL description="Assistant IA conversationnel - Hello Mira"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Copie des dépendances
COPY requirements.txt .

# Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création d'un user non-root pour la sécurité
RUN useradd -m -u 1000 assistant && \
    chown -R assistant:assistant /app

# Switch vers user non-root
USER assistant

# Exposition du port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:8003/api/v1/health').status_code == 200 else 1)"

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]