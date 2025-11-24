# ✈️ Hello Mira - Flight Platform

> **Plateforme intelligente pour les voyageurs** : Microservices pour la gestion des vols et aéroports avec Assistant IA conversationnel

Architecture moderne combinant FastAPI, MongoDB, LangGraph et Mistral AI pour fournir des informations de vol en temps réel avec une interface conversationnelle en langage naturel.

---

## 🎯 Vue d'Ensemble

### Fonctionnalités

**Microservice Airport (Port 8001) :**

- ✅ Recherche d'aéroport par code IATA
- ✅ Recherche d'aéroport par nom de lieu (avec géocodage)
- ✅ Recherche d'aéroport par coordonnées GPS
- ✅ Recherche d'aéroport par adresse
- ✅ Liste des vols au départ d'un aéroport
- ✅ Liste des vols à l'arrivée d'un aéroport

**Microservice Flight (Port 8002) :**

- ✅ Statut en temps réel d'un vol
- ✅ Historique d'un vol sur une période
- ✅ Statistiques agrégées (ponctualité, retards, annulations)

**Microservice Assistant (Port 8003) :**

- ✅ Interprétation d'intention en langage naturel
- ✅ Réponse complète avec orchestration LangGraph
- ✅ 7 outils disponibles (2 flight + 5 airport)

**Optimisations :**

- ✅ Cache MongoDB avec TTL de 300 secondes (5 minutes)
- ✅ Historique persistant avec accumulation progressive
- ✅ Index MongoDB optimisés (TTL + composite unique)

---

## 🔧 Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | FastAPI | 0.121.2 |
| **Serveur ASGI** | Uvicorn | 0.38.0 (Airport/Flight) / 0.34.0 (Assistant) |
| **Validation** | Pydantic | 2.12.4 |
| **Configuration** | Pydantic Settings | 2.12.0 |
| **Base de données** | MongoDB | 7.0 |
| **Driver MongoDB** | PyMongo | 4.15.4 |
| **Client HTTP** | httpx | 0.28.1 (Airport/Flight) / 0.27.0 (Assistant) |
| **Orchestration IA** | LangGraph | 0.2.45 |
| **LangChain Core** | langchain-core | 0.3.21 |
| **Integration Mistral** | langchain-mistralai | 0.2.2 |
| **Modèle LLM** | Mistral AI | mistral-large-latest |
| **API Externe Vols** | Aviationstack | Basic Plan |
| **Géocodage** | Nominatim (OSM) | - |
| **Container** | Docker Compose | v3.8 |

---

## 📋 Table des Matières

