# Tests - Hello Mira Flight Platform

Organisation professionnelle des tests selon les **best practices pytest 2025**.

## 📁 Structure Complète (Best Practices 2025)

### Architecture Globale

```text
hello-mira-flight-platform/
│
├── airport/tests/                      # Tests microservice Airport
│   ├── conftest.py                     # Fixtures globales airport
│   ├── unit/                           # Tests unitaires isolés
│   │   ├── conftest.py                 # Fixtures spécifiques unit
│   │   └── test_*.py
│   ├── integration/                    # Tests endpoints API
│   │   ├── conftest.py                 # Fixtures spécifiques integration
│   │   └── test_*_endpoints.py
│   ├── fixtures/                       # ⭐ NOUVEAU 2025: Fixtures complexes
│   │   └── __init__.py
│   ├── mocks/                          # ⭐ NOUVEAU 2025: Mock data
│   │   ├── airport_response_sample.json
│   │   └── flight_response_sample.json
│   └── exploration/                    # ⭐ Scripts démarche empirique
│       ├── README.md                   # Documentation approche
│       └── explore_*.py                # Scripts (pas test_*)
│
├── flight/tests/                       # Tests microservice Flight
│   ├── conftest.py                     # Fixtures globales flight
│   ├── unit/
│   │   ├── conftest.py
│   │   └── test_*.py
│   ├── integration/
│   │   ├── conftest.py
│   │   └── test_*_endpoints.py
│   ├── fixtures/
│   ├── mocks/
│   └── exploration/
│       └── README.md
│
├── assistant/tests/                    # Tests microservice Assistant (futur)
│   └── (même structure)
│
└── tests/                              # Tests cross-services
    ├── conftest.py                     # ⭐ Fixtures cross-services
    ├── performance/                    # Tests de performance
    │   ├── test_cache_isolated.sh
    │   ├── test_coalescing_isolated.sh
    │   ├── test_coalescing.sh
    │   └── test_cache_and_coalescing.sh
    └── e2e/                            # ⭐ Tests end-to-end
        ├── conftest.py                 # Scénarios e2e
        └── test_*.py
```

## 🎯 Nouveautés Best Practices 2025

### 1. Séparation `exploration/` vs `tests/`

**Problème 2024** : Scripts d'exploration mélangés avec tests automatisés

**Solution 2025** :

- Scripts d'exploration renommés `explore_*.py` (pytest les ignore)
- Placés dans `exploration/` avec README explicatif
- Montre la démarche empirique sans confusion

### 2. Dossier `mocks/` dédié

**Problème 2024** : Mock data éparpillée dans le code

**Solution 2025** :

- Dossier `mocks/` dédié pour JSON samples
- Facilite la maintenance et réutilisation
- Séparation claire données vs code

### 3. Dossier `fixtures/` pour fixtures complexes

**Problème 2024** : Fixtures complexes noyées dans conftest.py

**Solution 2025** :

- Dossier `fixtures/` pour fixtures partagées complexes
- Permet de mieux organiser fixtures volumineuses
- Modules séparés par domaine

### 4. Hiérarchie `conftest.py` (Global → Integration → Unit)

**Best Practice 2025** : 3 niveaux de fixtures

```text
tests/conftest.py               # Niveau 1: Cross-services
  └── airport/tests/conftest.py # Niveau 2: Service
      ├── unit/conftest.py      # Niveau 3: Type de test
      └── integration/conftest.py
```

**Avantages** :

- Fixtures au bon niveau de scope
- Pas de pollution entre types de tests
- Découverte pytest optimisée

## 🧪 Types de Tests

### 1. Tests Unitaires (isolés, rapides)

**Localisation** : `<service>/tests/unit/`

**Caractéristiques** :

- Testent une fonction/classe isolément
- Utilisent mocks pour dépendances externes
- Pas d'appels réseau réels
- Exécution < 1s par test

**Exemples** :

```python
# airport/tests/unit/test_cache_service.py
async def test_cache_miss_returns_none(cache_service):
    result = await cache_service.get("nonexistent_key")
    assert result is None
```

### 2. Tests d'Intégration (endpoints API)

**Localisation** : `<service>/tests/integration/`

**Caractéristiques** :

- Testent les endpoints FastAPI
- Utilisent TestClient ou AsyncClient
- Peuvent utiliser vraie DB ou mock
- Vérifient contrats API

**Exemples** :

```python
# airport/tests/integration/test_airports_endpoints.py
async def test_get_airport_by_iata(async_client):
    response = await async_client.get("/api/v1/airports/CDG")
    assert response.status_code == 200
    assert response.json()["iata_code"] == "CDG"
```

### 3. Tests End-to-End (scénarios utilisateur)

**Localisation** : `tests/e2e/`

**Caractéristiques** :

- Testent workflows complets
- Nécessitent tous les services running (`docker-compose up`)
- Vérifient orchestration entre services
- Plus lents mais haute valeur

