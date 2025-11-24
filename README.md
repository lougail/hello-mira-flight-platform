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
- [Architecture](#️-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#️-configuration)
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

**Exemples de prompts** :

- "Je suis sur le vol AF282, à quelle heure j'arrive ?"
- "Quels vols partent de CDG cet après-midi ?"
- "Trouve-moi l'aéroport le plus proche de Lille"
- "Donne-moi les statistiques du vol BA117"

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
- **AF282** - Air France (CDG → JFK, statut complet)
- **BA117** - British Airways (avec historique et statistiques)

**Vols au départ/arrivée** :

- Liste de 5 vols au départ de CDG
- Liste de 5 vols à l'arrivée à CDG

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
  -d '{"prompt": "Donne-moi les statistiques du vol BA117"}'
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

- Données limitées (3 aéroports, 3 vols)
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
  "data": {
    "airport_name": "Charles de Gaulle Airport",
    "iata_code": "CDG",
    "icao_code": "LFPG",
    "latitude": 49.012779,
    "longitude": 2.55,
    "country_name": "France",
    "city_iata_code": "PAR"
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
  "data": {
    "airport_name": "Paris-Le Bourget Airport",
    "iata_code": "LBG",
    "icao_code": "LFPB",
    "latitude": 48.969444,
    "longitude": 2.441389,
    "country_name": "France",
    "distance_km": 12.8
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
  "data": [
    {
      "flight_date": "2024-11-24",
      "flight_status": "scheduled",
      "departure": {
        "airport": "Charles de Gaulle Airport",
        "iata": "CDG",
        "scheduled": "2024-11-24T14:30:00+00:00"
      },
      "arrival": {
        "airport": "John F Kennedy International Airport",
        "iata": "JFK"
      },
      "airline": {"name": "Air France", "iata": "AF"},
      "flight": {"number": "282", "iata": "AF282"}
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 5,
    "total": 150
  }
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
  "data": {
    "flight_date": "2024-11-24",
    "flight_status": "active",
    "departure": {
      "airport": "Charles de Gaulle Airport",
      "iata": "CDG",
      "scheduled": "2024-11-24T14:30:00+00:00",
      "estimated": "2024-11-24T14:45:00+00:00",
      "delay": 15
    },
    "arrival": {
      "airport": "John F Kennedy International Airport",
      "iata": "JFK",
      "scheduled": "2024-11-24T17:15:00+00:00",
      "estimated": "2024-11-24T17:30:00+00:00"
    },
    "airline": {"name": "Air France", "iata": "AF"},
    "flight": {"number": "282", "iata": "AF282"}
  }
}
```

#### Consulter l'historique d'un vol

```bash
curl "http://localhost:8002/api/v1/flights/AF282/history?start_date=2024-11-01&end_date=2024-11-24"
```

**Réponse** :

```json
{
  "data": {
    "flight_iata": "AF282",
    "period": {
      "start_date": "2024-11-01",
      "end_date": "2024-11-24"
    },
    "flights": [
      {
        "flight_date": "2024-11-24",
        "flight_status": "active",
        "departure": {
          "iata": "CDG",
          "scheduled": "2024-11-24T14:30:00+00:00"
        },
        "arrival": {
          "iata": "JFK",
          "scheduled": "2024-11-24T17:15:00+00:00"
        }
      }
    ],
    "total_flights": 24
  }
}
```

#### Obtenir les statistiques d'un vol

```bash
curl "http://localhost:8002/api/v1/flights/AF282/statistics?start_date=2024-10-01&end_date=2024-11-24"
```

**Réponse** :

```json
{
  "data": {
    "flight_iata": "AF282",
    "period": {
      "start_date": "2024-10-01",
      "end_date": "2024-11-24"
    },
    "statistics": {
      "total_flights": 55,
      "on_time": 42,
      "delayed": 10,
      "cancelled": 3,
      "on_time_rate": 76.36,
      "average_delay_minutes": 12.5,
      "max_delay_minutes": 45
    }
  }
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
    "scheduled_arrival": "2024-11-24T17:15:00+00:00",
    "estimated_arrival": "2024-11-24T17:30:00+00:00",
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

Un fichier `requests.http` est fourni à la racine avec 43 exemples de requêtes.

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
