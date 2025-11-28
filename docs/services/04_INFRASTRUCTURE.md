# Infrastructure - Documentation Ultra-Détaillée

## Vue d'Ensemble

L'infrastructure Hello Mira est orchestrée via **Docker Compose** et comprend :

- 7 services conteneurisés
- 1 réseau bridge dédié
- 4 volumes persistants
- Monitoring complet avec Prometheus + Grafana

### Architecture Globale

```text
                                    ┌─────────────────────────────────┐
                                    │         Internet               │
                                    └───────────────┬─────────────────┘
                                                    │
                                    ┌───────────────▼─────────────────┐
                                    │       API Aviationstack         │
                                    │       api.aviationstack.com     │
                                    └───────────────┬─────────────────┘
                                                    │
                    ┌───────────────────────────────▼───────────────────────────────┐
                    │                         GATEWAY                               │
                    │                        (Port 8004)                            │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
                    │  │  Cache   │ │  Rate    │ │ Circuit  │ │   Request      │  │
                    │  │ MongoDB  │ │ Limiter  │ │ Breaker  │ │   Coalescer    │  │
                    │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
                    └───────────────────────────────┬───────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
        ┌───────────▼───────────┐     ┌─────────────▼─────────────┐     ┌──────────▼──────────┐
        │       AIRPORT         │     │         FLIGHT            │     │      ASSISTANT      │
        │      (Port 8001)      │     │        (Port 8002)        │     │     (Port 8003)     │
        │                       │     │                           │     │                     │
        │  - Geocoding          │     │  - Flight Status          │     │  - LangGraph        │
        │  - Airport Search     │     │  - History (MongoDB)      │     │  - Mistral AI       │
        │  - Departures/Arrivals│     │  - Statistics             │     │  - Tools            │
        └───────────────────────┘     └─────────────┬─────────────┘     └──────────┬──────────┘
                                                    │                              │
                                        ┌───────────▼───────────┐                  │
                                        │       MongoDB         │◄─────────────────┘
                                        │      (Port 27017)     │
                                        │  - Cache Gateway      │
                                        │  - Flights History    │
                                        │  - Rate Limit Counter │
                                        └───────────────────────┘
                                                    ▲
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                     MONITORING                                │
                    │                                                               │
        ┌───────────▼───────────┐     ┌─────────────────────────┐     ┌────────────────────┐
        │     PROMETHEUS        │────▶│        GRAFANA          │     │     FRONTEND       │
        │     (Port 9090)       │     │       (Port 3000)       │     │    (Port 8501)     │
        └───────────────────────┘     └─────────────────────────┘     │    Streamlit       │
                                                                       └────────────────────┘
```

### Tableau des Services

| Service | Port | Image | Description |
|---------|------|-------|-------------|
| **mongo** | 27017 | `mongo:7.0` | Base de données + cache |
| **gateway** | 8004 | Custom | API Gateway (cache, rate limit, circuit breaker) |
| **airport** | 8001 | Custom | Recherche d'aéroports |
| **flight** | 8002 | Custom | Suivi de vols |
| **assistant** | 8003 | Custom | IA conversationnelle |
| **prometheus** | 9090 | `prom/prometheus:v2.54.0` | Collecte de métriques |
| **grafana** | 3000 | `grafana/grafana:10.2.2` | Visualisation |
| **frontend** | 8501 | Custom | Interface Streamlit |

---

## Docker Compose - Configuration Détaillée

### Fichier : docker-compose.yml

**Localisation** : Racine du projet
**Lignes** : 528
**Rôle** : Orchestration complète de l'infrastructure

### Structure du Fichier

```yaml
services:
  mongo:        # Base de données
  gateway:      # API Gateway
  airport:      # Microservice Airport
  flight:       # Microservice Flight
  assistant:    # Microservice Assistant
  prometheus:   # Monitoring
  grafana:      # Dashboards
  frontend:     # Interface utilisateur

networks:
  hello-mira-network:   # Réseau bridge dédié

volumes:
  mongo_data:           # Données MongoDB
  mongo_config:         # Config MongoDB
  prometheus_data:      # Métriques Prometheus
  grafana_data:         # Dashboards Grafana
```

---

## Service MongoDB

### Configuration Docker Compose Mongo

