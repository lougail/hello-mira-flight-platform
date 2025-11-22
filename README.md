# Hello Mira Flight Platform

Plateforme de microservices pour la recherche d'aéroports et le suivi de vols en temps réel.

## Architecture

Le système est composé de microservices indépendants :

- **Airport** (port 8001) : Recherche d'aéroports et consultation des vols au départ/arrivée
- **Flight** (port 8002) : Suivi individuel de vols avec historique et statistiques
- **Assistant** : Interface en langage naturel (en développement)

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
- Airport : `http://localhost:8001`
- Flight : `http://localhost:8002`

## Utilisation

### Documentation interactive

Une fois l'application lancée, la documentation Swagger est accessible sur :

**Airport :**
- Swagger UI : http://localhost:8001/docs
- ReDoc : http://localhost:8001/redoc

**Flight :**
- Swagger UI : http://localhost:8002/docs
- ReDoc : http://localhost:8002/redoc

### Endpoints disponibles

#### Microservice Airport (port 8001)

**Recherche d'aéroports**

```bash
# Par code IATA
GET /api/v1/airports/{iata}
# Exemple : GET /api/v1/airports/CDG

# Par nom de lieu (ville, région)
GET /api/v1/airports/search?name={query}&country_code={code}
# Exemple : GET /api/v1/airports/search?name=Paris&country_code=FR

# Par coordonnées GPS
GET /api/v1/airports/nearest-by-coords?latitude={lat}&longitude={lon}&country_code={code}
# Exemple : GET /api/v1/airports/nearest-by-coords?latitude=48.8566&longitude=2.3522&country_code=FR

# Par adresse (avec géocodage automatique)
GET /api/v1/airports/nearest-by-address?address={address}&country_code={code}
# Exemple : GET /api/v1/airports/nearest-by-address?address=Lille,France&country_code=FR
```

**Vols au départ et à l'arrivée**

```bash
# Vols au départ d'un aéroport
GET /api/v1/airports/{iata}/departures?limit=10&offset=0
# Exemple : GET /api/v1/airports/CDG/departures?limit=20

# Vols à l'arrivée d'un aéroport
GET /api/v1/airports/{iata}/arrivals?limit=10&offset=0
# Exemple : GET /api/v1/airports/CDG/arrivals?limit=20
```

#### Suivi de vols (Flight)

```bash
# Statut en temps réel d'un vol
GET /api/v1/flights/{flight_iata}

# Historique d'un vol sur une période
GET /api/v1/flights/{flight_iata}/history?start_date=2025-11-01&end_date=2025-11-14

# Statistiques agrégées d'un vol
GET /api/v1/flights/{flight_iata}/statistics?start_date=2025-11-01&end_date=2025-11-14
```

### Exemples

Le fichier `requests.http` à la racine contient des exemples prêts à l'emploi. Utilisable avec l'extension VSCode REST Client ou avec curl.

**Exemples Airport :**
```bash
# Recherche de l'aéroport CDG par code IATA
curl http://localhost:8001/api/v1/airports/CDG

# Recherche d'aéroports par nom de lieu
curl "http://localhost:8001/api/v1/airports/search?name=Paris&country_code=FR"

# Aéroport le plus proche de coordonnées GPS
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=48.8566&longitude=2.3522&country_code=FR"

# Aéroport le plus proche d'une adresse
curl "http://localhost:8001/api/v1/airports/nearest-by-address?address=Lille,France&country_code=FR"

# Vols au départ de CDG
curl "http://localhost:8001/api/v1/airports/CDG/departures?limit=10"

# Vols à l'arrivée à CDG
curl "http://localhost:8001/api/v1/airports/CDG/arrivals?limit=10"
```

