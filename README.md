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
- ✅ **Multi-langue automatique** (FR/EN/ES...) - Détecte la langue et répond dans la même
- ✅ **Enrichissement données vol** avec pays de destination (arrival_country)

**Optimisations :**

- ✅ **Cache MongoDB** avec TTL de 300 secondes (5 minutes) - Hit rate 63-65%
- ✅ **Request Coalescing** : Fusion des requêtes identiques simultanées - ~27% des requêtes
- ✅ **Économie globale** : ~70% de réduction d'appels API (cache + coalescing combinés)
- ✅ **Asynchronisme complet** : httpx.AsyncClient, async/await partout
- ✅ **Historique persistant** avec accumulation progressive
- ✅ **Index MongoDB optimisés** (TTL + composite unique)

**Monitoring (6 services Docker) :**

- ✅ **Prometheus** (port 9090) : Collecte de métriques custom (cache, coalescing, latency)
- ✅ **Grafana** (port 3000) : Dashboard avec 19 panels de monitoring temps réel
- ✅ **Tests e2e** : 16/16 tests passent (100%) - Validation complète de l'orchestration
- ✅ **77 commits** : Historique complet du développement

---

## 🔧 Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | FastAPI | 0.122.0 |
| **Serveur ASGI** | Uvicorn | 0.38.0 |
| **Validation** | Pydantic | 2.12.4 |
| **Configuration** | Pydantic Settings | 2.12.0 |
| **Base de données** | MongoDB | 7.0 |
| **Driver MongoDB** | PyMongo | 4.15.4 |
| **Client HTTP** | httpx | 0.28.1 |
| **Orchestration IA** | LangGraph | 1.0.3 |
| **LangChain Core** | langchain-core | 1.1.0 |
| **Integration Mistral** | langchain-mistralai | 1.1.0 |
| **Modèle LLM** | Mistral AI | open-mixtral-8x7b (défaut) / mistral-large-latest |
| **API Externe Vols** | Aviationstack | Basic Plan |
| **Géocodage** | Nominatim (OSM) | - |
| **Monitoring** | Prometheus | 2.54.0 |
| **Visualisation** | Grafana | 10.2.2 |
| **Métriques** | prometheus_fastapi_instrumentator | 7.1.0 |
| **Tests** | pytest + pytest-asyncio | 9.0.1 / 1.3.0 |
| **Container** | Docker Compose | v3.8 |

---

## 📋 Table des Matières