```yaml
mongo:
  image: mongo:7.0
  container_name: hello-mira-mongo
  restart: unless-stopped

  environment:
    MONGO_INITDB_ROOT_USERNAME: admin
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    MONGO_INITDB_DATABASE: hello_mira

  ports:
    - "27017:27017"

  volumes:
    - mongo_data:/data/db
    - mongo_config:/data/configdb

  healthcheck:
    test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/hello_mira --quiet
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 40s

  networks:
    - hello-mira-network
```

### Collections MongoDB

| Collection | Service | Rôle |
|------------|---------|------|
| `gateway_cache` | Gateway | Cache des réponses Aviationstack (TTL) |
| `api_rate_limit` | Gateway | Compteur mensuel d'appels API |
| `flights` | Flight | Historique des vols consultés |

### Index Créés

```javascript
// Gateway - Cache avec TTL automatique
db.gateway_cache.createIndex({"expires_at": 1}, {expireAfterSeconds: 0})

// Flight - Recherche d'historique
db.flights.createIndex({"flight_iata": 1})
db.flights.createIndex({"flight_date": 1})
db.flights.createIndex({"flight_iata": 1, "flight_date": 1})
```

---

## Service Gateway - API Gateway Centralisé

### Configuration Docker Compose Gateway

```yaml
gateway:
  build:
    context: ./gateway
    dockerfile: Dockerfile

  image: hello-mira/gateway:latest
  container_name: hello-mira-gateway
  restart: unless-stopped

  depends_on:
    mongo:
      condition: service_healthy

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
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 30s

  networks:
    - hello-mira-network
```

### Architecture du Gateway

Le Gateway implémente 4 patterns d'optimisation :

```text
gateway/
├── main.py              # Point d'entrée FastAPI
├── config.py            # Configuration
├── cache.py             # Cache MongoDB avec TTL
├── rate_limiter.py      # Limite 10000 appels/mois
├── circuit_breaker.py   # Protection contre les pannes
├── request_coalescer.py # Fusion des requêtes identiques
├── Dockerfile
├── requirements.txt
└── monitoring/
    └── metrics.py       # Métriques Prometheus
```

### 1. Cache MongoDB (cache.py)

**Rôle** : Évite les appels API redondants pendant 5 minutes

```python
class CacheService:
    """Cache avec TTL via MongoDB."""

    def __init__(self, collection=None, ttl: int = 300):
        self.collection = collection
        self.ttl = ttl
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        doc = await self.collection.find_one({"_id": key})
        if doc and doc.get("expires_at") > datetime.utcnow():
            self._hits += 1
            return doc.get("data")
        self._misses += 1
        return None

    async def set(self, key: str, data: Any) -> bool:
        """Stocke une valeur dans le cache."""
        await self.collection.replace_one(
            {"_id": key},
            {
                "_id": key,
                "data": data,
                "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl),
                "created_at": datetime.utcnow()
            },
            upsert=True
        )
        return True
```

**Fonctionnement** :

- Clé de cache : `"{endpoint}:{sorted(params.items())}"`
- TTL : 300 secondes (configurable)
- Index MongoDB avec `expireAfterSeconds: 0` pour auto-suppression

### 2. Rate Limiter (rate_limiter.py)

**Rôle** : Respecte le quota de 10000 appels/mois d'Aviationstack

```python
class RateLimiter:
    """
    Rate limiter partagé via MongoDB.
    - 10000 appels/mois (Basic Plan)
    - Reset automatique le 1er du mois
    """

    def __init__(self, collection=None, max_calls: int = 10000):
        self.collection = collection
        self.max_calls = max_calls
        self._key = "aviationstack_api_calls"

    def _get_month_key(self) -> str:
        """Retourne '2025-11' pour novembre 2025."""
        now = datetime.utcnow()
        return f"{now.year}-{now.month:02d}"

    async def check_and_increment(self):
        """
        Vérifie le quota et incrémente le compteur.
        Raises: RateLimitExceeded si 10000 appels atteints
        """
        month = self._get_month_key()
        doc = await self.collection.find_one({"_id": self._key})

        # Reset si nouveau mois
        if doc and doc.get("month") == month:
            count = doc.get("count", 0)
        else:
            count = 0
            logger.info(f"🔄 Nouveau mois {month}, compteur reset")

        if count >= self.max_calls:
            reset = self._get_next_reset().strftime("%d/%m/%Y")
            raise RateLimitExceeded(
                f"Limite atteinte: {count}/{self.max_calls} appels. Reset le {reset}"
            )

        # Incrémente
        await self.collection.replace_one(
            {"_id": self._key},
            {
                "_id": self._key,
                "month": month,
                "count": count + 1,
                "max_calls": self.max_calls,
                "updated_at": datetime.utcnow()
            },
            upsert=True
        )
```