**Exemples** :

```python
# tests/e2e/test_assistant_flow.py
async def test_assistant_orchestrates_services(assistant_client):
    response = await assistant_client.post(
        "/assistant/answer",
        json={"prompt": "Quels vols partent de CDG ?"}
    )
    assert response.status_code == 200
    assert "CDG" in response.json()["answer"]
```

### 4. Tests de Performance (scripts bash)

**Localisation** : `tests/performance/`

**Caractéristiques** :

- Testent cache, coalescing, latence
- Scripts bash avec métriques Prometheus
- Génèrent rapports Grafana
- Valident optimisations

**Exemples** :

```bash
bash tests/performance/test_cache_isolated.sh
# Vérifie cache hit-rate > 70%
```

### 5. Scripts d'Exploration (documentation démarche)

**Localisation** : `<service>/tests/exploration/`

**Caractéristiques** :

- **PAS des tests automatisés**
- Scripts utilisés pendant développement
- Découverte empirique API externes
- Génération de mock data

**Exemples** :

```bash
python airport/tests/exploration/explore_api_structure.py
# Explore Aviationstack, génère JSON samples
```

## 🚀 Exécution des Tests

### Prérequis

```bash
# Pour tests unitaires et intégration
docker-compose up mongodb  # Seulement MongoDB

# Pour tests e2e
docker-compose up          # Tous les services
```

### Tests Unitaires

```bash
# Un service spécifique
cd airport && pytest tests/unit/ -v

# Tous les services
pytest airport/tests/unit/ flight/tests/unit/ -v

# Avec markers
pytest -m unit -v
```

### Tests d'Intégration

```bash
# Nécessite services running
pytest airport/tests/integration/ -v
pytest flight/tests/integration/ -v

# Tous les tests d'intégration
pytest */tests/integration/ -v
```

### Tests End-to-End

```bash
# Nécessite docker-compose up complet
pytest tests/e2e/ -v

# Avec marker
pytest -m e2e -v
```

### Tests de Performance

```bash
# Cache isolé
bash tests/performance/test_cache_isolated.sh

# Coalescing isolé
bash tests/performance/test_coalescing_isolated.sh

# Coalescing seul (simple)
bash tests/performance/test_coalescing.sh

# Cache + Coalescing ensemble
bash tests/performance/test_cache_and_coalescing.sh
```

### Exécuter tous les tests

```bash
# Option 1: Séquentiel (recommandé)
pytest */tests/unit/ -v           # Rapides
pytest */tests/integration/ -v    # Moyens
pytest tests/e2e/ -v              # Lents

# Option 2: Tout d'un coup (si services running)
pytest -v
```

## 📊 Couverture Actuelle

| Composant | Tests | Status |
|-----------|-------|--------|
| **Airport** | | |
| - Cache Service | ✅ Scripts perf | 100% |
| - Geocoding | ⏳ À créer | 0% |
| - Endpoints | ✅ 1 test | 20% |
| **Flight** | | |
| - Cache Service | ✅ Scripts perf | 100% |
| - Statistics | ⏳ À créer | 0% |
| - Endpoints | ⏳ À créer | 0% |
| **Coalescing** | ✅ Scripts perf | 100% |
| **E2E** | ⏳ À créer | 0% |
| **Global** | | **~40%** |

## 📝 Conventions de Nommage

### Fichiers de tests

```python
# Tests unitaires
test_{nom_module}.py              # Ex: test_cache_service.py

# Tests d'intégration
test_{nom_endpoint}_endpoints.py  # Ex: test_airports_endpoints.py

# Tests E2E
test_{scenario}.py                # Ex: test_assistant_flow.py

# Scripts exploration
explore_{module}.py               # Ex: explore_api_structure.py
```

### Fichiers de fixtures

```python
conftest.py           # Fixtures pytest
__init__.py           # Module marker
```

### Fichiers mock data

```python
{resource}_response_sample.json   # Ex: airport_response_sample.json
{resource}_mock_data.json         # Ex: flight_mock_data.json
```

## 🔧 Fixtures - Hiérarchie

### Niveau 1: Global (`tests/conftest.py`)

```python
@pytest.fixture
async def airport_client() -> AsyncClient:
    """Client HTTP pour service airport."""
    ...

@pytest.fixture
async def all_services() -> Dict[str, AsyncClient]:
    """Tous les clients pour tests e2e."""
    ...
```

### Niveau 2: Service (`airport/tests/conftest.py`)

```python
@pytest.fixture
async def async_client():
    """Client HTTP pour tester endpoints airport."""
    ...

@pytest.fixture
async def mongo_test_db():
    """DB MongoDB de test pour airport."""
    ...
```

### Niveau 3: Type de test (`airport/tests/unit/conftest.py`)

```python
@pytest.fixture
def mock_airport_api_response():
    """Mock réponse Aviationstack pour tests unit."""
    ...
```

## 🎨 Exemple de Test Complet