- [Vue d'Ensemble](#-vue-densemble)
- [Stack Technique](#-stack-technique)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Endpoints API](#-endpoints-api)
- [Mode DEMO](#-mode-demo)
- [Exemples d'Utilisation](#-exemples-dutilisation)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture

### Structure du Projet

```text
hello-mira-flight-platform/
├── airport/                          # Microservice Airport (port 8001)
│   ├── __init__.py
│   ├── main.py                       # Point d'entrée FastAPI
│   ├── Dockerfile                    # Image Docker multi-stage
│   ├── requirements.txt              # Dépendances Python
│   ├── api/
│   │   ├── __init__.py
│   │   ├── responses.py              # Schémas Pydantic réponses API
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── airports.py           # 4 endpoints recherche aéroports
│   │       ├── flights.py            # 2 endpoints vols départ/arrivée
│   │       └── health.py             # Health check + readiness
│   ├── clients/
│   │   ├── __init__.py
│   │   └── aviationstack_client.py   # Client HTTP Aviationstack
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Configuration Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py                  # FlightStatus enum
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── airport.py            # Schémas API aéroports
│   │   │   └── flight.py             # Schémas API vols
│   │   └── domain/
│   │       ├── __init__.py
│   │       ├── airport.py            # Modèle domaine Airport
│   │       └── flight.py             # Modèle domaine Flight
│   ├── services/
│   │   ├── __init__.py
│   │   ├── airport_service.py        # Logique métier aéroports
│   │   ├── cache_service.py          # Service cache MongoDB
│   │   └── geocoding_service.py      # Géocodage Nominatim
│   └── tests/
│       ├── __init__.py
│       ├── test_api_structure.py
│       ├── test_client.py
│       ├── test_models.py
│       ├── test_services.py
│       └── test_settings.py
│
├── flight/                           # Microservice Flight (port 8002)
│   ├── __init__.py
│   ├── main.py                       # Point d'entrée FastAPI
│   ├── Dockerfile                    # Image Docker multi-stage
│   ├── requirements.txt              # Dépendances Python
│   ├── api/
│   │   ├── __init__.py
│   │   ├── responses.py              # Schémas Pydantic réponses API
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── flights.py            # 3 endpoints (statut, historique, stats)
│   ├── clients/
│   │   ├── __init__.py
│   │   └── aviationstack_client.py   # Client HTTP Aviationstack
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Configuration Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py                  # FlightStatus enum
│   │   └── domain/
│   │       ├── __init__.py
│   │       ├── airport.py            # Modèle domaine Airport
│   │       └── flight.py             # Modèle domaine Flight
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py          # Service cache MongoDB
│   │   └── flight_service.py         # Logique métier vols + stats
│   └── tests/
│       └── __init__.py
│
├── assistant/                        # Microservice Assistant (port 8003)
│   ├── __init__.py
│   ├── main.py                       # Point d'entrée FastAPI
│   ├── Dockerfile                    # Image Docker multi-stage
│   ├── requirements.txt              # Dépendances Python (+ LangGraph)
│   ├── agents/
│   │   ├── __init__.py
│   │   └── assistant_agent.py        # LangGraph StateGraph (3 nodes)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── assistant.py          # 2 endpoints (interpret, answer)
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── airport_client.py         # Proxy HTTP vers Airport Service
│   │   └── flight_client.py          # Proxy HTTP vers Flight Service
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Configuration + DEMO_MODE flag
│   ├── models/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── requests.py           # PromptRequest schema
│   │   │   └── responses.py          # InterpretResponse, AnswerResponse
│   │   └── domain/
│   │       ├── __init__.py
│   │       └── state.py              # LangGraph State TypedDict
│   └── tools/
│       ├── __init__.py
│       ├── airport_tools.py          # 5 outils LangGraph aéroports
│       ├── flight_tools.py           # 2 outils LangGraph vols
│       └── mock_data/
│           ├── __init__.py
│           ├── airports.py           # Mock LIL, CDG (DEMO mode)
│           └── flights.py            # Mock AV15, AF282 (DEMO mode)
│
├── CLAUDE.md                         # Instructions pour Claude
├── docker-compose.yml                # Orchestration 4 services
├── requests.http                     # 43 exemples de requêtes
├── .env                              # Secrets (non versionné, .gitignore)
├── .gitignore
└── README.md
```

### MongoDB Collections

| Collection | Type | Description | Index |
|------------|------|-------------|-------|
| `airport_cache` | Cache | Aéroports consultés | TTL sur `expires_at` (300s) |
| `flight_cache` | Cache | Vols consultés (temps réel) | TTL sur `expires_at` (300s) |
| `flights` | Persistant | Historique complet des vols | Composite unique `(flight_iata, flight_date)` |

---

## ✅ Prérequis

- **Docker** >= 20.10
- **Docker Compose** >= 1.29
- **Clés API** :
  - [Aviationstack](https://aviationstack.com) (Basic Plan gratuit - 100 calls/mois)
  - [Mistral AI](https://console.mistral.ai/) (crédits gratuits disponibles)

---

## 🚀 Installation

### 1. Cloner le Repository

```bash
git clone https://github.com/lougail/hello-mira-flight-platform.git
cd hello-mira-flight-platform
```

### 2. Créer le Fichier `.env`

Créer un fichier `.env` à la racine du projet avec vos clés API :

```env
# API Aviationstack (OBLIGATOIRE)
AVIATIONSTACK_API_KEY=votre_cle_ici

# MongoDB (OBLIGATOIRE)
MONGO_PASSWORD=votre_mot_de_passe_securise

# Mistral AI (OBLIGATOIRE pour mode PRODUCTION)
MISTRAL_API_KEY=votre_cle_mistral_ici
```

### 3. Lancer les Services

```bash
docker-compose up -d
```

Les services démarrent dans cet ordre :

1. MongoDB (avec health check)
2. Airport Service (attend MongoDB)
3. Flight Service (attend MongoDB)
4. Assistant Service (attend Airport + Flight)

### 4. Vérifier l'État

```bash
# Vérifier que tous les services sont UP
docker-compose ps

# Health checks
curl http://localhost:8001/api/v1/health  # Airport
curl http://localhost:8002/api/v1/health  # Flight
curl http://localhost:8003/api/v1/health  # Assistant

# Logs en temps réel
docker-compose logs -f assistant
```

### 5. Accéder à la Documentation

- **Airport API** : <http://localhost:8001/docs>
- **Flight API** : <http://localhost:8002/docs>
- **Assistant API** : <http://localhost:8003/docs>

---

## ⚙️ Configuration

### Variables d'Environnement

Le projet utilise une architecture en 3 couches pour la configuration :

1. **`.env`** : Secrets et configuration changeant selon l'environnement (dev/prod)
2. **`docker-compose.yml`** : Overrides pour l'environnement Docker
3. **`*/config/settings.py`** : Valeurs par défaut techniques

### Fichier `.env` (Obligatoire)

Créer un fichier `.env` à la racine avec les variables suivantes :

```env
# =============================================================================
# API KEYS (Secrets - OBLIGATOIRE)
# =============================================================================
AVIATIONSTACK_API_KEY=votre_cle_ici          # ✅ OBLIGATOIRE
MISTRAL_API_KEY=votre_cle_mistral_ici        # ✅ OBLIGATOIRE (si DEMO_MODE=false)

# =============================================================================
# MONGODB
# =============================================================================
MONGO_PASSWORD=votre_mot_de_passe            # ✅ OBLIGATOIRE

# =============================================================================
# APPLICATION SETTINGS (Configurables selon environnement)
# =============================================================================
DEBUG=false                                  # true en dev, false en prod
DEMO_MODE=false                              # true = données mockées (pas d'appels API)
MISTRAL_MODEL=open-mixtral-8x7b              # open-mixtral-8x7b (gratuit) ou mistral-large-latest (payant)
```

### Variables Docker Compose

Lors du déploiement Docker, `docker-compose.yml` override certaines variables :

#### Services Airport & Flight

| Variable | Valeur Docker | Description |
|----------|---------------|-------------|
| `MONGODB_URL` | `mongodb://admin:${MONGO_PASSWORD}@mongo:27017` | URL avec authentification |
| `MONGODB_DATABASE` | `hello_mira` | Nom de la base de données |
| `MONGODB_TIMEOUT` | `5000` | Timeout connexion (ms) |
| `CACHE_TTL` | `300` | Durée cache (5 minutes) |
| `DEBUG` | `${DEBUG:-false}` | Utilise .env ou false par défaut |

#### Service Assistant

| Variable | Valeur Docker | Description |
|----------|---------------|-------------|
| `MISTRAL_MODEL` | `${MISTRAL_MODEL:-open-mixtral-8x7b}` | Utilise .env ou open-mixtral-8x7b |
| `MISTRAL_TEMPERATURE` | `0.0` | Température LLM (déterministe) |
| `AIRPORT_API_URL` | `http://airport:8001/api/v1` | URL interne Docker Airport |
| `FLIGHT_API_URL` | `http://flight:8002/api/v1` | URL interne Docker Flight |
| `HTTP_TIMEOUT` | `30` | Timeout appels HTTP (secondes) |
| `DEBUG` | `${DEBUG:-false}` | Utilise .env ou false |
| `DEMO_MODE` | `${DEMO_MODE:-false}` | Utilise .env ou false |
| `MAX_TOKENS` | `1000` | Tokens max pour réponses LLM |
| `ENABLE_STREAMING` | `false` | Streaming désactivé |

### Variables settings.py (Defaults)

Chaque microservice définit des valeurs par défaut dans `*/config/settings.py` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `aviationstack_base_url` | `http://api.aviationstack.com/v1` | URL API Aviationstack |
| `aviationstack_timeout` | `30` | Timeout requêtes (secondes) |
| `mongodb_url` | `mongodb://localhost:27017` | URL MongoDB (local) |
| `mongodb_database` | `hello_mira` | Nom base de données |
| `cache_ttl` | `300` | Durée cache (secondes) |
| `app_name` | `Hello Mira - [Service]` | Nom du service |
| `app_version` | `1.0.0` | Version |
| `cors_origins` | `["http://localhost:3000", ...]` | Origines CORS autorisées |

**Note** : Ces valeurs sont overridées par docker-compose.yml en production

---

**Note** : Ce README documente l'état du projet au 24 novembre 2024. Toutes les informations sont basées sur le code réel du repository.

---

<!-- SECTIONS À COMPLÉTER : Endpoints API, Mode DEMO, Exemples, Troubleshooting -->