**Structure MongoDB** :

```json
{
  "_id": "aviationstack_api_calls",
  "month": "2025-11",
  "count": 42,
  "max_calls": 10000,
  "updated_at": "2025-11-28T10:30:00Z"
}
```

### 3. Circuit Breaker (circuit_breaker.py)

**Rôle** : Protège contre les cascading failures en coupant les appels vers un service défaillant

```python
class CircuitState(Enum):
    CLOSED = "closed"      # Normal - requêtes passent
    OPEN = "open"          # Bloqué - service KO
    HALF_OPEN = "half_open"  # Test - quelques requêtes passent

class CircuitBreaker:
    """
    Circuit Breaker avec les paramètres :
    - failure_threshold: 5 échecs avant ouverture
    - recovery_timeout: 30s avant passage en HALF_OPEN
    - half_open_max_calls: 3 requêtes de test
    """

    def __init__(self, failure_threshold=5, recovery_timeout=30, half_open_max_calls=3):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None

    async def can_execute(self) -> bool:
        """Vérifie si une requête peut passer."""
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        # OPEN
        return False

    async def record_failure(self) -> None:
        """Enregistre un échec."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()

        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                logger.warning(f"🔴 Circuit CLOSED -> OPEN ({self._failure_count} failures)")
                self._state = CircuitState.OPEN

    async def record_success(self) -> None:
        """Enregistre un succès."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                logger.info("✅ Circuit HALF_OPEN -> CLOSED (recovery success)")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
```

**Diagramme d'états** :

```text
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    ▼                                                 │
┌──────────┐  5 échecs  ┌────────┐  30s  ┌───────────┴───┐
│  CLOSED  │───────────▶│  OPEN  │──────▶│   HALF_OPEN   │
└────┬─────┘            └────────┘       └───────────────┘
     │                       ▲                   │
     │                       │  1 échec          │ 3 succès
     │                       └───────────────────┤
     │                                           ▼
     └───────────────────────────────────────────┘
```

### 4. Request Coalescer (request_coalescer.py)

**Rôle** : Fusionne les requêtes identiques concurrentes en un seul appel API

```python
class RequestCoalescer:
    """
    Coalescer centralise pour le gateway.

    Usage:
        # Ces 3 appels simultanés ne déclenchent qu'UN appel API
        results = await asyncio.gather(
            coalescer.execute("airports:CDG", fetch_airport, "CDG"),
            coalescer.execute("airports:CDG", fetch_airport, "CDG"),
            coalescer.execute("airports:CDG", fetch_airport, "CDG")
        )
    """

    def __init__(self):
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._total_requests = 0
        self._coalesced_requests = 0

    async def execute(self, key: str, func, *args, **kwargs):
        """Execute une fonction avec coalescing."""
        self._total_requests += 1

        async with self._lock:
            # Si une requête identique est en cours, on attend son résultat
            if key in self._in_flight:
                self._coalesced_requests += 1
                logger.debug(f"🔗 Coalescing request: {key}")

        if key in self._in_flight:
            return await self._in_flight[key]

        # Nouvelle requête
        async with self._lock:
            task = asyncio.create_task(func(*args, **kwargs))
            self._in_flight[key] = task

        try:
            result = await task
            return result
        finally:
            async with self._lock:
                self._in_flight.pop(key, None)
```

**Exemple concret** :

```text
Requête 1 → "flights:AF282" → Crée task
Requête 2 → "flights:AF282" → Attend task existante (coalesced)
Requête 3 → "flights:AF282" → Attend task existante (coalesced)

Résultat : 1 appel API, 3 réponses identiques
```

### Flux d'une Requête dans le Gateway

