# Hello Mira Flight Platform

Plateforme de microservices pour la recherche d'aéroports et le suivi de vols en temps réel.

## Architecture

Le système est composé de microservices indépendants :

- **Airport** (port 8001) : Recherche d'aéroports et consultation des vols au départ/arrivée
- **Flight** (port 8002) : Suivi individuel de vols avec historique et statistiques
- **Assistant** (à venir) : Interface en langage naturel

## Prérequis

- Docker et Docker Compose
- Clé API Aviationstack (gratuite sur [aviationstack.com](https://aviationstack.com))

## Installation

1. Cloner le repository

```bash
git clone https://github.com/lougail/hello-mira-flight-platform.git
cd hello-mira-flight-platform
```

2. Créer le fichier `.env` à la racine

```env
AVIATIONSTACK_API_KEY=votre_cle_api
MONGO_PASSWORD=un_mot_de_passe_securise
```

3. Lancer l'application

```bash
docker-compose up
```

Les APIs seront disponibles sur :
- **Airport** : `http://localhost:8001`
- **Flight** : `http://localhost:8002`

## Utilisation

### Documentation interactive

Une fois l'application lancée, la documentation Swagger est accessible sur :

**Microservice Airport :**
- Swagger UI : http://localhost:8001/docs
- ReDoc : http://localhost:8001/redoc

**Microservice Flight :**
- Swagger UI : http://localhost:8002/docs
- ReDoc : http://localhost:8002/redoc

### Endpoints disponibles

#### Recherche d'aéroports

```bash
# Par code IATA
GET /api/v1/airports/{iata}

# Par nom ou ville
GET /api/v1/airports/search?name={query}

# Par coordonnées GPS
GET /api/v1/airports/nearest?lat={latitude}&lon={longitude}&radius={km}

# Par adresse (avec géocodage automatique)
GET /api/v1/airports/nearest?address={adresse}&radius={km}
```

#### Vols au départ/arrivée d'un aéroport (Airport API)

```bash
# Vols au départ
GET /api/v1/airports/{iata}/departures?limit=10&offset=0

# Vols à l'arrivée
GET /api/v1/airports/{iata}/arrivals?limit=10&offset=0
```

#### Suivi individuel de vols (Flight API)

```bash
# Statut en temps réel d'un vol
GET /api/v1/flights/{flight_iata}

# Historique d'un vol sur une période
GET /api/v1/flights/{flight_iata}/history?start_date=2025-11-21&end_date=2025-11-22

# Statistiques agrégées (ponctualité, retards)
GET /api/v1/flights/{flight_iata}/statistics?start_date=2025-11-21&end_date=2025-11-22
```

### Exemples

Le fichier `requests.http` à la racine contient des exemples prêts à l'emploi. Utilisable avec l'extension VSCode REST Client ou avec curl.

```bash
# Microservice Airport
# Recherche de l'aéroport CDG
curl http://localhost:8001/api/v1/airports/CDG

# Vols au départ de CDG
curl http://localhost:8001/api/v1/airports/CDG/departures?limit=10

# Aéroport le plus proche de Paris
curl "http://localhost:8001/api/v1/airports/nearest?lat=48.8566&lon=2.3522&radius=50"

# Microservice Flight
# Statut du vol AF282
curl http://localhost:8002/api/v1/flights/AF282

# Historique du vol AF282
curl "http://localhost:8002/api/v1/flights/AF282/history?start_date=2025-11-21&end_date=2025-11-22"

# Statistiques du vol AF282
curl "http://localhost:8002/api/v1/flights/AF282/statistics?start_date=2025-11-21&end_date=2025-11-22"
```

## Développement

### Structure du projet

```
hello-mira-flight-platform/
├── airport/                 # Microservice Airport
│   ├── api/                # Routes FastAPI
│   │   └── routes/
│   ├── clients/            # Client API Aviationstack
│   ├── config/             # Configuration et settings
│   ├── models/             # Modèles Pydantic
│   │   ├── api/           # Modèles de réponse API
│   │   └── domain/        # Modèles métier
│   ├── services/           # Logique métier
│   ├── tests/             # Tests unitaires
│   ├── Dockerfile
│   ├── main.py            # Point d'entrée
│   └── requirements.txt
├── flight/                  # Microservice Flight
│   ├── api/                # Routes FastAPI
│   │   └── routes/
│   ├── clients/            # Client API Aviationstack
│   ├── config/             # Configuration et settings
│   ├── models/             # Modèles Pydantic
│   │   ├── api/           # Modèles de réponse API
│   │   └── domain/        # Modèles métier
│   ├── services/           # Logique métier
│   ├── Dockerfile
│   ├── main.py            # Point d'entrée
│   └── requirements.txt
├── docker-compose.yml
├── requests.http          # Collection de requêtes de test
└── README.md
```

### Lancement en mode développement

**Microservice Airport :**
```bash
cd airport
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**Microservice Flight :**
```bash
cd flight
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

MongoDB doit être accessible sur `mongodb://localhost:27017` ou modifier `MONGODB_URL` dans `.env`.

### Tests

```bash
cd airport
pytest
```

## Stack technique

- **Framework** : FastAPI 0.121.2
- **Base de données** : MongoDB 7.0 (cache avec TTL)
- **Client HTTP** : httpx (async)
- **Validation** : Pydantic 2.12.4
- **API externe** : Aviationstack
- **Géocodage** : Nominatim (OpenStreetMap)

## Cache et optimisations

Le système implémente plusieurs optimisations :

- Cache MongoDB avec TTL configurable (300s par défaut)
- Rate limiting intelligent sur l'API externe
- Retry automatique avec exponential backoff
- Géocodage d'adresses en coordonnées GPS

## Configuration

Variables d'environnement disponibles (fichier `.env`) :

```env
# API externe (obligatoire)
AVIATIONSTACK_API_KEY=xxx

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=hello_mira
MONGO_PASSWORD=xxx

# Cache
CACHE_TTL=300

# Application
DEBUG=false
```

## Limites connues

- L'API Aviationstack gratuite limite à 100 requêtes/mois
- Le géocodage Nominatim demande 1 seconde entre chaque requête (rate limiting)
- Le plan gratuit d'Aviationstack ne donne pas accès aux données historiques

## Licence

Projet réalisé dans le cadre du test technique Hello Mira.

## Contact

Louis - [GitHub](https://github.com/lougail)
