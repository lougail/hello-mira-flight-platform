# 🚀 Hello Mira Flight Platform - Vue d'Ensemble

## Table des Matières

1. [Introduction](#introduction)
2. [Architecture Globale](#architecture-globale)
3. [Stack Technologique](#stack-technologique)
4. [Services et Responsabilités](#services-et-responsabilités)
5. [Flux de Données](#flux-de-données)
6. [Patterns Architecturaux](#patterns-architecturaux)
7. [Structure du Projet](#structure-du-projet)
8. [Démarrage Rapide](#démarrage-rapide)
9. [Ports et Endpoints](#ports-et-endpoints)

---

## Introduction

**Hello Mira Flight Platform** est une plateforme intelligente pour les voyageurs, combinant IA conversationnelle et données aériennes en temps réel. Le système permet de :

- 🔍 **Rechercher des aéroports** par code IATA, nom, ville ou coordonnées GPS
- ✈️ **Suivre des vols** en temps réel avec statuts, retards et historique
- 📊 **Analyser les statistiques** de ponctualité sur des périodes données
- 💬 **Interagir en langage naturel** avec un assistant IA multi-langue (FR/EN/ES)

### Contexte du Projet

Ce projet a été développé dans le cadre d'un test technique pour Hello Mira, une startup développant une plateforme intelligente pour les voyageurs.

---

## Architecture Globale

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Streamlit)                              │
│                              Port 8501                                      │
│                    Authentification Supabase + UI                           │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │ HTTP REST
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASSISTANT SERVICE                                   │
│                            Port 8003                                        │
│              LangGraph + Mistral AI + ReAct Pattern                         │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      StateGraph (LangGraph)                          │   │
│  │                                                                      │   │
│  │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐   │   │
│  │   │ Analyze │──▶│  Plan   │───▶│ Execute │───▶│ Generate Answer │   │   │
│  │   │  Intent │    │  Tools  │    │  Tools  │    │   (Mistral)     │   │   │
│  │   └─────────┘    └─────────┘    └────┬────┘    └─────────────────┘   │   │
│  │                                      │                               │   │
│  │                           ┌──────────┴──────────┐                    │   │
│  │                           │    7 LangGraph      │                    │   │
│  │                           │       Tools         │                    │   │
│  │                           └─────────────────────┘                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────┬─────────────────────────┘
                 │ HTTP                             │ HTTP
                 ▼                                  ▼
┌────────────────────────────┐      ┌────────────────────────────────────────┐
│     AIRPORT SERVICE        │      │           FLIGHT SERVICE               │
│         Port 8001          │      │            Port 8002                   │
│                            │      │                                        │
│  • Recherche aéroports     │      │  • Statut vol en temps réel            │
│  • Géocodage adresses      │      │  • Historique des vols                 │
│  • Départs/Arrivées        │      │  • Statistiques de ponctualité         │
│  • Aéroport le plus proche │      │  • Lazy Loading automatique            │
└────────────┬───────────────┘      └──────────────┬───────────┬─────────────┘
             │                                     │           │
             └──────────────────┬──────────────────┘           │
                                │ HTTP                         │ MongoDB
                                ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GATEWAY SERVICE                                     │
│                            Port 8004                                        │
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │    Cache    │ │ Rate Limit  │ │ Circuit Breaker │ │   Request       │    │
│  │  MongoDB    │ │ 10K/month   │ │  (5 failures)   │ │   Coalescing    │    │
│  │  TTL=300s   │ │ auto-reset  │ │  30s recovery   │ │   (dedup)       │    │
│  └─────────────┘ └─────────────┘ └─────────────────┘ └─────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTPS
                                     ▼
                        ┌─────────────────────────────┐
                        │    Aviationstack API        │
                        │    (External Service)       │
                        │    10,000 calls/month       │
                        └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE                                   │
├──────────────────────┬─────────────────────┬────────────────────────────────┤
│      MongoDB 7.0     │    Prometheus       │         Grafana                │
│      Port 27017      │    Port 9090        │        Port 3000               │
│  • Cache Gateway     │  • Scrape /metrics  │  • Dashboards                  │
│  • Historique vols   │  • 15s interval     │  • Visualisation               │
│  • Rate limit state  │  • 15d retention    │  • Alertes                     │
└──────────────────────┴─────────────────────┴────────────────────────────────┘
```

---

## Stack Technologique

### Backend

| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| **Framework** | FastAPI | 0.100+ | Async native, validation Pydantic, OpenAPI auto |
| **HTTP Client** | httpx | 0.24+ | Async, connection pooling, timeouts |
| **ORM/DB** | Motor (MongoDB async) | 3.3+ | Driver async officiel MongoDB |
| **LLM Framework** | LangGraph + LangChain | 0.2+ | StateGraph, ReAct pattern |
| **LLM** | Mistral AI | latest | Function calling, multi-langue |
| **Validation** | Pydantic | 2.0+ | Settings, modèles typés |

### Frontend

| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| **Framework** | Streamlit | 1.28+ | Rapid prototyping, Python native |
| **Auth** | Supabase + st_login_form | - | Authentification prête à l'emploi |

### Infrastructure

| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| **Database** | MongoDB | 7.0 | Document-based, flexible schema |
| **Container** | Docker Compose | - | Orchestration multi-service |
| **Monitoring** | Prometheus | 2.54 | Métriques, alertes |
| **Visualization** | Grafana | 10.2 | Dashboards, observabilité |

### API Externe

| Service | Usage |
|---------|-------|
| **Aviationstack** | Données aéroports et vols en temps réel |
| **Nominatim (OSM)** | Géocodage d'adresses (gratuit) |

---

## Services et Responsabilités

### 1. Gateway Service (Port 8004)

**Rôle** : Point d'entrée unique vers l'API Aviationstack avec optimisations.

**Responsabilités** :

- **Cache MongoDB** : TTL 300s pour réduire les appels API
- **Rate Limiting** : 10,000 appels/mois avec reset automatique
- **Circuit Breaker** : Protection contre les pannes cascadées
- **Request Coalescing** : Fusion des requêtes identiques simultanées
- **Métriques Prometheus** : Observabilité centralisée

**Endpoints** :

- `GET /airports` - Proxy vers Aviationstack /airports
- `GET /flights` - Proxy vers Aviationstack /flights
- `GET /health` - État du service
- `GET /stats` - Statistiques complètes
- `GET /usage` - Utilisation du quota API

### 2. Airport Service (Port 8001)

**Rôle** : Microservice de recherche et consultation d'aéroports.

**Responsabilités** :

- Recherche par code IATA (CDG, JFK, LHR...)
- Recherche par nom/ville avec code pays
- Géocodage d'adresses via Nominatim
- Calcul de distance Haversine pour aéroport le plus proche
- Liste des départs/arrivées avec enrichissement pays

**Endpoints** :

- `GET /api/v1/airports/{iata}` - Aéroport par IATA
- `GET /api/v1/airports/search` - Recherche par nom
- `GET /api/v1/airports/nearest` - Plus proche d'une adresse
- `GET /api/v1/airports/{iata}/departures` - Vols au départ
- `GET /api/v1/airports/{iata}/arrivals` - Vols à l'arrivée

### 3. Flight Service (Port 8002)

**Rôle** : Microservice de suivi de vols individuels et statistiques.

**Responsabilités** :

- Statut en temps réel d'un vol
- Historique stocké en MongoDB
- Statistiques de ponctualité (retards, durées moyennes)
- **Lazy Loading** : Auto-population de l'historique si vide

**Endpoints** :

- `GET /api/v1/flights/{flight_iata}` - Statut en temps réel
- `GET /api/v1/flights/{flight_iata}/history` - Historique
- `GET /api/v1/flights/{flight_iata}/statistics` - Statistiques agrégées

### 4. Assistant Service (Port 8003)

**Rôle** : IA conversationnelle orchestrant les autres services.

**Responsabilités** :

- Interprétation du langage naturel (FR/EN/ES)
- Extraction d'entités (codes IATA, dates, villes)
- Orchestration via LangGraph StateGraph
- Génération de réponses en langage naturel

**Endpoints** :

- `POST /api/v1/assistant/interpret` - Analyse d'intention
- `POST /api/v1/assistant/answer` - Réponse complète

**Tools LangGraph disponibles** :

1. `get_airport_by_iata_tool` - Recherche aéroport par IATA
2. `search_airports_tool` - Recherche par nom + pays
3. `get_nearest_airport_tool` - Aéroport le plus proche
4. `get_departures_tool` - Vols au départ (avec enrichissement pays)
5. `get_arrivals_tool` - Vols à l'arrivée
6. `get_flight_status_tool` - Statut d'un vol
7. `get_flight_statistics_tool` - Statistiques d'un vol

### 5. Frontend (Port 8501)

**Rôle** : Interface utilisateur Streamlit.

**Responsabilités** :

- Authentification via Supabase
- Chat conversationnel avec l'Assistant
- Navigation visuelle (aéroports, vols)
- Affichage des données structurées

---

## Flux de Données

### Exemple : "Quels vols partent de CDG ?"

```text
1. [Frontend] Utilisateur tape "Quels vols partent de CDG ?"
                    │
                    ▼
2. [Assistant] POST /api/v1/assistant/answer
   │
   ├─ [Analyze Node] Mistral AI détecte intention "departures"
   │                 Extrait entité: iata="CDG"
   │
   ├─ [Plan Node] Sélectionne tool: get_departures_tool
   │
   ├─ [Execute Node] Appelle Airport Service
   │         │
   │         ▼
3. │   [Airport] GET /api/v1/airports/CDG/departures
   │         │
   │         ▼
4. │   [Gateway] GET /flights?dep_iata=CDG
   │         │
   │         ├─ Cache HIT? → Retourne données cachées
   │         └─ Cache MISS:
   │               ├─ Check Rate Limit (OK?)
   │               ├─ Check Circuit Breaker (CLOSED?)
   │               ├─ Request Coalescing (déjà en vol?)
   │               └─ Appel Aviationstack API
   │
   │         ◀─ Réponse avec vols
   │
   ├─ [Generate Node] Mistral AI génère réponse en français
   │
   └─ Retourne {answer: "...", data: {...}}
                    │
                    ▼
5. [Frontend] Affiche la réponse + données JSON
```

---

## Patterns Architecturaux

### 1. Clean Architecture (par service)

```text
┌─────────────────────────────────────────┐
│           Presentation Layer            │  ← routes/, main.py
│         (FastAPI Routers)               │
├─────────────────────────────────────────┤
│           Application Layer             │  ← services/
│      (Business Logic, Orchestration)    │
├─────────────────────────────────────────┤
│             Domain Layer                │  ← models/domain/
│        (Entities, Value Objects)        │
├─────────────────────────────────────────┤
│          Infrastructure Layer           │  ← clients/, repositories/
│     (External APIs, Database Access)    │
└─────────────────────────────────────────┘
```

### 2. Gateway Pattern

Le Gateway centralise **tous** les appels vers Aviationstack :

- Évite la duplication du code d'optimisation
- Point unique de rate limiting
- Cache partagé entre services
- Circuit breaker global

### 3. ReAct Pattern (Assistant)

**Reasoning + Acting** en boucle :

1. **Observe** : Analyse le prompt utilisateur
2. **Think** : Décide de l'action à entreprendre
3. **Act** : Exécute le tool approprié
4. **Observe** : Analyse le résultat
5. **Repeat** ou **Respond** : Itère ou génère la réponse

### 4. Lazy Loading (Flight History)

```python
# Si historique vide en MongoDB, un seul appel API le peuple
if not history_in_db:
    await get_flight_status(flight_iata)  # Peuple ~10 jours
    history_in_db = await query_mongodb()  # Maintenant disponible
```

---

## Structure du Projet

```text
hello-mira-flight-platform/
│
├── .env                          # Variables d'environnement (secrets)
├── .env.example                  # Template des variables
├── docker-compose.yml            # Orchestration des services
├── README.md                     # Documentation principale
├── CLAUDE.md                     # Instructions pour Claude AI
├── PROJECT_STATUS.md             # État du projet
│
├── airport/                      # Microservice Airport
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── config/settings.py        # Configuration Pydantic
│   ├── models/                   # Modèles de données
│   │   └── domain/               # Entités métier
│   ├── routes/                   # Endpoints REST
│   └── services/                 # Logique métier
│
├── flight/                       # Microservice Flight
│   ├── main.py
│   ├── config/settings.py
│   ├── models/
│   │   └── domain/
│   ├── routes/
│   └── services/
│
├── assistant/                    # Microservice Assistant IA
│   ├── main.py
│   ├── config/settings.py
│   ├── clients/                  # Clients HTTP vers autres services
│   ├── graph/                    # LangGraph StateGraph
│   ├── models/
│   │   └── domain/
│   │       ├── state.py          # État du graph
│   │       └── responses.py      # Modèles de réponse
│   ├── routes/
│   └── tools/                    # LangGraph tools
│       ├── airport_tools.py      # 5 tools aéroport
│       └── flight_tools.py       # 2 tools vol
│
├── gateway/                      # API Gateway
│   ├── main.py
│   ├── config.py
│   ├── cache.py                  # Cache MongoDB
│   ├── rate_limiter.py           # Rate limiting mensuel
│   ├── circuit_breaker.py        # Protection pannes
│   ├── request_coalescer.py      # Fusion requêtes
│   └── monitoring/
│       └── metrics.py            # Métriques Prometheus
│
├── frontend/                     # Interface Streamlit
│   ├── app.py                    # Application principale
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .streamlit/
│       ├── config.toml           # Configuration Streamlit
│       └── secrets.toml          # Credentials Supabase
│
├── monitoring/                   # Configuration monitoring
│   ├── prometheus.yml            # Config Prometheus
│   └── grafana/
│       ├── dashboards/           # Dashboards JSON
│       └── provisioning/         # Auto-provisioning
│
├── tests/                        # Tests automatisés
│   ├── conftest.py               # Fixtures globales
│   ├── e2e/                      # Tests end-to-end
│   └── performance/              # Tests de performance
│
├── scripts/                      # Scripts utilitaires
│   └── generate_traffic_intensive.sh
│
└── docs/                         # Documentation technique
    └── services/
        ├── 00_PROJECT_OVERVIEW.md
        ├── 01_AIRPORT_SERVICE.md
        ├── 02_FLIGHT_SERVICE.md
        ├── 03_ASSISTANT_SERVICE.md
        └── 04_INFRASTRUCTURE.md
```

---

## Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Clés API : Aviationstack, Mistral AI
- (Optionnel) Credentials Supabase

### 1. Configuration

```bash
# Copier et éditer le fichier .env
cp .env.example .env

# Variables requises :
# AVIATIONSTACK_API_KEY=xxx
# MISTRAL_API_KEY=xxx
# MONGO_PASSWORD=xxx
```

### 2. Lancement

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Vérifier la santé
curl http://localhost:8004/health  # Gateway
curl http://localhost:8001/api/v1/health  # Airport
curl http://localhost:8002/api/v1/health  # Flight
curl http://localhost:8003/api/v1/health  # Assistant
```

### 3. Accès

- **Frontend** : <http://localhost:8501>
- **Grafana** : <http://localhost:3000> (admin/admin)
- **Prometheus** : <http://localhost:9090>
- **Gateway API** : <http://localhost:8004>
- **Airport API** : <http://localhost:8001/api/v1>
- **Flight API** : <http://localhost:8002/api/v1>
- **Assistant API** : <http://localhost:8003/api/v1>

---

## Ports et Endpoints

| Service | Port | Base URL | Documentation |
|---------|------|----------|---------------|
| **MongoDB** | 27017 | - | - |
| **Gateway** | 8004 | <http://localhost:8004> | /docs |
| **Airport** | 8001 | <http://localhost:8001/api/v1> | /docs |
| **Flight** | 8002 | <http://localhost:8002/api/v1> | /docs |
| **Assistant** | 8003 | <http://localhost:8003/api/v1> | /docs |
| **Frontend** | 8501 | <http://localhost:8501> | - |
| **Prometheus** | 9090 | <http://localhost:9090> | - |
| **Grafana** | 3000 | <http://localhost:3000> | - |

---

## Documents Associés

- [01_AIRPORT_SERVICE.md](01_AIRPORT_SERVICE.md) - Documentation complète Airport
- [02_FLIGHT_SERVICE.md](02_FLIGHT_SERVICE.md) - Documentation complète Flight
- [03_ASSISTANT_SERVICE.md](03_ASSISTANT_SERVICE.md) - Documentation complète Assistant
- [04_INFRASTRUCTURE.md](04_INFRASTRUCTURE.md) - Infrastructure et DevOps
- [05_FRONTEND.md](05_FRONTEND.md) - Documentation Frontend Streamlit
- [06_GATEWAY.md](06_GATEWAY.md) - Documentation Gateway détaillée
- [07_TESTING.md](07_TESTING.md) - Stratégie de tests
- [08_MONITORING.md](08_MONITORING.md) - Monitoring et observabilité