```python
async def call_aviationstack(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appelle l'API Aviationstack avec:
    1. Cache MongoDB
    2. Circuit breaker
    3. Request coalescing
    4. Rate limiting
    """

    # 1. Check cache first
    cache_key = f"{endpoint}:{sorted(params.items())}"
    cached = await cache_service.get(cache_key)
    if cached:
        cache_hits.labels(endpoint=endpoint).inc()
        return cached
    cache_misses.labels(endpoint=endpoint).inc()

    # 2. Check circuit breaker
    if not await circuit_breaker.can_execute():
        raise HTTPException(status_code=503, detail="Circuit breaker open")

    # 3. Use request coalescer
    result = await request_coalescer.execute(
        key=cache_key,
        func=_do_api_call,
        endpoint=endpoint,
        params=params,
        cache_key=cache_key
    )
    return result

async def _do_api_call(endpoint, params, cache_key):
    # 4. Check rate limit
    await rate_limiter.check_and_increment()

    # 5. Call API
    response = await http_client.get(url, params=params_with_key)
    data = response.json()

    # 6. Record result for circuit breaker
    await circuit_breaker.record_success()

    # 7. Cache result
    await cache_service.set(cache_key, data)

    return data
```

### Endpoints du Gateway

| Endpoint | Description |
|----------|-------------|
| `GET /` | Root, retourne status |
| `GET /health` | Health check avec état du circuit breaker |
| `GET /usage` | Utilisation du quota API |
| `GET /stats` | Statistiques complètes (cache, rate limit, coalescing) |
| `GET /airports` | Proxy vers Aviationstack /airports |
| `GET /flights` | Proxy vers Aviationstack /flights |
| `GET /metrics` | Métriques Prometheus |

---

## Monitoring - Prometheus + Grafana

### Configuration Prometheus

**Fichier** : `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'hello-mira-platform'
    environment: 'development'

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Gateway (port 8004) - Métriques API Aviationstack
  - job_name: 'gateway'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['gateway:8004']

  # Airport (port 8001)
  - job_name: 'airport'
    scrape_interval: 10s
    static_configs:
      - targets: ['airport:8001']

  # Flight (port 8002)
  - job_name: 'flight'
    scrape_interval: 10s
    static_configs:
      - targets: ['flight:8002']

  # Assistant (port 8003)
  - job_name: 'assistant'
    scrape_interval: 10s
    static_configs:
      - targets: ['assistant:8003']
```

### Métriques Exposées

#### Gateway (gateway/monitoring/metrics.py)

| Métrique | Type | Description |
|----------|------|-------------|
| `gateway_cache_hits_total` | Counter | Cache hits par endpoint |
| `gateway_cache_misses_total` | Counter | Cache misses par endpoint |
| `gateway_api_calls_total` | Counter | Appels API par endpoint et status |
| `gateway_coalesced_requests_total` | Counter | Requêtes coalescées |
| `gateway_circuit_breaker_state` | Gauge | État du circuit (0=closed, 1=half_open, 2=open) |
| `gateway_rate_limit_used` | Gauge | Appels utilisés ce mois |
| `gateway_rate_limit_remaining` | Gauge | Appels restants ce mois |

#### Airport (airport/monitoring/metrics.py)

| Métrique | Type | Description |
|----------|------|-------------|
| `airport_searches_total` | Counter | Recherches par type |
| `airport_search_latency_seconds` | Histogram | Latence des recherches |
| `airport_geocoding_calls_total` | Counter | Appels géocodage |
| `airport_search_results_count` | Histogram | Nombre de résultats |

#### Flight (flight/monitoring/metrics.py)

| Métrique | Type | Description |
|----------|------|-------------|
| `flight_lookups_total` | Counter | Recherches par type et status |
| `flight_lookup_latency_seconds` | Histogram | Latence des recherches |
| `mongodb_operations_total` | Counter | Opérations MongoDB |
| `flights_stored_total` | Counter | Vols stockés |
| `statistics_calculated_total` | Counter | Statistiques calculées |
| `last_on_time_rate` | Gauge | Dernier taux de ponctualité |

#### Assistant (assistant/monitoring/metrics.py)

