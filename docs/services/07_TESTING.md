# 🧪 Stratégie de Tests - Documentation Technique

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture des Tests](#architecture-des-tests)
3. [Configuration Pytest](#configuration-pytest)
4. [Tests End-to-End](#tests-end-to-end)
5. [Tests de Performance](#tests-de-performance)
6. [Fixtures et Helpers](#fixtures-et-helpers)
7. [Exécution des Tests](#exécution-des-tests)
8. [Bonnes Pratiques](#bonnes-pratiques)

---

## Vue d'Ensemble

Le projet utilise une stratégie de tests à plusieurs niveaux :

| Type | Objectif | Outil |
|------|----------|-------|
| **E2E** | Valider les flux complets inter-services | pytest-asyncio |
| **Performance** | Valider cache, coalescing, métriques | Shell scripts + curl |

### Structure des Tests

```text
tests/
├── __init__.py
├── conftest.py              # Fixtures globales partagées
├── README.md                # Documentation tests
│
├── e2e/                     # Tests End-to-End
│   ├── __init__.py
│   ├── conftest.py          # Fixtures E2E
│   ├── test_airport_service.py
│   ├── test_flight_service.py
│   ├── test_assistant_orchestration.py
│   └── test_gateway.py
│
└── performance/             # Tests de Performance
    ├── __init__.py
    ├── test_cache_and_coalescing.sh
    ├── test_cache_isolated.sh
    └── test_coalescing_isolated.sh
```

---

## Architecture des Tests

### Diagramme de Flux E2E

```text
┌─────────────────────────────────────────────────────────────────┐
│                        pytest-asyncio                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    conftest.py                             │  │
│  │                                                            │  │
│  │  • gateway_client  → http://localhost:8004                │  │
│  │  • airport_client  → http://localhost:8001                │  │
│  │  • flight_client   → http://localhost:8002                │  │
│  │  • assistant_client → http://localhost:8003               │  │
│  │  • all_services    → Dict avec tous les clients           │  │
│  │  • check_services_running → Vérifie santé services        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│           ┌────────────────┼────────────────┐                   │
│           ▼                ▼                ▼                   │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────┐        │
│  │test_gateway.py │ │test_airport  │ │test_assistant  │        │
│  │                │ │_service.py   │ │_orchestration  │        │
│  │• Health checks │ │• Recherche   │ │• Interprétation│        │
│  │• Cache tests   │ │• Départs     │ │• Orchestration │        │
│  │• Coalescing    │ │• Arrivées    │ │• Full journey  │        │
│  │• Métriques     │ │              │ │                │        │
│  └────────────────┘ └──────────────┘ └────────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Services                       │
│                                                                  │
│   Gateway(8004)  Airport(8001)  Flight(8002)  Assistant(8003)  │
│        │              │              │              │           │
│        └──────────────┴──────────────┴──────────────┘           │
│                            │                                     │
│                      MongoDB(27017)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration Pytest

### Fichier `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    e2e: marks tests as end-to-end (require all services running)
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    performance: marks tests as performance tests
addopts = -v --tb=short
```

### Markers Personnalisés

| Marker | Description | Sélection |
|--------|-------------|-----------|
| `@pytest.mark.e2e` | Tests nécessitant tous les services | `-m e2e` |
| `@pytest.mark.slow` | Tests lents (>5s) | `-m "not slow"` |
| `@pytest.mark.integration` | Tests d'intégration | `-m integration` |
| `@pytest.mark.performance` | Tests de performance | `-m performance` |

---

## Tests End-to-End

### TestGatewayHealthE2E

**Fichier** : `tests/e2e/test_gateway.py`

```python
@pytest.mark.e2e
class TestGatewayHealthE2E:
    """Tests e2e du health check Gateway."""

    async def test_health_check(self, gateway_client: AsyncClient):
        """Vérifie que le Gateway répond au healthcheck avec infos rate limit."""
        response = await gateway_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "cache" in data
        assert "circuit_breaker" in data
        assert "rate_limit" in data
```

### TestGatewayCacheE2E

```python
@pytest.mark.e2e
class TestGatewayCacheE2E:
    """Tests e2e du cache Gateway."""

    async def test_cache_behavior_airports(self, gateway_client: AsyncClient):
        """
        Scénario e2e:
        1. Première requête (cache miss)
        2. Deuxième requête identique (cache hit)
        """
        iata_code = "LYS"

        response1 = await gateway_client.get(f"/airports?iata={iata_code}")
        assert response1.status_code == 200

        response2 = await gateway_client.get(f"/airports?iata={iata_code}")
        assert response2.status_code == 200

        # Données identiques = cache fonctionnel
        assert response1.json() == response2.json()
```

### TestGatewayCoalescingE2E

```python
@pytest.mark.e2e
class TestGatewayCoalescingE2E:
    """Tests e2e du request coalescing."""

    async def test_coalescing_simultaneous_requests(self, gateway_client: AsyncClient):
        """
        Envoie 5 requêtes identiques simultanées.
        Devrait résulter en 1 seul appel API.
        """
        iata_code = "TLS"

        tasks = [
            gateway_client.get(f"/airports?iata={iata_code}")
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Toutes doivent réussir
        successful = sum(1 for r in responses
                        if not isinstance(r, Exception)
                        and r.status_code in [200, 404])
        assert successful >= 4
```

### TestGatewayMetricsE2E

```python
@pytest.mark.e2e
class TestGatewayMetricsE2E:
    """Tests e2e des métriques Prometheus."""

    async def test_cache_hit_increases_after_request(self, gateway_client: AsyncClient):
        """
        1. Lire métriques initiales
        2. Faire une requête (mise en cache)
        3. Refaire la même requête (cache hit)
        4. Vérifier augmentation cache_hits
        """
        # Lecture initiale
        metrics1 = await gateway_client.get("/metrics")
        pattern = r'gateway_cache_hits_total\{endpoint="airports"\}\s+([\d.]+)'
        match1 = re.search(pattern, metrics1.text)
        initial_hits = float(match1.group(1)) if match1 else 0

        # Requêtes
        await gateway_client.get("/airports?iata=CDG")  # Mise en cache
        await gateway_client.get("/airports?iata=CDG")  # Cache hit

        # Vérification
        metrics2 = await gateway_client.get("/metrics")
        match2 = re.search(pattern, metrics2.text)
        final_hits = float(match2.group(1)) if match2 else 0

        assert final_hits >= initial_hits
```

### TestAssistantOrchestration

**Fichier** : `tests/e2e/test_assistant_orchestration.py`

```python
@pytest.mark.e2e
class TestAssistantOrchestration:
    """Tests e2e de l'orchestration Assistant."""

    async def test_assistant_calls_airport_service(
        self,
        assistant_client: AsyncClient,
        airport_client: AsyncClient
    ):
        """
        Scénario: Assistant → Airport service
        1. Utilisateur envoie un prompt
        2. Assistant interprète et appelle Airport
        3. Assistant retourne une réponse formatée
        """
        # Vérifier Airport accessible
        health = await airport_client.get("/api/v1/health")
        assert health.status_code == 200

        # Envoyer prompt
        response = await assistant_client.post(
            "/api/v1/assistant/answer",
            json={"prompt": "Trouve-moi l'aéroport CDG"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "cdg" in data["answer"].lower() or "charles de gaulle" in data["answer"].lower()

    async def test_full_user_journey(self, all_services: Dict[str, AsyncClient]):
        """
        Parcours utilisateur complet:
        1. Info aéroport via Assistant
        2. Accès direct Airport
        3. Info vol via Assistant
        """
        airport = all_services["airport"]
        assistant = all_services["assistant"]

        # Étape 1
        r1 = await assistant.post(
            "/api/v1/assistant/answer",
            json={"prompt": "Où se trouve l'aéroport CDG ?"}
        )
        assert "cdg" in r1.json()["answer"].lower()

        # Étape 2
        r2 = await airport.get("/api/v1/airports/CDG")
        assert r2.json()["iata_code"] == "CDG"

        # Étape 3
        r3 = await assistant.post(
            "/api/v1/assistant/answer",
            json={"prompt": "Y a-t-il des vols Air France ?"}
        )
        assert r3.status_code == 200
```

---

## Tests de Performance

### test_cache_and_coalescing.sh

**Fichier** : `tests/performance/test_cache_and_coalescing.sh`

#### Phase 1 : Test Coalescing

```bash
# Test 1.1 : 10 requêtes simultanées pour CDG
echo "Test 1.1 : 10 requêtes simultanées pour CDG (airport)"
echo "Attendu : 1 API call, 9 requêtes coalescées"

for i in {1..10}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
wait
```

#### Phase 2 : Test Cache

```bash
# Test 2.1 : Premier appel (cache miss attendu)
echo "Test 2.1 : Premier appel ORY (cache MISS attendu)"
curl -s "http://localhost:8001/api/v1/airports/ORY"

# Test 2.2 : Deuxième appel immédiat (cache hit attendu)
echo "Test 2.2 : Deuxième appel ORY immédiat (cache HIT attendu)"
curl -s "http://localhost:8001/api/v1/airports/ORY"
```

#### Phase 3 : Vérification Métriques

```bash
# Récupération des métriques Prometheus
curl -s "http://localhost:8004/metrics" | grep -E "gateway_(cache|api_calls|coalesced)"
```

### Exécution

```bash
# Lancer les tests de performance
cd tests/performance
chmod +x test_cache_and_coalescing.sh
./test_cache_and_coalescing.sh
```

### Résultats Attendus

```text
═══════════════════════════════════════
PHASE 1 : TEST DU COALESCING
═══════════════════════════════════════

Test 1.1 : 10 requêtes simultanées pour CDG (airport)
Attendu : 1 API call, 9 requêtes coalescées
✅ 10 requêtes terminées en 2s

═══════════════════════════════════════
PHASE 2 : TEST DU CACHE MONGODB
═══════════════════════════════════════

Test 2.1 : Premier appel ORY (cache MISS attendu)
✅ Status: 200 OK

Test 2.2 : Deuxième appel ORY immédiat (cache HIT attendu)
✅ Status: 200 OK (devrait venir du cache)

═══════════════════════════════════════
PHASE 3 : MÉTRIQUES PROMETHEUS
═══════════════════════════════════════

gateway_cache_hits_total{endpoint="airports"} 89.0
gateway_cache_misses_total{endpoint="airports"} 12.0
gateway_coalesced_requests_total{endpoint="airports"} 45.0
gateway_api_calls_total{endpoint="airports",status="success"} 15.0
```

---

## Fixtures et Helpers

### Fixtures Clients HTTP

**Fichier** : `tests/conftest.py`

```python
@pytest_asyncio.fixture
async def gateway_client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour le Gateway."""
    async with AsyncClient(base_url="http://localhost:8004", timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture
async def airport_client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour le service Airport."""
    async with AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture
async def flight_client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour le service Flight."""
    async with AsyncClient(base_url="http://localhost:8002", timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture
async def assistant_client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour le service Assistant."""
    async with AsyncClient(base_url="http://localhost:8003", timeout=30.0) as client:
        yield client

@pytest_asyncio.fixture
async def all_services() -> AsyncGenerator[Dict[str, AsyncClient], None]:
    """Tous les clients HTTP pour tests e2e complets."""
    async with AsyncClient(base_url="http://localhost:8004", timeout=10.0) as gateway, \
               AsyncClient(base_url="http://localhost:8001", timeout=10.0) as airport, \
               AsyncClient(base_url="http://localhost:8002", timeout=10.0) as flight, \
               AsyncClient(base_url="http://localhost:8003", timeout=30.0) as assistant:
        yield {
            "gateway": gateway,
            "airport": airport,
            "flight": flight,
            "assistant": assistant
        }
```

### Fixture Vérification Services

```python
@pytest_asyncio.fixture(scope="module")
async def check_services_running():
    """Vérifie que tous les services sont démarrés."""
    services = {
        "gateway": "http://localhost:8004/health",
        "airport": "http://localhost:8001/api/v1/health",
        "flight": "http://localhost:8002/api/v1/health",
        "assistant": "http://localhost:8003/api/v1/health"
    }

    async with AsyncClient(timeout=5.0) as client:
        for service_name, health_url in services.items():
            try:
                response = await client.get(health_url)
                if response.status_code != 200:
                    raise RuntimeError(f"Service {service_name} not healthy")
            except Exception as e:
                raise RuntimeError(
                    f"Service {service_name} not accessible. "
                    f"Make sure docker-compose is running."
                )
```

### Fixtures Données de Test

```python
@pytest.fixture
def sample_user_prompts() -> list[str]:
    """Prompts utilisateur d'exemple."""
    return [
        "Quels vols partent de CDG cet après-midi ?",
        "Je suis sur le vol AF447, à quelle heure vais-je arriver ?",
        "Trouve-moi l'aéroport le plus proche de Lille",
        "Quel est le statut du vol LH400 ?",
        "Y a-t-il des vols qui arrivent à JFK maintenant ?"
    ]

@pytest.fixture
def e2e_test_scenarios() -> Dict[str, Dict]:
    """Scénarios de test e2e prédéfinis."""
    return {
        "search_airport_and_flights": {
            "description": "Rechercher un aéroport puis ses vols",
            "steps": [
                {"service": "airport", "endpoint": "/api/v1/airports/CDG"},
                {"service": "airport", "endpoint": "/api/v1/airports/CDG/departures"}
            ]
        },
        # ...
    }
```

---

## Exécution des Tests

### Prérequis

```bash
# 1. Démarrer tous les services
docker-compose up -d

# 2. Attendre que les services soient healthy
docker-compose ps  # Vérifier état "healthy"

# 3. Installer les dépendances de test
pip install pytest pytest-asyncio httpx
```

### Commandes

```bash
# Tous les tests e2e
pytest tests/e2e -v -m e2e

# Tests Gateway uniquement
pytest tests/e2e/test_gateway.py -v

# Tests Assistant uniquement
pytest tests/e2e/test_assistant_orchestration.py -v

# Exclure les tests lents
pytest tests/e2e -v -m "not slow"

# Avec sortie détaillée
pytest tests/e2e -v --tb=long

# Tests de performance (shell)
cd tests/performance
./test_cache_and_coalescing.sh
```

### Sortie Attendue

```text
========================= test session starts ==========================
platform linux -- Python 3.11.0, pytest-9.0.1, pluggy-1.5.0
rootdir: /app
plugins: asyncio-0.24.0
collected 15 items

tests/e2e/test_gateway.py::TestGatewayHealthE2E::test_health_check PASSED
tests/e2e/test_gateway.py::TestGatewayCacheE2E::test_cache_behavior PASSED
tests/e2e/test_gateway.py::TestGatewayCoalescingE2E::test_coalescing PASSED
tests/e2e/test_gateway.py::TestGatewayMetricsE2E::test_metrics_exist PASSED
tests/e2e/test_assistant_orchestration.py::TestAssistantOrchestration::test_health PASSED
tests/e2e/test_assistant_orchestration.py::TestAssistantOrchestration::test_interpret PASSED
tests/e2e/test_assistant_orchestration.py::TestAssistantOrchestration::test_answer PASSED

========================= 15 passed in 45.23s ==========================
```

---

## Bonnes Pratiques

### 1. Isolation des Tests

```python
# Chaque test doit être indépendant
async def test_independent(self, gateway_client):
    # Ne pas dépendre de l'état laissé par un autre test
    response = await gateway_client.get("/airports?iata=NEW")
    assert response.status_code == 200
```

### 2. Timeouts Appropriés

```python
# Assistant peut prendre plus de temps (LLM)
async with AsyncClient(timeout=30.0) as assistant_client:
    ...

# Services simples peuvent avoir timeout plus court
async with AsyncClient(timeout=10.0) as airport_client:
    ...
```

### 3. Assertions Claires

```python
# Mauvais
assert response.json()

# Bon
assert response.status_code == 200
data = response.json()
assert "answer" in data
assert len(data["answer"]) > 0
```

### 4. Gestion des États Variables

```python
# Le vol peut exister ou non selon le moment
async def test_flight_status(self, flight_client):
    response = await flight_client.get("/api/v1/flights/AF447")
    # Accepter 200 (vol trouvé) ou 404 (pas de vol actuellement)
    assert response.status_code in [200, 404]
```

### 5. Nettoyage Automatique

```python
@pytest_asyncio.fixture
async def gateway_client():
    async with AsyncClient(...) as client:
        yield client
    # Le client est automatiquement fermé après le test
```

---

## CI/CD Integration

### GitHub Actions (Exemple)

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          sleep 60
          docker-compose ps

      - name: Run tests
        run: |
          pip install pytest pytest-asyncio httpx
          pytest tests/e2e -v

      - name: Stop services
        run: docker-compose down -v
```
