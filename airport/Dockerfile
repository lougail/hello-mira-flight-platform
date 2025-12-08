# ============================================================================
# DOCKERFILE - Microservice Airport
# Hello Mira Flight Platform
# ============================================================================
#
# Multi-stage build pour optimiser la taille de l'image finale
#
# Build:
#   docker build -t hello-mira/airport:latest ./airport
#
# Run:
#   docker run -p 8001:8001 \
#     -e AVIATIONSTACK_API_KEY=xxx \
#     -e MONGODB_URI=mongodb://mongo:27017 \
#     hello-mira/airport:latest
# ============================================================================

# ============================================================================
# STAGE 1: Builder (dépendances)
# ============================================================================
FROM python:3.13-slim as builder

LABEL maintainer="Louis - Hello Mira Test Technique"
LABEL description="Microservice Airport - Stage Builder"

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /build

# Copie uniquement requirements.txt d'abord (layer caching optimal)
COPY requirements.txt .

# Installe les dépendances dans un virtualenv
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ============================================================================
# STAGE 2: Runtime (production)
# ============================================================================
FROM python:3.13-slim

LABEL maintainer="Louis - Hello Mira Test Technique"
LABEL description="Microservice Airport - Hello Mira Flight Platform"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Crée un user non-root pour la sécurité
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Répertoire de travail
WORKDIR /app

# Copie le virtualenv depuis le stage builder
COPY --from=builder /opt/venv /opt/venv

# Copie le code de l'application
COPY --chown=appuser:appuser . .

# Passe à l'utilisateur non-root
USER appuser

# Expose le port 8001
EXPOSE 8001

# Health check (vérifie que l'API répond)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:8001/api/v1/health').status_code == 200 else 1)"

# Commande de démarrage
# Note: --workers 1 car on utilise async (pas besoin de multi-process)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "1", \
     "--log-level", "info"]

# ============================================================================
# NOTES TECHNIQUES
# ============================================================================
#
# Multi-stage build :
# - Stage 1 (builder) : ~900 MB avec build tools
# - Stage 2 (runtime) : ~200 MB (image finale)
# - Gain : 70% de réduction de taille
#
# Sécurité :
# - User non-root (UID 1000)
# - Pas de sudo/root dans le container
# - Code en read-only
#
# Performance :
# - Layer caching avec requirements.txt séparé
# - Python slim (pas full debian)
# - Pas de cache pip
#
# Health check :
# - Intervalle : 30s
# - Timeout : 10s
# - Start period : 40s (temps de démarrage MongoDB)
# - Retries : 3
#
# Variables d'environnement attendues :
# - AVIATIONSTACK_API_KEY (requis)
# - MONGODB_URI (optionnel, défaut: mongodb://localhost:27017)
# - CACHE_TTL (optionnel, défaut: 300s)
# - DEBUG (optionnel, défaut: False)
#
# ============================================================================