### Test Unitaire

```python
# airport/tests/unit/test_cache_service.py
import pytest
from services.cache_service import CacheService

@pytest.mark.unit
class TestCacheService:
    """Tests unitaires CacheService."""

    async def test_cache_hit(self, mock_cache_service):
        """Vérifie qu'un cache hit retourne les données."""
        # Arrange
        await mock_cache_service.set("key", {"data": "value"})

        # Act
        result = await mock_cache_service.get("key")

        # Assert
        assert result == {"data": "value"}
```

### Test d'Intégration

```python
# airport/tests/integration/test_airports_endpoints.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAirportsEndpoints:
    """Tests d'intégration endpoints /airports."""

    async def test_search_by_iata(self, async_client: AsyncClient):
        """Test GET /airports/{iata_code}."""
        # Act
        response = await async_client.get("/api/v1/airports/CDG")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["iata_code"] == "CDG"
        assert "name" in data
        assert "coordinates" in data
```

### Test E2E

```python
# tests/e2e/test_assistant_flow.py
import pytest

@pytest.mark.e2e
class TestAssistantOrchestration:
    """Tests e2e de l'assistant."""

    async def test_assistant_calls_airport_service(
        self,
        assistant_client,
        check_services_running
    ):
        """Test assistant → airport orchestration."""
        # Act
        response = await assistant_client.post(
            "/assistant/answer",
            json={"prompt": "Quels vols partent de CDG ?"}
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "answer" in result
        assert "CDG" in result["answer"]
        assert "data" in result
```

## 🐛 Debugging

### Pytest avec logs détaillés

```bash
# Tous les logs
pytest -v -s --log-cli-level=DEBUG

# Seulement erreurs
pytest -v --log-cli-level=ERROR

# Avec coverage
pytest -v --cov=airport --cov-report=html
```

### Scripts bash avec traces

```bash
# Mode debug
bash -x tests/performance/test_cache_isolated.sh

# Avec logs services
docker logs hello-mira-airport --tail 100 -f
```

### Vérifier services

```bash
# Status containers
docker-compose ps

# Healthcheck
curl http://localhost:8001/api/v1/health/liveness
curl http://localhost:8002/api/v1/health/liveness
curl http://localhost:8003/health

# MongoDB
docker exec -it hello-mira-mongodb mongosh
```

## ✅ Checklist Avant Restitution

- [x] Structure tests organisée (Best Practices 2025)
- [x] Tests performance cache/coalescing (scripts bash)
- [x] Hiérarchie conftest.py (global → service → type)
- [x] Documentation exploration/ (démarche empirique)
- [ ] Tests intégration endpoints (airport, flight)
- [ ] Tests e2e assistant orchestration
- [ ] Coverage > 70% sur services critiques

## 📚 Ressources

### Documentation Officielle

- **Pytest 2025** : <https://docs.pytest.org>
- **Pytest-asyncio** : <https://pytest-asyncio.readthedocs.io>
- **FastAPI Testing** : <https://fastapi.tiangolo.com/tutorial/testing/>
- **Motor (MongoDB async)** : <https://motor.readthedocs.io>

### Best Practices 2025

- **Test Organization** : <https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/>
- **Microservices Testing** : <https://python-microservices.github.io/tutorials/tutorial_testing/>
- **Fixtures Hierarchy** : <https://docs.pytest.org/en/stable/explanation/fixtures.html>

### Projet

- **Méthodologie** : Voir `CLAUDE.md` (Toujours Tester Avant de Coder)
- **Exploration Scripts** : Voir `airport/tests/exploration/README.md`
- **Architecture** : Voir `README.md` racine

## 🎓 Méthodologie - Démarche Empirique

Ce projet suit la méthodologie **"Toujours Tester Avant de Coder"** (voir `CLAUDE.md`).

### Workflow de Développement

1. **Explorer** : Scripts `explore_*.py` pour découvrir API externe
2. **Mocker** : Générer JSON samples dans `mocks/`
3. **Tester** : Créer tests unitaires avec mocks
4. **Coder** : Implémenter avec confiance
5. **Intégrer** : Tests d'intégration endpoints
6. **Orchestrer** : Tests e2e cross-services

### Exemple Concret

```bash
# 1. Explorer l'API Aviationstack
python airport/tests/exploration/explore_api_structure.py
# → Génère airport/tests/mocks/airport_response_sample.json

# 2. Créer tests unitaires avec mock
# airport/tests/unit/test_aviationstack_client.py utilise le mock

# 3. Implémenter le client
# airport/clients/aviationstack_client.py

# 4. Tester l'intégration
pytest airport/tests/integration/test_airports_endpoints.py
```

Cette approche garantit :

- ✅ Code validé empiriquement
- ✅ Tests réalistes (vrais formats API)
- ✅ Pas de surprises en production
- ✅ Documentation de la démarche

---

**Structure mise à jour** : 25 novembre 2024 (Best Practices 2025)
