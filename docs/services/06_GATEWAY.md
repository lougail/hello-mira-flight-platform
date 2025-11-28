# 🚪 API Gateway - Documentation Technique

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Composants](#composants)
4. [Cache MongoDB](#1-cache-mongodb)
5. [Rate Limiter](#2-rate-limiter)
6. [Circuit Breaker](#3-circuit-breaker)
7. [Request Coalescing](#4-request-coalescing)
8. [Endpoints API](#endpoints-api)
9. [Métriques Prometheus](#métriques-prometheus)
10. [Configuration](#configuration)

---

## Vue d'Ensemble

Le **Gateway** est le point d'entrée unique vers l'API Aviationstack. Il centralise toutes les optimisations nécessaires pour :

- ⚡ **Réduire la latence** (cache MongoDB)
- 💰 **Économiser le quota API** (rate limiting + coalescing)
- 🛡️ **Protéger contre les pannes** (circuit breaker)
- 📊 **Observer le système** (métriques Prometheus)

### Caractéristiques

| Aspect | Valeur |
|--------|--------|
| **Port** | 8004 |
| **Framework** | FastAPI |
| **Cache TTL** | 300 secondes (5 min) |
| **Rate Limit** | 10,000 appels/mois |
| **Circuit Breaker** | 5 échecs → ouverture |

---

## Architecture

### Diagramme de Flux

```text
                     ┌────────────────────────────────────────────────────────┐
  Requête entrante   │                    GATEWAY                             │
        │            │                                                        │
        ▼            │  ┌─────────────────────────────────────────────────┐   │
   ┌─────────┐       │  │              call_aviationstack()               │   │
   │ Airport │──────▶│  │                                                 │   │
   │ Service │       │  │  1. Check Cache ─────────────────────┐          │   │
   └─────────┘       │  │     │                                │          │   │
                     │  │     │ MISS                           │ HIT      │   │
   ┌─────────┐       │  │     ▼                                │          │   │
   │ Flight  │──────▶│  │  2. Check Circuit Breaker            │          │   │
   │ Service │       │  │     │                                │          │   │
   └─────────┘       │  │     │ CLOSED                         │          │   │
                     │  │     ▼                                │          │   │
                     │  │  3. Request Coalescer                │          │   │
                     │  │     │                                │          │   │
                     │  │     │ (dedupe concurrent)            │          │   │
                     │  │     ▼                                │          │   │
                     │  │  4. _do_api_call()                   │          │   │
                     │  │     │                                │          │   │
                     │  │     ├─ Check Rate Limit              │          │   │
                     │  │     │                                │          │   │
                     │  │     ├─ HTTP GET Aviationstack        │          │   │
                     │  │     │                                │          │   │
                     │  │     ├─ Record Success/Failure        │          │   │
                     │  │     │  (Circuit Breaker)             │          │   │
                     │  │     │                                │          │   │
                     │  │     └─ Set Cache                     │          │   │
                     │  │                                      │          │   │
                     │  │     ◀────────────────────────────────┘          │  │
                     │  │     │                                           │   │
                     │  │     ▼                                           │   │
                     │  │   Return Response                               │   │
                     │  └────────────────────────────────────────────────-┘   │
                     │                                                        │
                     └──────────────────────────────────────────────────────--┘
```

### Structure des Fichiers

```text
gateway/
├── __init__.py
├── main.py               # Point d'entrée FastAPI (360 lignes)
├── config.py             # Configuration Pydantic
├── Dockerfile
├── requirements.txt
│
├── cache.py              # Cache MongoDB (71 lignes)
├── rate_limiter.py       # Rate limiting (120 lignes)
├── circuit_breaker.py    # Circuit breaker (163 lignes)
├── request_coalescer.py  # Coalescing (113 lignes)
│
└── monitoring/
    ├── __init__.py
    └── metrics.py        # Métriques Prometheus
```

---

## Composants

### 1. Cache MongoDB

**Fichier** : `gateway/cache.py`

#### Classe `CacheService`

```python
class CacheService:
    """Cache avec TTL via MongoDB."""

    def __init__(self, collection=None, ttl: int = 300):
        self.collection = collection
        self.ttl = ttl
        self._hits = 0
        self._misses = 0
```

#### Méthodes Cache

| Méthode | Description |
|---------|-------------|
| `get(key)` | Récupère une valeur (vérifie expiration) |
| `set(key, data)` | Stocke avec TTL (upsert) |
| `get_stats()` | Retourne hits, misses, hit_rate |

#### Document MongoDB Cache

```json
{
  "_id": "airports:iata_code=CDG",
  "data": { /* données API */ },
  "expires_at": "2025-11-28T15:05:00Z",
  "created_at": "2025-11-28T15:00:00Z"
}
```

#### Index TTL

```python
# Création automatique au startup
await cache_col.create_index("expires_at", expireAfterSeconds=0)
```

MongoDB supprime automatiquement les documents dont `expires_at < now`.

---

### 2. Rate Limiter

**Fichier** : `gateway/rate_limiter.py`

#### Classe `RateLimiter`

```python
class RateLimiter:
    """
    Rate limiter partagé via MongoDB.
    - 10000 appels/mois (Basic Plan Aviationstack)
    - Reset automatique le 1er du mois
    """

    def __init__(self, collection=None, max_calls: int = 10000):
        self.collection = collection
        self.max_calls = max_calls
```

#### Méthodes Rate Limiter

| Méthode | Description |
|---------|-------------|
| `check_and_increment()` | Vérifie quota, incrémente si OK |
| `get_usage()` | Retourne used, remaining, percentage |
| `_get_month_key()` | Retourne "2025-11" pour novembre |
| `_get_next_reset()` | Date du 1er du mois suivant |

#### Document MongoDB Rate Limiter

```json
{
  "_id": "aviationstack_api_calls",
  "month": "2025-11",
  "count": 1234,
  "max_calls": 10000,
  "updated_at": "2025-11-28T14:30:00Z"
}
```

#### Exception

```python
class RateLimitExceeded(Exception):
    """Levée quand la limite mensuelle est atteinte."""
    pass
```

---

### 3. Circuit Breaker

**Fichier** : `gateway/circuit_breaker.py`

#### États du Circuit

```text
    CLOSED ◀───────────────────┐
       │                       │
       │ N échecs             succès en HALF_OPEN
       ▼                       │
     OPEN ─────────────────▶ HALF_OPEN
           après recovery_timeout
```

| État | Description | Comportement |
|------|-------------|--------------|
| **CLOSED** | Normal | Requêtes passent, compteur échecs |
| **OPEN** | Bloqué | Requêtes rejetées immédiatement |
| **HALF_OPEN** | Test | N requêtes autorisées pour tester |

#### Configuration Circuit Breaker

```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Échecs avant ouverture
    recovery_timeout=30,      # Secondes avant HALF_OPEN
    half_open_max_calls=3     # Requêtes test en HALF_OPEN
)
```

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `can_execute()` | True si requête autorisée |
| `record_success()` | Enregistre un succès |
| `record_failure()` | Enregistre un échec |
| `get_reset_time()` | Quand passer en HALF_OPEN |
| `get_stats()` | État et compteurs |

#### Transitions

```python
async def record_failure(self):
    """Enregistre un échec."""
    self._failure_count += 1

    if self._state == CircuitState.HALF_OPEN:
        # Un échec rouvre le circuit
        self._state = CircuitState.OPEN

    elif self._state == CircuitState.CLOSED:
        if self._failure_count >= self.failure_threshold:
            # 5 échecs → ouverture
            self._state = CircuitState.OPEN
```

---

### 4. Request Coalescing

**Fichier** : `gateway/request_coalescer.py`

#### Principe

Fusionne les requêtes **identiques** et **simultanées** en une seule :

```text
Temps │
      │  ┌─────────────────────────────────────┐
   T0 │  │ Request A: GET /airports?iata=CDG   │────┐
      │  └─────────────────────────────────────┘    │
      │  ┌─────────────────────────────────────┐    │  UN SEUL
   T1 │  │ Request B: GET /airports?iata=CDG   │────┤  APPEL API
      │  └─────────────────────────────────────┘    │
      │  ┌─────────────────────────────────────┐    │
   T2 │  │ Request C: GET /airports?iata=CDG   │────┘
      │  └─────────────────────────────────────┘
      │
      │  ◀─────── Toutes reçoivent la même réponse ───────▶
```

#### Classe `RequestCoalescer`

```python
class RequestCoalescer:
    def __init__(self):
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._total_requests = 0
        self._coalesced_requests = 0
```

#### Méthode `execute()`

```python
async def execute(self, key: str, func: Callable, *args, **kwargs) -> T:
    """
    Execute une fonction avec coalescing.

    Args:
        key: Clé unique (ex: "airports:iata_code=CDG")
        func: Fonction async à exécuter
    """
    async with self._lock:
        if key in self._in_flight:
            # Requête identique en cours → attendre
            self._coalesced_requests += 1
            task = self._in_flight[key]

    if key in self._in_flight:
        return await self._in_flight[key]

    # Nouvelle requête
    async with self._lock:
        task = asyncio.create_task(func(*args, **kwargs))
        self._in_flight[key] = task

    try:
        return await task
    finally:
        async with self._lock:
            self._in_flight.pop(key, None)
```

#### Statistiques

```json
{
  "total_requests": 150,
  "coalesced_requests": 45,
  "actual_api_calls": 105,
  "savings_rate": "30.0%",
  "in_flight": 0
}
```

---

## Endpoints API

### Endpoints Principaux

#### `GET /airports`

Proxy vers Aviationstack `/airports`.

**Paramètres** :

- `iata_code` (optional) : Code IATA
- `search` (optional) : Terme de recherche
- `country_iso2` (optional) : Code pays
- `limit` (default: 100, max: 100)

**Exemple** :

```bash
curl "http://localhost:8004/airports?iata_code=CDG"
```

#### `GET /flights`

Proxy vers Aviationstack `/flights`.

**Paramètres** :

- `flight_iata` (optional) : Code vol
- `dep_iata` (optional) : Aéroport départ
- `arr_iata` (optional) : Aéroport arrivée
- `airline_iata` (optional) : Compagnie
- `flight_status` (optional) : Statut
- `flight_date` (optional) : Date YYYY-MM-DD
- `limit` (default: 100, max: 100)

**Exemple** :

```bash
curl "http://localhost:8004/flights?flight_iata=AF447"
```

### Endpoints de Monitoring

#### `GET /health`

Retourne l'état de santé.

```json
{
  "status": "healthy",
  "rate_limit": {
    "month": "2025-11",
    "used": 1234,
    "limit": 10000,
    "remaining": 8766
  },
  "cache": "enabled",
  "circuit_breaker": "closed"
}
```

#### `GET /stats`

Statistiques complètes de tous les composants.

```json
{
  "rate_limit": {
    "month": "2025-11",
    "used": 1234,
    "limit": 10000,
    "remaining": 8766,
    "percentage": 12.3
  },
  "circuit_breaker": {
    "state": "closed",
    "failure_count": 0,
    "success_count": 15,
    "failure_threshold": 5,
    "recovery_timeout": 30,
    "reset_at": null
  },
  "request_coalescer": {
    "total_requests": 150,
    "coalesced_requests": 45,
    "actual_api_calls": 105,
    "savings_rate": "30.0%",
    "in_flight": 0
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 300,
    "hits": 89,
    "misses": 61,
    "total_requests": 150,
    "hit_rate": "59.3%"
  }
}
```

#### `GET /usage`

Utilisation du quota API uniquement.

```json
{
  "month": "2025-11",
  "used": 1234,
  "limit": 10000,
  "remaining": 8766,
  "reset_date": "2025-12-01T00:00:00",
  "percentage": 12.3
}
```

---

## Métriques Prometheus

### Fichier `monitoring/metrics.py`

```python
from prometheus_client import Counter, Gauge

# Cache metrics
cache_hits = Counter('gateway_cache_hits_total', 'Cache hits', ['endpoint'])
cache_misses = Counter('gateway_cache_misses_total', 'Cache misses', ['endpoint'])

# API metrics
api_calls = Counter('gateway_api_calls_total', 'API calls', ['endpoint', 'status'])

# Coalescing metrics
coalesced_requests = Counter('gateway_coalesced_requests_total', 'Coalesced', ['endpoint'])

# Circuit breaker metrics
circuit_breaker_state = Gauge('gateway_circuit_breaker_state', 'State (0=closed, 1=half_open, 2=open)')

# Rate limit metrics
rate_limit_used = Gauge('gateway_rate_limit_used', 'API calls used this month')
rate_limit_remaining = Gauge('gateway_rate_limit_remaining', 'Remaining calls')
```

### Endpoint `/metrics`

Généré automatiquement par `prometheus_fastapi_instrumentator` :

```text
# HELP gateway_cache_hits_total Cache hits
# TYPE gateway_cache_hits_total counter
gateway_cache_hits_total{endpoint="airports"} 89.0
gateway_cache_hits_total{endpoint="flights"} 45.0

# HELP gateway_circuit_breaker_state State
# TYPE gateway_circuit_breaker_state gauge
gateway_circuit_breaker_state 0.0

# HELP gateway_rate_limit_used API calls used
# TYPE gateway_rate_limit_used gauge
gateway_rate_limit_used 1234.0
```

---

## Configuration

### Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `AVIATIONSTACK_API_KEY` | - | Clé API (requis) |
| `AVIATIONSTACK_BASE_URL` | <http://api.aviationstack.com/v1> | URL de l'API |
| `MONGODB_URL` | mongodb://localhost:27017 | URL MongoDB |
| `MONGODB_DATABASE` | hello_mira | Nom de la base |
| `CACHE_TTL` | 300 | TTL cache en secondes |
| `DEBUG` | false | Mode debug |

### Fichier `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aviationstack_api_key: str
    aviationstack_base_url: str = "http://api.aviationstack.com/v1"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "hello_mira"
    cache_ttl: int = 300
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### Docker Compose (Extrait)

```yaml
gateway:
  build:
    context: ./gateway
  environment:
    AVIATIONSTACK_API_KEY: ${AVIATIONSTACK_API_KEY}
    MONGODB_URL: mongodb://admin:${MONGO_PASSWORD}@mongo:27017
    MONGODB_DATABASE: hello_mira
    CACHE_TTL: 300
    DEBUG: ${DEBUG:-false}
  ports:
    - "8004:8004"
  healthcheck:
    test: ["CMD", "python", "-c", "import httpx; exit(0 if httpx.get('http://localhost:8004/health').status_code == 200 else 1)"]
```

---

## Bonnes Pratiques

### 1. Monitoring

Toujours surveiller :

- **Hit rate cache** : Devrait être > 50% en production
- **Rate limit remaining** : Alerter si < 1000
- **Circuit breaker state** : Alerter si != CLOSED

### 2. Tuning

| Paramètre | Bas trafic | Haut trafic |
|-----------|------------|-------------|
| Cache TTL | 600s | 300s |
| Circuit failure_threshold | 10 | 5 |
| Circuit recovery_timeout | 60s | 30s |

### 3. Debugging

```bash
# Logs du gateway
docker-compose logs -f gateway

# Stats temps réel
watch -n 5 'curl -s http://localhost:8004/stats | jq .'

# Métriques Prometheus
curl http://localhost:8004/metrics | grep gateway_
```