**Exemples Flight :**
```bash
# Statut en temps réel du vol AF447
curl http://localhost:8002/api/v1/flights/AF447

# Historique sur 7 jours
curl "http://localhost:8002/api/v1/flights/AF447/history?start_date=2025-11-01&end_date=2025-11-07"

# Statistiques sur 30 jours
curl "http://localhost:8002/api/v1/flights/AF447/statistics?start_date=2025-10-15&end_date=2025-11-14"
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
│   ├── clients/            # Client API Aviationstack (partagé)
│   ├── config/             # Configuration et settings
│   ├── models/             # Modèles Pydantic
│   │   └── domain/        # Modèles métier (partagés avec Airport)
│   ├── services/           # Logique métier (FlightService)
│   ├── tests/             # Tests unitaires
│   ├── Dockerfile
│   ├── main.py            # Point d'entrée
│   └── requirements.txt
├── docker-compose.yml
├── requests.http          # Collection de requêtes de test
└── README.md
```

### Lancement en mode développement

**Airport (port 8001) :**
```bash
cd airport
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**Flight (port 8002) :**
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
# Tests Airport
cd airport
pytest

# Tests Flight
cd flight
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

## Intégration avec l'assistant conversationnel (Partie 4)

Le microservice Airport est conçu pour être facilement consommé par l'assistant IA. Exemples de mapping prompts → endpoints :

| Prompt utilisateur | Endpoint à appeler | Traitement assistant |
|-------------------|-------------------|---------------------|
| "Trouve-moi l'aéroport le plus proche de Lille" | `GET /airports/nearest-by-address?address=Lille,France&country_code=FR` | Extraction : lieu + pays |
| "Quels vols partent de CDG cet après-midi ?" | `GET /airports/CDG/departures?limit=100` | Extraction : code IATA<br>Filtrage : horaires 14h-18h |
| "Aéroports près de 48.8566, 2.3522" | `GET /airports/nearest-by-coords?latitude=48.8566&longitude=2.3522&country_code=FR` | Extraction : coords + pays |
| "Cherche aéroports à Paris" | `GET /airports/search?name=Paris&country_code=FR` | Extraction : lieu + pays |

**Points forts pour l'IA :**
- ✅ Endpoints explicites et prévisibles
- ✅ Réponses structurées (JSON Pydantic)
- ✅ Tous les horaires en ISO 8601
- ✅ country_code systématique (réduit les ambiguïtés)
- ✅ Pagination pour grandes listes

## Choix architecturaux

### Recherche d'aéroports par nom (OpenStreetMap)

Le plan Basic d'Aviationstack ne supporte pas le paramètre `search` (retourne 403 Forbidden). Pour contourner cette limitation :

1. **Géocodage du nom de lieu** via Nominatim (OpenStreetMap)
   - Exemple : "Paris" → coordonnées GPS (48.8566, 2.3522)
2. **Récupération des aéroports** du pays via Aviationstack
3. **Calcul de distance** avec formule de Haversine
4. **Tri par proximité** au lieu géocodé

**Avantages :**
- ✅ Fonctionne avec villes, régions, quartiers
- ✅ Tolérant aux variations de noms
- ✅ Résultats triés par pertinence géographique

### Séparation des endpoints `/nearest`

Deux endpoints distincts au lieu d'un seul avec paramètres mutuellement exclusifs :
- `/airports/nearest-by-coords` : Pour coordonnées GPS précises
- `/airports/nearest-by-address` : Pour adresses textuelles (géocodage inclus)

**Avantages :**
- ✅ API plus explicite et RESTful
- ✅ Documentation plus claire
- ✅ Validation de paramètres simplifiée

### Cache MongoDB avec TTL

Réduction des appels à l'API externe (limite de 100 req/mois sur plan gratuit) :
- TTL par défaut : 300s (5 minutes)
- Collections séparées : `airport_cache`, `flight_cache`
- Logs de hit-rate pour monitoring

## Limites connues

- **API Aviationstack gratuite** : 100 requêtes/mois maximum
- **Géocodage Nominatim** : 1 seconde entre chaque requête (rate limiting)
- **Plan Basic Aviationstack** :
  - Pas de paramètre `search` pour les aéroports
  - Pas de `flight_date` seul pour l'historique
  - Pas de combinaison `flight_iata` + `flight_date`
- **country_code requis** : Pour éviter les ambiguïtés géographiques

## Licence

Projet réalisé dans le cadre du test technique Hello Mira.

## Contact

Louis - [GitHub](https://github.com/lougail)
