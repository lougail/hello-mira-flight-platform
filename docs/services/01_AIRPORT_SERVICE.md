# Microservice Airport - Documentation Technique Complète

**Port** : 8001
**Partie du test** : Partie 1
**Statut** : ✅ COMPLET

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture des fichiers](#architecture-des-fichiers)
3. [Endpoints API](#endpoints-api)
4. [Couche Domain (Modèles)](#couche-domain-modèles)
5. [Services métier](#services-métier)
6. [Client Aviationstack](#client-aviationstack)
7. [Service de géocodage](#service-de-géocodage)
8. [Métriques Prometheus](#métriques-prometheus)
9. [Configuration](#configuration)
10. [Patterns et solutions techniques](#patterns-et-solutions-techniques)
11. [Problèmes rencontrés et solutions](#problèmes-rencontrés-et-solutions)

---

## Vue d'ensemble

### Objectif

Le microservice Airport permet d'interroger les aéroports via l'API externe Aviationstack. Il répond aux besoins de la **Partie 1** du test technique.

### Fonctionnalités principales

- ✅ Trouver un aéroport par **code IATA** (CDG, JFK, LHR...)
- ✅ Trouver un aéroport par **proximité GPS** (coordonnées lat/lon)
- ✅ Trouver un aéroport par **adresse** (géocodage automatique)
- ✅ Rechercher des aéroports par **nom de lieu** (ville, région)
- ✅ Lister les **vols au départ** d'un aéroport
- ✅ Lister les **vols à l'arrivée** d'un aéroport

### Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI (async) |
| Client HTTP | httpx (async) |
| Validation | Pydantic v2 |
| Géocodage | Nominatim (OpenStreetMap) |
| Métriques | prometheus-fastapi-instrumentator |
| Configuration | pydantic-settings |

---

## Architecture des fichiers

```text
airport/
├── main.py                          # Point d'entrée FastAPI + lifecycle
├── Dockerfile                       # Image Docker
├── requirements.txt                 # Dépendances Python
│
├── api/                             # Couche présentation (REST)
│   ├── __init__.py
│   ├── responses.py                 # Modèles de réponse API (Pydantic)
│   └── routes/
│       ├── __init__.py              # Router principal qui agrège tous les routers
│       ├── airports.py              # 4 endpoints de recherche d'aéroports
│       ├── flights.py               # 2 endpoints départs/arrivées
│       └── health.py                # Health checks (liveness + readiness)
│
├── clients/                         # Couche d'accès aux APIs externes
│   ├── __init__.py
│   └── aviationstack_client.py      # Client HTTP vers le Gateway
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration centralisée (pydantic-settings)
│
├── models/                          # Couche domain (modèles métier)
│   ├── __init__.py                  # Exports publics
│   ├── enums.py                     # Énumérations (FlightStatus)
│   ├── api/                         # Modèles spécifiques API (pas utilisés ici)
│   │   └── ...
│   └── domain/
│       ├── __init__.py
│       ├── airport.py               # Modèle Airport avec from_api_response()
│       └── flight.py                # Modèle Flight avec from_api_response()
│
├── monitoring/
│   ├── __init__.py
│   └── metrics.py                   # Métriques Prometheus custom
│
├── services/                        # Couche logique métier
│   ├── __init__.py
│   ├── airport_service.py           # Orchestration des recherches d'aéroports
│   └── geocoding_service.py         # Géocodage + calcul de distance Haversine
│
└── tests/                           # Tests (unit, integration, exploration)
    └── ...
```

---

## Endpoints API

### Base URL : `/api/v1`

### 1. GET `/airports/{iata_code}` - Recherche par code IATA

**Fichier** : `api/routes/airports.py:350-407`

**Description** : Récupère les informations complètes d'un aéroport à partir de son code IATA.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| iata_code | path | ✅ | Code IATA 3 lettres (ex: CDG, JFK) |

**Réponse** : `AirportResponse`

```json
{
  "iata_code": "CDG",
  "icao_code": "LFPG",
  "name": "Charles de Gaulle International Airport",
  "city": "PAR",
  "country": "France",
  "country_code": "FR",
  "timezone": "Europe/Paris",
  "coordinates": {
    "latitude": 49.0097,
    "longitude": 2.5479
  }
}
```

**Flux** :

```text
Endpoint → AirportService.get_airport_by_iata() → AviationstackClient → Gateway → Aviationstack API
```

---

### 2. GET `/airports/search` - Recherche par nom de lieu

**Fichier** : `api/routes/airports.py:58-167`

**Description** : Recherche des aéroports par nom de lieu (ville, région, etc.) en utilisant le géocodage.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| name | query | ✅ | Nom du lieu (min 2 caractères) |
| country_code | query | ✅ | Code pays ISO (ex: FR, US) - **Pattern regex : `^[A-Z]{2}$`** |
| limit | query | ❌ | Max résultats (1-50, défaut: 10) |
| offset | query | ❌ | Pagination (défaut: 0) |

**Algorithme** :

1. Géocode le nom du lieu via Nominatim
2. Récupère tous les aéroports du pays via Aviationstack
3. Calcule la distance de chaque aéroport au lieu (formule Haversine)
4. Trie par distance croissante
5. Retourne les N premiers

**Exemple** : `?name=Paris&country_code=FR` → CDG, ORY, BVA (triés par distance)

---

### 3. GET `/airports/nearest-by-coords` - Plus proche par GPS

**Fichier** : `api/routes/airports.py:170-261`

**Description** : Trouve l'aéroport le plus proche à partir de coordonnées GPS.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| latitude | query | ✅ | Latitude (-90 à 90) |
| longitude | query | ✅ | Longitude (-180 à 180) |
| country_code | query | ✅ | Code pays ISO |

**Algorithme** :

1. Valide les coordonnées
2. Récupère les aéroports du pays
3. Calcule la distance avec Haversine
4. Retourne le plus proche

---

### 4. GET `/airports/nearest-by-address` - Plus proche par adresse

**Fichier** : `api/routes/airports.py:264-347`

**Description** : Trouve l'aéroport le plus proche d'une adresse textuelle.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| address | query | ✅ | Adresse (min 3 caractères) |
| country_code | query | ✅ | Code pays ISO |

**Algorithme** :

1. Géocode l'adresse via Nominatim
2. Appelle `find_nearest_airport()` avec les coordonnées

---

### 5. GET `/airports/{iata_code}/departures` - Vols au départ

**Fichier** : `api/routes/flights.py:55-146`

**Description** : Liste les vols au départ d'un aéroport.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| iata_code | path | ✅ | Code IATA (3 lettres, majuscules) |
| limit | query | ❌ | Max vols (1-100, défaut: 10) |
| offset | query | ❌ | Pagination |

**Réponse** : `FlightListResponse`

```json
{
  "flights": [...],
  "total": 25,
  "limit": 10,
  "offset": 0,
  "airport_iata": "CDG"
}
```

---

### 6. GET `/airports/{iata_code}/arrivals` - Vols à l'arrivée

**Fichier** : `api/routes/flights.py:149-240`

**Description** : Liste les vols à l'arrivée d'un aéroport.

**Structure identique à departures.**

---

### 7. GET `/api/v1/health` - Liveness probe

**Fichier** : `api/routes/health.py:68-96`

Retourne toujours 200 OK si le service répond.

### 8. GET `/api/v1/health/ready` - Readiness probe

**Fichier** : `api/routes/health.py:99-155`

Vérifie que toutes les dépendances sont accessibles.

---

## Couche Domain (Modèles)

### Airport (`models/domain/airport.py`)

```python
class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class Airport(BaseModel):
    iata_code: str = Field(..., pattern="^[A-Z]{3}$")
    icao_code: str = Field(..., pattern="^[A-Z]{4}$")
    name: str
    city: str
    country: str
    country_code: str = Field(..., pattern="^[A-Z]{2}$")
    coordinates: Coordinates
    timezone: str
```

**Point clé - Validator `uppercase_codes`** :

```python
@field_validator('iata_code', 'icao_code', 'country_code', mode='before')
@classmethod
def uppercase_codes(cls, v: str) -> str:
    """Force les codes en majuscules AVANT validation du pattern."""
    if isinstance(v, str):
        return v.upper()
    return v
```

Ce validator s'exécute **AVANT** la validation du pattern regex, permettant d'accepter `cdg` et le convertir en `CDG`.

---

### Flight (`models/domain/flight.py`)

```python
class FlightSchedule(BaseModel):
    scheduled: Optional[datetime] = None
    estimated: Optional[datetime] = None
    actual: Optional[datetime] = None
    delay_minutes: Optional[int] = None

class Flight(BaseModel):
    flight_number: str
    flight_iata: str
    flight_date: str  # Format YYYY-MM-DD
    status: FlightStatus
    departure_airport: str
    departure_iata: str
    arrival_airport: str
    arrival_iata: str
    departure_schedule: FlightSchedule
    arrival_schedule: FlightSchedule
    airline_name: str
    airline_iata: Optional[str] = None
```

### FlightStatus (`models/enums.py`)

```python
class FlightStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    LANDED = "landed"
    CANCELLED = "cancelled"
    INCIDENT = "incident"
    DIVERTED = "diverted"

    @classmethod
    def _missing_(cls, value):
        """Gère les valeurs inconnues de l'API."""
        return value  # Retourne la valeur telle quelle
```

**Pourquoi `_missing_`** : L'API Aviationstack peut retourner des statuts inconnus. Plutôt que de crasher, on les accepte.

---

## Services métier

### AirportService (`services/airport_service.py`)

**Responsabilités** :

- Orchestrer les appels au client Aviationstack
- Calculer les distances pour trouver l'aéroport le plus proche
- Collecter les métriques Prometheus

**Méthodes principales** :

#### `get_airport_by_iata(iata_code: str) -> Optional[Airport]`

Simple wrapper avec métriques.

#### `find_nearest_airport(latitude, longitude, country_code, limit=100) -> Optional[Airport]`

```python
# Algorithme :
1. Valide les coordonnées
2. Récupère les aéroports du pays (limit=100)
3. Pour chaque aéroport:
   - Calcule la distance avec Haversine
   - Stocke (airport, distance)
4. Trie par distance croissante
5. Retourne le premier
```

#### `find_nearest_airport_by_address(address, country_code) -> Optional[Airport]`

```python
# Algorithme :
1. Géocode l'adresse → (lat, lon)
2. Appelle find_nearest_airport()
```

#### `search_airports_by_location(location_name, country_code, limit=10) -> List[Airport]`

```python
# Algorithme :
1. Géocode "{location_name} airport, {country_code}"
2. Si échec: géocode "{location_name}, {country_code}"
3. Récupère les aéroports du pays
4. Calcule les distances
5. Trie et retourne les N premiers
```

---

## Client Aviationstack

**Fichier** : `clients/aviationstack_client.py`

### Architecture

```text
AviationstackClient
        │
        ▼ (HTTP)
    Gateway (port 8004)
        │
        ▼ (Cache + Rate limiting + Circuit breaker + Coalescing)
    Aviationstack API
```

**Point important** : Le client ne contacte PAS directement Aviationstack. Il passe par un Gateway interne qui centralise toute la logique d'optimisation.

### Retry avec backoff exponentiel

```python
async def _make_request(self, endpoint, params, retry_count=3):
    for attempt in range(retry_count):
        try:
            response = await self.client.get(url, params=params)
            # ... gestion succès
        except httpx.HTTPStatusError as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
```

### Gestion des erreurs spéciales

```python
if response.status_code == 429:
    raise AviationstackError("Quota API mensuel atteint")

if response.status_code == 503:
    # Circuit breaker ouvert
    raise AviationstackError("Service temporairement indisponible")
```

### Pool de connexions

```python
self.client = httpx.AsyncClient(
    timeout=httpx.Timeout(self.timeout),
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    )
)
```

---

## Service de géocodage

**Fichier** : `services/geocoding_service.py`

### Nominatim (OpenStreetMap)

- **Gratuit** et sans clé API
- **Limite** : 1 requête/seconde (politique d'usage équitable)
- **User-Agent obligatoire** pour identifier l'application

### Formule de Haversine

```python
@staticmethod
def calculate_distance(lat1, lon1, lat2, lon2) -> float:
    """Calcule la distance orthodromique entre deux points GPS."""
    R = 6371.0  # Rayon de la Terre en km

    # Conversion en radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Formule de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # Distance en km
```

**Pourquoi Haversine ?** : La Terre est une sphère. Calculer une distance en ligne droite (Pythagore) donnerait des résultats faux, surtout sur de grandes distances.

---

## Métriques Prometheus

**Fichier** : `monitoring/metrics.py`

### Métriques définies

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `airport_lookups_total` | Counter | type, status | Recherches d'aéroports |
| `airport_lookup_latency_seconds` | Histogram | type | Latence des recherches |
| `airport_airports_found` | Histogram | type | Nombre de résultats |
| `airport_geocoding_calls_total` | Counter | status | Appels Nominatim |
| `airport_geocoding_latency_seconds` | Histogram | - | Latence géocodage |
| `airport_flight_queries_total` | Counter | type, status | Requêtes vols |
| `airport_flight_query_latency_seconds` | Histogram | type | Latence vols |
| `airport_flights_returned` | Histogram | type | Nombre de vols |
| `airport_distance_calculations_total` | Counter | - | Calculs Haversine |
| `airport_last_nearest_distance_km` | Gauge | - | Dernière distance calculée |

### Instrumentation automatique FastAPI

```python
from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/docs", "/redoc"]
)

instrumentator.add(
    metrics.latency(
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )
)
```

---

## Configuration

**Fichier** : `config/settings.py`

### Variables d'environnement

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `GATEWAY_URL` | str | `http://gateway:8004` | URL du Gateway |
| `AVIATIONSTACK_TIMEOUT` | int | 30 | Timeout API (secondes) |
| `MONGODB_URL` | str | `mongodb://localhost:27017` | URL MongoDB |
| `MONGODB_DATABASE` | str | `hello_mira` | Nom de la base |
| `DEBUG` | bool | False | Mode debug |
| `CORS_ORIGINS` | list | `["http://localhost:3000"]` | CORS autorisés |

### Chargement depuis .env

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
```

---

## Patterns et solutions techniques

### 1. Dependency Injection FastAPI

**Fichier** : `main.py:208-228`

```python
# Routes déclarent une dépendance abstraite
async def get_airport_service() -> AirportService:
    raise HTTPException(503, "Service not configured")

# main.py configure l'implémentation concrète
app.dependency_overrides[get_airport_service] = get_airport_service_override
```

**Avantage** : Les routes ne dépendent pas de l'implémentation concrète du service. Facilite les tests avec des mocks.

### 2. Lifecycle avec asynccontextmanager

**Fichier** : `main.py:58-125`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    aviationstack_client = AviationstackClient()
    geocoding_service = GeocodingService()
    airport_service = AirportService(aviationstack_client, geocoding_service)

    yield  # Application tourne ici

    # SHUTDOWN
    await aviationstack_client.close()
```

**Avantage** : Gestion propre des ressources (connections HTTP, etc.)

### 3. Ordre des routes FastAPI

**Fichier** : `api/routes/airports.py:55-57` (commentaire important)

```python
# IMPORTANT: Les routes spécifiques (/search, /nearest) DOIVENT être déclarées
# AVANT les routes avec path parameters (/{iata_code}) pour éviter les conflits
```

Si `/{iata_code}` était déclaré en premier, une requête vers `/search` serait capturée avec `iata_code="search"`.

### 4. Pattern `from_domain` / `from_api_response`

**Séparation des responsabilités** :ù

- `from_api_response()` : Crée un modèle domain depuis la réponse API brute
- `from_domain()` : Crée une réponse API depuis un modèle domain

```text
API Aviationstack → from_api_response() → Domain Model → from_domain() → API Response
```

---

## Problèmes rencontrés et solutions

### 1. Validation regex avec majuscules

**Problème** : Les codes IATA doivent être en majuscules (`^[A-Z]{3}$`), mais l'utilisateur peut envoyer `cdg`.

**Solution** : Validator Pydantic `mode='before'` qui convertit en majuscules AVANT la validation du pattern.

```python
@field_validator('iata_code', mode='before')
def uppercase_codes(cls, v):
    return v.upper() if isinstance(v, str) else v
```

### 2. Géocodage fallback

**Problème** : La recherche `{ville} airport, FR` peut échouer si le lieu n'est pas un aéroport connu.

**Solution** : Fallback sans "airport" si premier essai échoue.

```python
coords = await self.geocoding.geocode_address(f"{location_name} airport, {country_code}")
if not coords:
    coords = await self.geocoding.geocode_address(f"{location_name}, {country_code}")
```

### 3. Statuts de vol inconnus

**Problème** : L'API Aviationstack peut retourner des statuts non documentés.

**Solution** : Méthode `_missing_` dans l'enum qui accepte toute valeur.

```python
@classmethod
def _missing_(cls, value):
    return value
```

### 4. Coordonnées invalides

**Problème** : Des coordonnées hors limites (-90/90 pour lat, -180/180 pour lon) causent des erreurs.

**Solution** : Validation explicite avant calcul.

```python
def validate_coordinates(self, latitude, longitude) -> bool:
    if latitude < -90 or latitude > 90:
        return False
    if longitude < -180 or longitude > 180:
        return False
    return True
```

### 5. Pool de connexions HTTP

**Problème** : Créer un nouveau client HTTP pour chaque requête est coûteux.

**Solution** : Client httpx réutilisable avec pool de connexions.

```python
self.client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    )
)
```

---

## Conclusion

Le microservice Airport implémente une architecture **Clean Architecture** simplifiée :

```text
┌─────────────────────────────────────────┐
│            API Routes (FastAPI)         │  ← Couche Présentation
├─────────────────────────────────────────┤
│            Services (métier)            │  ← Couche Application
├─────────────────────────────────────────┤
│         Domain Models (Pydantic)        │  ← Couche Domain
├─────────────────────────────────────────┤
│     Clients (HTTP, Geocoding)           │  ← Couche Infrastructure
└─────────────────────────────────────────┘
```

**Points forts** :

- Séparation claire des responsabilités
- Async/await partout pour la performance
- Métriques Prometheus intégrées
- Configuration centralisée et validée
- Gestion d'erreurs robuste avec retry