| Métrique | Type | Description |
|----------|------|-------------|
| `assistant_llm_calls_total` | Counter | Appels LLM par node et modèle |
| `assistant_llm_latency_seconds` | Histogram | Latence LLM |
| `assistant_intent_detected_total` | Counter | Intentions détectées |
| `assistant_tool_calls_total` | Counter | Appels aux tools |
| `assistant_tool_latency_seconds` | Histogram | Latence des tools |
| `assistant_graph_iterations` | Histogram | Itérations ReAct par requête |

### Queries PromQL Utiles

```promql
# Hit-rate du cache Gateway (%)
sum(gateway_cache_hits_total) /
(sum(gateway_cache_hits_total) + sum(gateway_cache_misses_total)) * 100

# Latence P95 des appels LLM
histogram_quantile(0.95, rate(assistant_llm_latency_seconds_bucket[5m]))

# Quota API restant
gateway_rate_limit_remaining

# Circuit breaker ouvert
gateway_circuit_breaker_state == 2

# Appels API par minute
rate(gateway_api_calls_total[1m]) * 60

# Distribution des intentions
sum(rate(assistant_intent_detected_total[5m])) by (intent)

# Taux de coalescing
sum(rate(gateway_coalesced_requests_total[5m])) /
(sum(rate(gateway_coalesced_requests_total[5m])) +
 sum(rate(gateway_api_calls_total[5m]))) * 100
```

### Configuration Grafana

**Fichier** : `monitoring/grafana/provisioning/datasources/grafana-datasources.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "10s"
      httpMethod: POST
```

**Dashboard** : `monitoring/grafana/dashboards/hello-mira-metrics.json`

---

## Dockerfiles

### Pattern Commun

Tous les services utilisent le même pattern :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE <PORT>

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "<PORT>"]
```

### Ports par Service

| Service | Port |
|---------|------|
| Airport | 8001 |
| Flight | 8002 |
| Assistant | 8003 |
| Gateway | 8004 |
| Frontend | 8501 |

---

## Réseau Docker

### Configuration

```yaml
networks:
  hello-mira-network:
    name: hello-mira-network
    driver: bridge
```

### DNS Interne

Docker fournit une résolution DNS automatique :

- `mongo` → 172.18.0.2:27017
- `gateway` → 172.18.0.3:8004
- `airport` → 172.18.0.4:8001
- `flight` → 172.18.0.5:8002
- `assistant` → 172.18.0.6:8003

### Communication Inter-Services

```text
Frontend (8501)
    │
    └──▶ Assistant (8003)
              │
              ├──▶ Airport (8001)
              │         │
              │         └──▶ Gateway (8004)
              │                    │
              │                    ├──▶ MongoDB (27017)
              │                    └──▶ Aviationstack API
              │
              └──▶ Flight (8002)
                        │
                        ├──▶ Gateway (8004)
                        └──▶ MongoDB (27017)
```

---

## Volumes Persistants

```yaml
volumes:
  mongo_data:
    name: hello-mira-mongo-data    # Données MongoDB
  mongo_config:
    name: hello-mira-mongo-config  # Configuration MongoDB
  prometheus_data:
    name: hello-mira-prometheus-data  # Métriques historiques
  grafana_data:
    name: hello-mira-grafana-data  # Dashboards sauvegardés
```

### Gestion des Volumes

```bash
# Lister les volumes
docker volume ls | grep hello-mira

# Supprimer les volumes (ATTENTION: perte de données)
docker-compose down -v

# Backup MongoDB
docker exec hello-mira-mongo mongodump --out /data/backup

# Restore MongoDB
docker exec hello-mira-mongo mongorestore /data/backup
```

---

## Health Checks

Tous les services ont des health checks configurés :

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import httpx; exit(0 if httpx.get('http://localhost:<PORT>/api/v1/health').status_code == 200 else 1)"]
  interval: 30s      # Vérifie toutes les 30s
  timeout: 10s       # Timeout de la vérification
  retries: 3         # 3 échecs avant "unhealthy"
  start_period: 40s  # Délai avant la première vérification
```

### Dépendances avec Health Checks