- [Vue d'Ensemble](#-vue-densemble)
- [Stack Technique](#-stack-technique)
- [Architecture](#️-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Monitoring & Métriques](#-monitoring--métriques)
- [Tests](#-tests)
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
│   │   ├── aviationstack_client.py   # Client HTTP Aviationstack
│   │   └── request_coalescer.py      # Request Coalescing pattern
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
│   ├── monitoring/                   # Monitoring Prometheus
│   │   ├── __init__.py
│   │   └── metrics.py                # Métriques custom (cache, coalescing)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── airport_service.py        # Logique métier aéroports
│   │   ├── cache_service.py          # Service cache MongoDB
│   │   └── geocoding_service.py      # Géocodage Nominatim
│   └── tests/                        # Tests
│       ├── __init__.py
│       ├── conftest.py               # Fixtures pytest niveau service
│       ├── exploration/              # Scripts exploration empirique
│       │   ├── __init__.py
│       │   ├── README.md
│       │   ├── explore_api_structure.py
│       │   ├── explore_client.py
│       │   ├── explore_models.py
│       │   ├── explore_services.py
│       │   └── explore_settings.py
│       ├── fixtures/                 # Fixtures complexes
│       │   └── __init__.py
│       ├── integration/              # Tests endpoints API
│       │   ├── __init__.py
│       │   ├── conftest.py
│       │   └── test_airports_endpoints.py
│       ├── mocks/                    # Données mockées
│       │   ├── __init__.py
│       │   ├── airport_response_sample.json
│       │   └── flight_response_sample.json
│       └── unit/                     # Tests unitaires
│           ├── __init__.py
│           └── conftest.py
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
│   │   ├── aviationstack_client.py   # Client HTTP Aviationstack
│   │   └── request_coalescer.py      # Request Coalescing pattern
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
│   ├── monitoring/                   # Monitoring Prometheus
│   │   ├── __init__.py
│   │   └── metrics.py                # Métriques custom (cache, coalescing)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py          # Service cache MongoDB
│   │   └── flight_service.py         # Logique métier vols + stats
│   └── tests/                        # Tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── exploration/
│       │   ├── __init__.py
│       │   └── README.md
│       ├── fixtures/
│       │   └── __init__.py
│       ├── integration/
│       │   ├── __init__.py
│       │   └── conftest.py
│       ├── mocks/
│       │   └── __init__.py
│       └── unit/
│           ├── __init__.py
│           └── conftest.py
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
├── monitoring/                       # Infrastructure Monitoring
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── hello-mira-metrics.json  # Dashboard 19 panels (5 sections)
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   └── default.yml
│   │       └── datasources/
│   │           └── grafana-datasources.yml
│   └── prometheus.yml                # Configuration Prometheus
│
├── tests/                            # Tests cross-services
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures globales e2e
│   ├── README.md                     # Documentation tests (Best Practices 2025)
│   ├── e2e/                          # Tests end-to-end
│   │   ├── __init__.py
│   │   ├── conftest.py               # Scénarios e2e
│   │   ├── test_airport_service.py   # 4 tests Airport
│   │   ├── test_assistant_orchestration.py  # 6 tests Assistant
│   │   └── test_flight_service.py    # 6 tests Flight
│   └── performance/                  # Tests performance bash
│       ├── __init__.py
│       ├── test_cache_and_coalescing.sh
│       ├── test_cache_isolated.sh
│       └── test_coalescing_isolated.sh
│
├── CLAUDE.md                         # Instructions pour Claude
├── PROJECT_STATUS.md                 # État détaillé du projet
├── pytest.ini                        # Configuration pytest
├── docker-compose.yml                # Orchestration 6 services
├── requests.http                     # 52 exemples de requêtes HTTP
├── .env.example                      # Template variables d'environnement
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

Les **6 services** démarrent dans cet ordre :

1. **MongoDB** (avec health check) - port 27017
2. **Airport Service** (attend MongoDB) - port 8001
3. **Flight Service** (attend MongoDB) - port 8002
4. **Assistant Service** (attend Airport + Flight) - port 8003
5. **Prometheus** (attend les microservices) - port 9090
6. **Grafana** (attend Prometheus) - port 3000

### 4. Vérifier l'État

```bash
# Vérifier que tous les 6 services sont UP (healthy)
docker-compose ps

# Health checks des microservices
curl http://localhost:8001/api/v1/health  # Airport
curl http://localhost:8002/api/v1/health  # Flight
curl http://localhost:8003/api/v1/health  # Assistant

# Vérifier Prometheus et Grafana
curl http://localhost:9090/-/healthy       # Prometheus
curl http://localhost:3000/api/health      # Grafana

# Logs en temps réel
docker-compose logs -f assistant
```

### 5. Accéder aux Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| **Airport API** | <http://localhost:8001/docs> | Documentation Swagger Airport |
| **Flight API** | <http://localhost:8002/docs> | Documentation Swagger Flight |
| **Assistant API** | <http://localhost:8003/docs> | Documentation Swagger Assistant |
| **Grafana** | <http://localhost:3000> | Dashboard monitoring (admin/admin) |
| **Prometheus** | <http://localhost:9090> | Métriques brutes |

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

**Note** : Ce README documente l'état du projet au 27 novembre 2024. Toutes les informations sont basées sur le code réel du repository.

---

## 📡 Endpoints API

Tous les endpoints sont documentés automatiquement via FastAPI Swagger UI.

### Airport Service (Port 8001)

**Base URL** : `http://localhost:8001/api/v1`
**Documentation** : <http://localhost:8001/docs>

#### Recherche d'Aéroports

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/airports/{iata_code}` | GET | Aéroport par code IATA | `iata_code` : Code IATA 3 lettres (ex: CDG) |
| `/airports/search` | GET | Recherche par nom de lieu | `name`, `country_code` (2 lettres), `limit` (défaut 10), `offset` (défaut 0) |
| `/airports/nearest-by-coords` | GET | Aéroport le plus proche (GPS) | `latitude` (-90 à 90), `longitude` (-180 à 180), `country_code` (2 lettres) |
| `/airports/nearest-by-address` | GET | Aéroport le plus proche (adresse) | `address` (min 3 car), `country_code` (2 lettres) |

#### Vols Liés aux Aéroports

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/airports/{iata_code}/departures` | GET | Vols au départ | `iata_code` (Code IATA), `limit` (1-100, défaut 10), `offset` (pagination) |
| `/airports/{iata_code}/arrivals` | GET | Vols à l'arrivée | `iata_code` (Code IATA), `limit` (1-100, défaut 10), `offset` (pagination) |

#### Health Check

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | Liveness probe (toujours 200 OK) |
| `/health/ready` | GET | Readiness probe (vérifie dépendances) |

---

### Flight Service (Port 8002)

**Base URL** : `http://localhost:8002/api/v1`
**Documentation** : <http://localhost:8002/docs>

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/flights/{flight_iata}` | GET | Statut en temps réel | `flight_iata` (Code vol, ex: AF447) |
| `/flights/{flight_iata}/history` | GET | Historique sur période | `flight_iata` (Code vol), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `/flights/{flight_iata}/statistics` | GET | Statistiques agrégées | `flight_iata` (Code vol), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `/health` | GET | Liveness probe (toujours 200 OK) | - |
| `/health/ready` | GET | Readiness probe (vérifie dépendances) | - |

**Limites** :

- Période max history/statistics : **90 jours**
- Données historiques : **3 mois en arrière** (API Aviationstack Basic)

---

### Assistant Service (Port 8003)

**Base URL** : `http://localhost:8003/api/v1`
**Documentation** : <http://localhost:8003/docs>

| Endpoint | Méthode | Description | Body |
|----------|---------|-------------|------|
| `/assistant/interpret` | POST | Détecte intention (pas d'exécution) | `{"prompt": "votre question"}` |
| `/assistant/answer` | POST | Orchestration complète (LangGraph) | `{"prompt": "votre question"}` |

**Exemples de prompts (multi-langue)** :

**Français** :

- "Je suis sur le vol AF282, à quelle heure j'arrive ?"
- "Quels vols partent de CDG cet après-midi ?"
- "Trouve-moi l'aéroport le plus proche de Lille"
- "Quels vols vont aux États-Unis depuis CDG ?"

**English** :

- "What is the status of flight AF282?"
- "Which flights depart from CDG this afternoon?"
- "Find the nearest airport to Paris"
- "Show me flights to Japan from CDG"

**Format réponse `/assistant/answer`** :

```json
{
  "answer": "Réponse en langage naturel",
  "data": { /* Données structurées */ }
}
```

**Format réponse `/assistant/interpret`** :

```json
{
  "intent": "get_flight_status",
  "entities": {"flight_iata": "AF282"},
  "confidence": 0.95
}
```

---

## 🎭 Mode DEMO

Le mode DEMO permet de tester le microservice **Assistant** avec des données mockées, **sans consommer de quota API Aviationstack**.

### Activation

Modifier le fichier `.env` à la racine du projet :

```env
DEMO_MODE=true
```

Puis recréer le container Assistant pour charger la nouvelle variable :

```bash
docker-compose up -d --force-recreate assistant
```

Ou redémarrer tous les services :

```bash
docker-compose down
docker-compose up -d
```

### Données Mockées Disponibles

Le mode DEMO utilise des données fictives cohérentes stockées dans `assistant/tools/mock_data/` :

**Aéroports** :

- **CDG** - Charles de Gaulle (Paris)
- **BOG** - El Dorado International (Bogota)
- **LIL** - Lille Airport

**Vols** :

- **AV15** - Avianca (BOG → CDG, en vol avec retard de 18 min)
- **AF282** - Air France (CDG → NRT, statut complet)

**Vols au départ** :

- Liste de 5 vols au départ de CDG (AF007, EK073, VY8004, BA314, AF282)

### Exemples de Prompts en Mode DEMO

Ces prompts fonctionnent avec les données mockées :

```bash
# Statut d'un vol
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Je suis sur le vol AV15, à quelle heure j'\''arrive ?"}'

# Recherche d'aéroport
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Trouve-moi l'\''aéroport le plus proche de Lille"}'

# Vols au départ
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Quels vols partent de CDG cet après-midi ?"}'

# Statistiques
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Donne-moi les statistiques du vol AV15"}'
```

### Avantages

**Économie de quota API** :

- Les appels à l'API Aviationstack sont simulés
- Idéal pour démonstrations, tests, développement

**Données cohérentes** :

- Horaires réalistes (basés sur l'heure actuelle)
- Retards, portes, terminaux fictifs mais plausibles
- Réponses instantanées (pas d'appel HTTP externe)

### Limitations

**vs Mode Production** :

- Données limitées (3 aéroports, 2 vols)
- Pas de recherche géographique réelle
- Historiques pré-générés (pas de données temps réel)
- Ne teste pas la connectivité avec Airport/Flight microservices

**Important** : Le mode DEMO ne concerne que le microservice **Assistant**. Les microservices Airport et Flight appellent toujours l'API Aviationstack (sauf si leur cache MongoDB contient les données).

### Vérification du Mode

Vérifier que le mode DEMO est actif dans les logs :

```bash
docker-compose logs assistant | grep "DEMO MODE"
```

Sortie attendue :

```log
assistant  | INFO:     AirportClient initialized in DEMO MODE - using mock data
assistant  | INFO:     FlightClient initialized in DEMO MODE - using mock data
```

---

## 📋 Exemples d'Utilisation

### Airport Service

#### Rechercher un aéroport par code IATA

```bash
curl http://localhost:8001/api/v1/airports/CDG
```

**Réponse** :

```json
{
  "iata_code": "CDG",
  "icao_code": "LFPG",
  "name": "Charles de Gaulle International Airport",
  "city": "Paris",
  "country": "France",
  "country_code": "FR",
  "timezone": "Europe/Paris",
  "coordinates": {
    "latitude": 49.012779,
    "longitude": 2.55
  }
}
```

#### Rechercher un aéroport par coordonnées GPS

```bash
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=48.8566&longitude=2.3522"
```

**Réponse** :

```json
{
  "iata_code": "LBG",
  "icao_code": "LFPB",
  "name": "Paris-Le Bourget Airport",
  "city": "Paris",
  "country": "France",
  "country_code": "FR",
  "timezone": "Europe/Paris",
  "coordinates": {
    "latitude": 48.969444,
    "longitude": 2.441389
  }
}
```

#### Lister les vols au départ

```bash
curl "http://localhost:8001/api/v1/airports/CDG/departures?limit=5"
```

**Réponse** :

```json
{
  "flights": [
    {
      "flight_number": "282",
      "flight_iata": "AF282",
      "flight_date": "2025-11-24",
      "status": "scheduled",
      "departure_airport": "Charles de Gaulle International Airport",
      "departure_iata": "CDG",
      "departure_schedule": {
        "scheduled": "2025-11-24T14:30:00+00:00",
        "estimated": "2025-11-24T14:30:00+00:00",
        "actual": null,
        "delay_minutes": 0
      },
      "arrival_airport": "John F Kennedy International Airport",
      "arrival_iata": "JFK",
      "arrival_schedule": {
        "scheduled": "2025-11-24T17:15:00+00:00",
        "estimated": null,
        "actual": null,
        "delay_minutes": null
      },
      "airline_name": "Air France",
      "airline_iata": "AF"
    }
  ],
  "total": 150,
  "limit": 5,
  "offset": 0,
  "airport_iata": "CDG"
}
```

### Flight Service

#### Obtenir le statut d'un vol

```bash
curl http://localhost:8002/api/v1/flights/AF282
```

**Réponse** :

```json
{
  "flight_iata": "AF282",
  "flight_number": "282",
  "flight_date": "2025-11-24",
  "flight_status": "active",
  "departure": {
    "scheduled_time": "2025-11-24T14:30:00+00:00",
    "estimated_time": "2025-11-24T14:45:00+00:00",
    "actual_time": null,
    "delay_minutes": 15,
    "terminal": "2F",
    "gate": "K42",
    "airport_iata": "CDG"
  },
  "arrival": {
    "scheduled_time": "2025-11-24T17:15:00+00:00",
    "estimated_time": "2025-11-24T17:30:00+00:00",
    "actual_time": null,
    "delay_minutes": null,
    "terminal": "4",
    "gate": null,
    "airport_iata": "JFK"
  },
  "airline_name": "Air France",
  "airline_iata": "AF",
  "airline_icao": "AFR"
}
```

#### Consulter l'historique d'un vol

```bash
curl "http://localhost:8002/api/v1/flights/AF282/history?start_date=2025-11-01&end_date=2025-11-24"
```

**Réponse** :

```json
{
  "flight_iata": "AF282",
  "flights": [
    {
      "flight_iata": "AF282",
      "flight_number": "282",
      "flight_date": "2025-11-24",
      "flight_status": "landed",
      "departure": {
        "scheduled_time": "2025-11-24T14:30:00+00:00",
        "estimated_time": "2025-11-24T14:30:00+00:00",
        "actual_time": "2025-11-24T14:32:00+00:00",
        "delay_minutes": 2,
        "terminal": "2F",
        "gate": "K42",
        "airport_iata": "CDG"
      },
      "arrival": {
        "scheduled_time": "2025-11-24T17:15:00+00:00",
        "estimated_time": "2025-11-24T17:17:00+00:00",
        "actual_time": "2025-11-24T17:20:00+00:00",
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
  "total": 24,
  "start_date": "2025-11-01",
  "end_date": "2025-11-24"
}
```

#### Obtenir les statistiques d'un vol

```bash
curl "http://localhost:8002/api/v1/flights/AF282/statistics?start_date=2025-10-01&end_date=2025-11-24"
```

**Réponse** :

```json
{
  "flight_iata": "AF282",
  "total_flights": 55,
  "on_time_count": 42,
  "delayed_count": 10,
  "cancelled_count": 3,
  "on_time_rate": 76.36,
  "delay_rate": 18.18,
  "cancellation_rate": 5.45,
  "average_delay_minutes": 12.5,
  "max_delay_minutes": 45,
  "average_duration_minutes": 480.2,
  "start_date": "2025-10-01",
  "end_date": "2025-11-24"
}
```

### Assistant Service

#### Poser une question en langage naturel

```bash
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Je suis sur le vol AF282, à quelle heure j'\''arrive ?"}'
```

**Réponse** :

```json
{
  "answer": "Le vol AF282 est prévu à 17h15 (heure locale) avec un retard estimé de 15 minutes. Vous devriez arriver à 17h30.",
  "data": {
    "flight_iata": "AF282",
    "scheduled_arrival": "2025-11-24T17:15:00+00:00",
    "estimated_arrival": "2025-11-24T17:30:00+00:00",
    "delay_minutes": 15,
    "arrival_airport": "JFK"
  }
}
```

#### Interpréter l'intention (sans exécution)

```bash
curl -X POST "http://localhost:8003/api/v1/assistant/interpret" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Trouve-moi l'\''aéroport le plus proche de Lille"}'
```

**Réponse** :

```json
{
  "intent": "find_nearest_airport",
  "entities": {
    "location": "Lille"
  },
  "confidence": 0.92,
  "action": "search_airport_by_address"
}
```

### Tester avec requests.http (VS Code)

Un fichier `requests.http` est fourni à la racine avec 52 exemples de requêtes.

Exemples :

```http
### Rechercher un aéroport
GET http://localhost:8001/api/v1/airports/CDG

### Vols au départ
GET http://localhost:8001/api/v1/airports/CDG/departures?limit=3

### Statut d'un vol
GET http://localhost:8002/api/v1/flights/AF282

### Assistant - Question IA
POST http://localhost:8003/api/v1/assistant/answer
Content-Type: application/json

{
  "prompt": "Quels vols partent de CDG cet après-midi ?"
}
```

---

## 📊 Monitoring & Métriques

Le projet intègre un stack de monitoring complet basé sur **Prometheus** et **Grafana** pour observer les performances en temps réel et valider les optimisations (cache, coalescing).

### Architecture Monitoring

```text
┌─────────────────┐
│   Microservices │  (Airport, Flight, Assistant)
│   Port 8001-8003│
│   /metrics      │  ← prometheus-fastapi-instrumentator
└────────┬────────┘
         │ HTTP scrape (10s)
         ▼
┌─────────────────┐
│   Prometheus    │  Port 9090
│   - Collecte    │  ← Stockage Time Series Database
│   - Agrégation  │
└────────┬────────┘
         │ PromQL queries
         ▼
┌─────────────────┐
│     Grafana     │  Port 3000
│   - Dashboard   │  ← Visualisation
│   - 19 panels   │
└─────────────────┘
```

### Accès aux Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | [http://localhost:3000](http://localhost:3000) | admin / admin |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | - |

**Dashboard principal** : "Hello Mira - Flight Platform Metrics"

- Disponible automatiquement au démarrage (provisioning)
- 19 panels de monitoring (5 sections organisées)
- Refresh automatique : 10 secondes
- Time range : Last 15 minutes (ajustable)

### Métriques Collectées

#### Métriques Standard (prometheus-fastapi-instrumentator)

| Métrique | Type | Description | Labels |
|----------|------|-------------|--------|
| `http_request_duration_seconds` | Histogram | Latence des requêtes HTTP | `handler`, `method`, `status` |
| `http_request_duration_seconds_count` | Counter | Nombre total de requêtes | `handler`, `method`, `status` |
| `http_requests_inprogress` | Gauge | Requêtes en cours | `handler`, `method` |

#### Métriques Custom Airport/Flight

| Métrique | Type | Description | Labels |
|----------|------|-------------|--------|
| `cache_hits_total` | Counter | Nombre de cache HITs | `service`, `cache_type` |
| `cache_misses_total` | Counter | Nombre de cache MISSes | `service`, `cache_type` |
| `coalesced_requests_total` | Counter | Requêtes coalescées (dupliquées évitées) | `service`, `endpoint` |
| `aviationstack_api_calls_total` | Counter | Appels réels à l'API Aviationstack | `service`, `endpoint` |

### Panels Grafana

Le dashboard contient **19 panels** organisés en **5 sections** :

#### Section 1 : ⚡ MÉTRIQUES TEMPS RÉEL (5 dernières minutes)

4 panels avec fenêtre glissante 5m :

| Panel | Type | Métrique | Seuils |
|-------|------|----------|--------|
| **🎯 Cache Hit Rate - Airport (5m)** | Gauge | `increase(cache_hits)[5m] / (hits+misses)` | Rouge <50%, Jaune <70%, Vert ≥70% |
| **🎯 Cache Hit Rate - Flight (5m)** | Gauge | `increase(cache_hits)[5m] / (hits+misses)` | Rouge <50%, Jaune <70%, Vert ≥70% |
| **🔗 Taux de Coalescing (5m)** | Gauge | `increase(coalesced)[5m] / (coalesced+api_calls)` | Rouge <50%, Jaune <70%, Vert ≥70% |
| **📡 API Calls (5m)** | Timeseries | `rate(aviationstack_api_calls_total)[5m] * 60` | Affiche appels/min par service |

#### Section 2 : 📊 MÉTRIQUES CUMULATIVES (depuis démarrage)

7 panels avec valeurs totales :

| Panel | Type | Métrique | Description |
|-------|------|----------|-------------|
| **🎯 Cache Hit Rate - Airport (Total)** | Gauge | `sum(cache_hits) / (hits+misses)` | Taux cumulé depuis démarrage |
| **🎯 Cache Hit Rate - Flight (Total)** | Gauge | `sum(cache_hits) / (hits+misses)` | Taux cumulé depuis démarrage |
| **🔗 Taux de Coalescing (Total)** | Gauge | `sum(coalesced) / (coalesced+api_calls)` | Taux cumulé depuis démarrage |
| **📡 Total API Calls** | Stat | `sum(aviationstack_api_calls_total)` | Nombre total d'appels API |
| **Total Requêtes Coalescées** | Stat | `sum(coalesced_requests_total)` | Économie via coalescing |
| **Total Cache Hits** | Stat | `sum(cache_hits_total)` | Économie via cache |
| **Économie Totale** | Bar Gauge | Coalescées + Cache Hits vs API Calls | Visualisation comparative |

#### Section 3 : 📊 PERFORMANCE DES APIS

2 panels de performance :

| Panel | Type | Métrique | Description |
|-------|------|----------|-------------|
| **⚡ Latence des APIs (p50 / p95)** | Timeseries | `histogram_quantile(0.50/0.95, ...)` | Latence médiane et 95e percentile |
| **📈 Requêtes HTTP par seconde** | Timeseries | `sum(rate(http_request_duration_seconds_count)[1m])` | Volume de requêtes par service |

#### Section 4 : 🤖 ASSISTANT IA CONVERSATIONNEL

3 panels dédiés à l'assistant :

| Panel | Type | Métrique | Description |
|-------|------|----------|-------------|
| **✅ Taux de Succès Assistant IA** | Pie Chart | `http_request_duration_seconds_count{status}` | Distribution 2xx / 4xx / 5xx |
| **⚡ Latence Assistant p50 (5m)** | Gauge | `histogram_quantile(0.50, ...)` | Latence médiane assistant |
| **🤖 Total Requêtes Assistant IA** | Stat | `sum(http_request_duration_seconds_count{job="assistant"})` | Volume total requêtes |

#### Section 5 : 🌐 CONSOMMATION API AVIATIONSTACK (QUOTA)

3 panels de monitoring quota :

| Panel | Type | Métrique | Description |
|-------|------|----------|-------------|
| **📞 Total Appels API Aviationstack** | Stat | `sum(aviationstack_api_calls_total)` | Suivi quota mensuel |
| **📊 Appels API par minute** | Timeseries | `rate(aviationstack_api_calls_total)[1m] * 60` | Tendance consommation |
| **🍩 Répartition par Endpoint** | Pie Chart | `sum by (endpoint) (aviationstack_api_calls_total)` | Distribution airports/flights |

### Script de Génération de Trafic

Un script bash est fourni pour tester le monitoring avec un trafic réaliste :

```bash
# Générer ~300 requêtes mixtes (Airport, Flight, Assistant)
./scripts/generate_traffic_intensive.sh

# Avec paramètre custom (100 iterations = ~600 requêtes)
./scripts/generate_traffic_intensive.sh 100
```

**Le script :**

1. **Récupère des données réelles** depuis l'API (50 vols de CDG)
2. **Sépare les données** de manière déterministe :
   - Aéroports 1-10 : Trafic mixte normal
   - Aéroport 11 : Test coalescing (cache MISS garanti)
   - Réutilisation aéroport 11 : Test cache (cache HIT garanti)
3. **Génère du trafic mixte** :
   - 40% Airport (recherche aéroports, départs/arrivées)
   - 30% Flight (statut vols réels)
   - 30% Assistant (prompts en français avec vols réels)
4. **Teste le coalescing** : 10 requêtes simultanées identiques
5. **Teste le cache** : 20 requêtes séquentielles identiques

**Sortie attendue** :

```text
📊 Statistiques :
  - Total requêtes : 333
  - Airport : 237 (71%)
  - Flight : 48 (14%)
  - Assistant : 48 (14%)

📈 Prochaines étapes :
  1. Attends 15s que Prometheus scrape les données
  2. Rafraîchis Grafana : http://localhost:3000
  3. Vérifie les panels
```

### Résultats Validés (Test Réel)

Après exécution du script sur une plateforme propre :

| Métrique | Valeur | Détail |
|----------|--------|--------|
| **Cache Hit Rate Airport** | **63.6%** | 21 hits / 33 requêtes |
| **Cache Hit Rate Flight** | **65.0%** | 13 hits / 20 requêtes |
| **Taux de Coalescing** | **27.3%** | 9 coalescées / 33 requêtes |
| **Total Cache Hits** | **48** | Cumul Airport + Flight |
| **Total Requêtes Coalescées** | **9** | Requêtes dupliquées évitées |
| **API Calls économisés** | **~70%** | Via cache + coalescing |
| **Assistant Success Rate** | **100%** | 24/24 requêtes réussies |
| **API Calls Réels Aviationstack** | **24** | Sur ~81 requêtes totales |

**Interprétation** :

- ✅ Cache hit rate >60% démontre l'efficacité du cache MongoDB avec TTL 300s
- ✅ Coalescing rate 27% prouve que les requêtes simultanées sont bien fusionnées
- ✅ Économie globale ~70% d'appels API valide l'architecture d'optimisation
- ✅ Assistant 100% success rate confirme la robustesse de l'orchestration LangGraph

### Configuration Prometheus

**Scrape interval** : 10 secondes pour Airport/Flight/Assistant

```yaml
scrape_configs:
  - job_name: 'airport'
    scrape_interval: 10s
    static_configs:
      - targets: ['airport:8001']

  - job_name: 'flight'
    scrape_interval: 10s
    static_configs:
      - targets: ['flight:8002']

  - job_name: 'assistant'
    scrape_interval: 10s
    static_configs:
      - targets: ['assistant:8003']
```

**Retention** : 15 jours (par défaut)

### Requêtes PromQL Utiles

```promql
# Taux de succès HTTP
sum(http_request_duration_seconds_count{status="2xx"})
/ sum(http_request_duration_seconds_count)

# Cache hit rate
sum(cache_hits_total) / (sum(cache_hits_total) + sum(cache_misses_total))

# Latence p95
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)

# Volume de coalescing sur 5 minutes
increase(coalesced_requests_total[5m])
```

### Reset des Métriques

Si besoin de repartir de zéro (pour tests) :

```bash
# Arrêter les services
docker-compose down

# Supprimer le volume Prometheus (efface l'historique)
docker volume rm hello-mira-prometheus-data

# Redémarrer
docker-compose up -d

# Attendre 15s pour scraping initial
sleep 15
```

---

## ✅ Tests

Le projet intègre une suite de tests complète pour valider le comportement des microservices et l'orchestration.

### Tests End-to-End (e2e)

**Statut** : ✅ **16/16 tests passent** (100% success rate)

```bash
# Lancer tous les tests e2e
docker-compose exec airport pytest tests/e2e/ -v

# Ou depuis l'extérieur (avec services Docker running)
pytest tests/e2e/ -v
```

#### Couverture des Tests

| Service | Tests | Fichier | Scénarios |
|---------|-------|---------|-----------|
| **Airport** | 4 tests | `test_airport_service.py` | IATA, coords, address, departures |
| **Flight** | 6 tests | `test_flight_service.py` | Status, history, statistics |
| **Assistant** | 6 tests | `test_assistant_orchestration.py` | 7 outils + orchestration LangGraph |

#### Tests Assistant (LangGraph)

Les tests valident **l'orchestration complète** et l'intégration avec les services :

- `test_health_check` : Health check du service
- `test_interpret_airport_query` : Interprétation intention aéroport
- `test_assistant_calls_airport_service` : Appel service Airport
- `test_assistant_calls_flight_service` : Appel service Flight
- `test_full_user_journey` : Parcours utilisateur complet
- `test_airport_to_flights_workflow` : Workflow aéroport → vols

**Exemple de test** :

```python
@pytest.mark.asyncio
async def test_orchestration_full_workflow():
    """Test de l'orchestration complète : prompt → answer"""
    async with httpx.AsyncClient(base_url=ASSISTANT_BASE_URL) as client:
        response = await client.post(
            "/assistant/answer",
            json={"prompt": "Quel est le statut du vol AF447 ?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "data" in data
        assert "flight_iata" in data["data"]
```

### Tests de Performance

Scripts bash pour tests isolés d'optimisation :

```bash
# Test cache isolé
./tests/performance/test_cache_isolated.sh

# Test coalescing isolé
./tests/performance/test_coalescing_isolated.sh

# Test cache + coalescing combinés
./tests/performance/test_cache_and_coalescing.sh
```

**Métriques validées** :

- ✅ Cache hit rate > 60% (TTL 300s)
- ✅ Coalescing rate > 20% (requêtes simultanées)
- ✅ Latence p50 < 100ms (sans appel API externe)
- ✅ Latence p95 < 500ms

### Configuration pytest

Le projet utilise `pytest-asyncio` pour tester le code asynchrone :

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
```

### Fixtures Globales

Les fixtures sont organisées en 3 niveaux :

1. **`tests/conftest.py`** : Fixtures globales e2e (URLs, clients HTTP)
2. **`*/tests/conftest.py`** : Fixtures par service (mocks, données)
3. **`tests/e2e/conftest.py`** : Scénarios e2e complexes

### Mode DEMO pour Tests

Pour tester sans consommer de quota API Aviationstack :

```bash
# Activer le mode DEMO
export DEMO_MODE=true

# Recréer le container Assistant
docker-compose up -d --force-recreate assistant

# Les tests Assistant utilisent maintenant les données mockées
pytest tests/e2e/test_assistant_orchestration.py -v
```

### CI/CD (À venir)

Le projet est prêt pour intégration CI/CD avec :

- ✅ Tests e2e automatisables (`pytest tests/e2e/`)
- ✅ Docker Compose pour environnement isolé
- ✅ Health checks pour vérifier disponibilité services
- ✅ Métriques Prometheus pour monitoring post-déploiement

**Exemple GitHub Actions** (à implémenter) :

```yaml
name: Tests e2e
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Wait for readiness
        run: sleep 30
      - name: Run e2e tests
        run: pytest tests/e2e/ -v
      - name: Stop services
        run: docker-compose down
```

---

## 🔧 Troubleshooting

### Problème : Container ne démarre pas

**Symptôme** : `docker-compose up` échoue

**Solutions** :

1. Vérifier que le fichier `.env` existe et contient toutes les variables obligatoires
2. Vérifier les logs : `docker-compose logs <service>`
3. Vérifier que les ports 8001, 8002, 8003, 27017 ne sont pas déjà utilisés

```bash
# Windows
netstat -ano | findstr "8001"

# Linux/Mac
lsof -i :8001
```

### Problème : Health check échoue

**Symptôme** : Service reste `unhealthy` dans `docker-compose ps`

**Solutions** :

1. Vérifier les logs du service : `docker-compose logs <service>`
2. Vérifier la connectivité MongoDB : `docker-compose exec mongo mongosh`
3. Augmenter `start_period` dans `docker-compose.yml` si machine lente

### Problème : Erreur MongoDB Authentication Failed

**Symptôme** : `Authentication failed` dans les logs

**Solutions** :

1. Vérifier que `MONGO_PASSWORD` dans `.env` correspond à celui utilisé par MongoDB
2. Supprimer les volumes et recréer :

```bash
docker-compose down -v
docker-compose up -d
```

### Problème : API Aviationstack quota dépassé

**Symptôme** : Erreur 429 ou `Monthly API call volume exceeded`

**Solutions** :

1. Activer le mode DEMO pour l'Assistant :

```env
DEMO_MODE=true
```

2. Le cache MongoDB (TTL 300s) réduit les appels API - vérifier qu'il fonctionne :

```bash
docker-compose exec mongo mongosh hello_mira --eval "db.airport_cache.countDocuments()"
```

### Problème : Mistral API Key invalide

**Symptôme** : Erreur 401 sur les requêtes Assistant

**Solutions** :

1. Vérifier la clé API dans `.env` : `MISTRAL_API_KEY=xxx`

2. Tester la clé directement :

```bash
curl https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer VOTRE_CLE"
```

3. Activer le mode DEMO si pas de clé valide

### Problème : CORS errors depuis le frontend

**Symptôme** : `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solutions** :

1. Vérifier que l'origine est autorisée dans `docker-compose.yml` :

```yaml
CORS_ORIGINS: '["http://localhost:3000", "http://localhost:8000"]'
```

2. Ajouter l'origine du frontend si différente

### Problème : Container redémarre en boucle

**Symptôme** : `docker-compose ps` montre `Restarting`

**Solutions** :

1. Vérifier les logs : `docker-compose logs --tail=50 <service>`
2. Causes fréquentes :
   - Variable d'environnement manquante
   - Erreur dans le code Python (vérifier syntax)
   - MongoDB non accessible

### Logs utiles

```bash
# Logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f assistant

# Dernières 100 lignes
docker-compose logs --tail=100

# Logs avec timestamps
docker-compose logs -t
```

---

**Note** : Pour toute question ou bug, ouvrir une issue sur GitHub avec les logs complets.