```yaml
# Gateway attend que MongoDB soit healthy
gateway:
  depends_on:
    mongo:
      condition: service_healthy

# Airport attend que Gateway soit healthy
airport:
  depends_on:
    gateway:
      condition: service_healthy

# Assistant attend que Airport ET Flight soient healthy
assistant:
  depends_on:
    airport:
      condition: service_healthy
    flight:
      condition: service_healthy
```

---

## Variables d'Environnement

### Fichier .env (requis)

```env
# API Keys
AVIATIONSTACK_API_KEY=858189fdc6...
MISTRAL_API_KEY=...

# MongoDB
MONGO_PASSWORD=your_secure_password

# Grafana (optionnel)
GRAFANA_PASSWORD=admin

# Debug (optionnel)
DEBUG=false
DEMO_MODE=false
MISTRAL_MODEL=mistral-large-latest
```

### Variables par Service

| Service | Variables |
|---------|-----------|
| **mongo** | `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`, `MONGO_INITDB_DATABASE` |
| **gateway** | `AVIATIONSTACK_API_KEY`, `MONGODB_URL`, `CACHE_TTL`, `DEBUG` |
| **airport** | `GATEWAY_URL`, `DEBUG`, `CORS_ORIGINS` |
| **flight** | `GATEWAY_URL`, `MONGODB_URL`, `DEBUG`, `CORS_ORIGINS` |
| **assistant** | `MISTRAL_API_KEY`, `MISTRAL_MODEL`, `AIRPORT_API_URL`, `FLIGHT_API_URL`, `DEBUG`, `DEMO_MODE` |
| **grafana** | `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`, `GF_AUTH_ANONYMOUS_ENABLED` |

---

## Commandes Utiles

### Démarrage

```bash
# Démarrer tous les services
docker-compose up -d

# Démarrer avec rebuild
docker-compose up -d --build

# Démarrer un service spécifique
docker-compose up -d airport
```

### Logs

```bash
# Tous les logs
docker-compose logs -f

# Logs d'un service
docker-compose logs -f airport
docker-compose logs -f gateway
docker-compose logs -f assistant

# 100 dernières lignes
docker-compose logs --tail=100
```

### État des Services

```bash
# État
docker-compose ps

# Health status
docker inspect --format='{{.State.Health.Status}}' hello-mira-airport
```

### Shell dans un Container

```bash
docker-compose exec mongo mongosh
docker-compose exec airport sh
docker-compose exec gateway sh
```

### Arrêt

```bash
# Arrêter (garde les volumes)
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

---

## Problèmes Rencontrés et Solutions

### Problème 1 : Quota API Épuisé

**Symptôme** : Erreur 429 "Rate limit exceeded"

**Solutions** :

- Augmenter le TTL du cache (`CACHE_TTL=600`)
- Activer le mode DEMO (`DEMO_MODE=true`)
- Attendre le reset le 1er du mois

### Problème 2 : Circuit Breaker Ouvert

**Symptôme** : Erreur 503 "Circuit breaker open"

**Solution** : Attendre 30 secondes (recovery_timeout) pour le passage en HALF_OPEN

### Problème 3 : MongoDB Non Disponible

**Symptôme** : Services en erreur au démarrage

**Solution** : Vérifier que MongoDB a eu le temps de démarrer (start_period: 40s)

### Problème 4 : Prometheus Ne Collecte Pas

**Symptôme** : Pas de métriques dans Grafana

**Solution** :

- Vérifier que les services exposent `/metrics`
- Vérifier la configuration `prometheus.yml`
- Vérifier que les services sont dans le même réseau

---

## Conclusion

L'infrastructure Hello Mira implémente les bonnes pratiques :

1. **Gateway Pattern** : Point unique d'accès à l'API externe avec optimisations
2. **Cache Intelligent** : MongoDB avec TTL pour réduire les appels API
3. **Rate Limiting** : Respect du quota mensuel Aviationstack
4. **Circuit Breaker** : Protection contre les cascading failures
5. **Request Coalescing** : Fusion des requêtes concurrentes identiques
6. **Health Checks** : Dépendances ordonnées au démarrage
7. **Monitoring Complet** : Prometheus + Grafana avec métriques custom
8. **Volumes Persistants** : Données MongoDB et métriques conservées
9. **Réseau Isolé** : Communication sécurisée entre services
10. **Configuration Externalisée** : Variables d'environnement via .env
