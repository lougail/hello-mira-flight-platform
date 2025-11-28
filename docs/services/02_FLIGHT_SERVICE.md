# Microservice Flight - Documentation Technique Ultra-Détaillée

**Port** : 8002
**Partie du test** : Partie 2
**Statut** : ✅ COMPLET

---

## 📋 Table des Matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Différences avec le service Airport](#2-différences-avec-le-service-airport)
3. [Architecture des fichiers](#3-architecture-des-fichiers)
4. [Point d'entrée - main.py](#4-point-dentrée---mainpy)
5. [Endpoints API](#5-endpoints-api)
6. [Le FlightService - Logique métier](#6-le-flightservice---logique-métier)
7. [Modèles Domain](#7-modèles-domain)
8. [Stockage MongoDB - Historique](#8-stockage-mongodb---historique)
9. [Calcul des statistiques](#9-calcul-des-statistiques)
10. [Métriques Prometheus](#10-métriques-prometheus)
11. [Flux complet d'une requête](#11-flux-complet-dune-requête)
12. [Problèmes rencontrés et solutions](#12-problèmes-rencontrés-et-solutions)
13. [Points clés pour la présentation](#13-points-clés-pour-la-présentation)

---

## 1. Vue d'ensemble

### Objectif du service

Le microservice Flight permet de consulter les **vols individuels** : leur statut en temps réel, leur historique sur une période, et des statistiques agrégées. Il répond aux besoins de la **Partie 2** du test technique.

### Fonctionnalités implémentées

| Fonctionnalité | Endpoint | Description |
|----------------|----------|-------------|
| Statut temps réel | `GET /flights/{flight_iata}` | Statut actuel d'un vol (AF447, BA117...) |
| Historique | `GET /flights/{flight_iata}/history` | Historique sur une période (max 90 jours) |
| Statistiques | `GET /flights/{flight_iata}/statistics` | Taux ponctualité, retard moyen, etc. |
| Health check | `GET /api/v1/health` | État du service |

### Ce qui différencie Flight de Airport

| Aspect | Airport | Flight |
|--------|---------|--------|
| Focus | Aéroports + vols au départ/arrivée | Vols individuels |
| Stockage | Pas de stockage local | MongoDB pour l'historique |
| Calculs | Géocodage + Haversine | Statistiques agrégées |
| Données | Temps réel uniquement | Temps réel + Historique |

### Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI (async) |
| Client HTTP | httpx (async) |
| Validation | Pydantic v2 |
| Base de données | MongoDB (AsyncMongoClient) |
| Métriques | prometheus-client |

---

## 2. Différences avec le service Airport

### Pourquoi deux services distincts ?

**1. Séparation des responsabilités** :

- Airport = "Où sont les aéroports ?" + "Quels vols partent/arrivent ?"
- Flight = "Quel est le statut de CE vol ?" + "Historique de CE vol"

**2. Données différentes** :

- Airport : Données relativement statiques (aéroports) + listes de vols
- Flight : Données très dynamiques (statut temps réel) + accumulation historique

**3. Stockage** :

- Airport : Pas de stockage local (tout via Gateway)
- Flight : MongoDB pour accumuler l'historique des vols consultés

### Schéma d'interaction

```text
┌──────────────────┐
│     Frontend     │
└────────┬─────────┘
         │
    ┌────▼────┐
    │ Airport │ ────────► "Aéroports près de Lille" → CDG, LIL
    │  :8001  │ ────────► "Vols au départ de CDG" → [AF123, BA456]
    └────┬────┘
         │
    ┌────▼────┐
    │  Flight │ ────────► "Statut de AF123" → scheduled, 10h30
    │  :8002  │ ────────► "Historique AF123" → [jour1, jour2...]
    └─────────┘ ────────► "Stats AF123" → 85% à l'heure
```

---

## 3. Architecture des fichiers

```text
flight/                              # Racine du microservice
│
├── main.py                          # [368 lignes] Point d'entrée + MongoDB
├── Dockerfile                       # Image Docker
├── requirements.txt                 # Dépendances
├── __init__.py
│
├── api/                             # COUCHE PRÉSENTATION
│   ├── __init__.py
│   ├── responses.py                 # [264 lignes] Modèles de réponse API
│   └── routes/
│       ├── __init__.py
│       └── flights.py               # [400 lignes] 3 endpoints principaux
│
├── clients/                         # COUCHE INFRASTRUCTURE
│   ├── __init__.py
│   └── aviationstack_client.py      # [~300 lignes] Client HTTP → Gateway
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration
│
├── models/                          # COUCHE DOMAIN
│   ├── __init__.py
│   ├── enums.py                     # FlightStatus
│   └── domain/
│       ├── __init__.py
│       ├── airport.py               # (non utilisé ici)
│       └── flight.py                # [129 lignes] Modèle Flight complet
│
├── monitoring/
│   ├── __init__.py
│   └── metrics.py                   # [119 lignes] Métriques custom
│
├── services/
│   ├── __init__.py
│   └── flight_service.py            # [468 lignes] Logique métier + Stats
│
└── tests/
    └── ...
```

---

## 4. Point d'entrée - main.py

**Chemin** : `flight/main.py`
**Lignes** : 368

### Particularités par rapport à Airport

#### 1. Connexion MongoDB (lignes 85-109)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, flights_collection

    # Connexion MongoDB
    mongo_client = AsyncMongoClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=settings.mongodb_timeout
    )

    # Vérifie la connexion
    await mongo_client.admin.command('ping')

    # Collection pour l'historique
    mongo_db = mongo_client[settings.mongodb_database]
    flights_collection = mongo_db["flights"]

    # Crée des index pour les requêtes performantes
    await flights_collection.create_index("flight_iata")
    await flights_collection.create_index("flight_date")
    await flights_collection.create_index([("flight_iata", 1), ("flight_date", 1)])
```

**Pourquoi des index ?**

- `flight_iata` : Pour rechercher tous les vols d'un numéro donné
- `flight_date` : Pour filtrer par période
- Composite `(flight_iata, flight_date)` : Pour l'upsert sans doublons

#### 2. Service avec MongoDB (lignes 119-122)

```python
flight_service = FlightService(
    aviationstack_client=aviationstack_client,
    flights_collection=flights_collection  # ← Pas dans Airport !
)
```

Le FlightService reçoit la collection MongoDB pour stocker l'historique.

#### 3. Health check avec MongoDB (lignes 307-322)

```python
@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected" if mongo_client else "disconnected",  # ← Nouveau
        "gateway": settings.gateway_url
    }
```

---

## 5. Endpoints API

### Base URL : `/api/v1`

### 5.1 GET `/flights/{flight_iata}` - Statut temps réel

**Fichier** : `api/routes/flights.py:62-135`

**Description** : Récupère le statut actuel d'un vol.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| flight_iata | path | ✅ | Code vol (AF447, BA117) |

**Réponse** : `FlightResponse`

```json
{
  "flight_iata": "AF447",
  "flight_number": "447",
  "flight_date": "2025-11-28",
  "flight_status": "scheduled",
  "departure": {
    "scheduled_time": "2025-11-28T10:30:00+00:00",
    "estimated_time": "2025-11-28T10:30:00+00:00",
    "actual_time": null,
    "delay_minutes": 0,
    "terminal": "2F",
    "gate": "K42",
    "airport_iata": "CDG"
  },
  "arrival": {
    "scheduled_time": "2025-11-28T13:15:00+00:00",
    "estimated_time": null,
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

**Comportement spécial** : Chaque appel stocke le vol dans MongoDB pour construire l'historique.

> **💡 Découverte importante** : L'API Aviationstack retourne ~10 jours d'historique dans une seule requête (30-40 vols pour un vol quotidien comme AF1234). Cela signifie qu'un seul appel à cet endpoint peuple automatiquement MongoDB avec l'historique récent !

---

### 5.2 GET `/flights/{flight_iata}/history` - Historique

**Fichier** : `api/routes/flights.py:138-261`

**Description** : Récupère l'historique d'un vol sur une période.

**Paramètres** :

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| flight_iata | path | ✅ | Code vol |
| start_date | query | ✅ | Date début (YYYY-MM-DD) |
| end_date | query | ✅ | Date fin (YYYY-MM-DD) |

**Validation** :

- Dates au format `YYYY-MM-DD` (regex)
- `start_date` <= `end_date`
- Période max : 90 jours (limitation API AviationStack)

**Réponse** : `FlightHistoryResponse`

```json
{
  "flight_iata": "AF447",
  "flights": [
    { "flight_date": "2025-11-25", "flight_status": "landed", ... },
    { "flight_date": "2025-11-26", "flight_status": "landed", ... },
    { "flight_date": "2025-11-27", "flight_status": "scheduled", ... }
  ],
  "total": 3,
  "start_date": "2025-11-25",
  "end_date": "2025-11-27"
}
```

**Important** : L'historique provient de MongoDB. **Si MongoDB est vide pour ce vol, un appel API automatique est effectué** pour construire l'historique (~10 jours en une seule requête). Ce comportement "lazy loading" évite à l'utilisateur de devoir appeler manuellement `GET /flights/{flight_iata}` avant de consulter l'historique.

---

### 5.3 GET `/flights/{flight_iata}/statistics` - Statistiques

**Fichier** : `api/routes/flights.py:264-399`

**Description** : Calcule des statistiques agrégées sur une période.

**Paramètres** : Même que history.

**Réponse** : `FlightStatisticsResponse`

```json
{
  "flight_iata": "AF447",
  "total_flights": 30,
  "on_time_count": 22,
  "delayed_count": 6,
  "cancelled_count": 2,
  "on_time_rate": 73.33,
  "delay_rate": 20.0,
  "cancellation_rate": 6.67,
  "average_delay_minutes": 18.5,
  "max_delay_minutes": 45,
  "average_duration_minutes": 480.2,
  "start_date": "2025-10-01",
  "end_date": "2025-11-14"
}
```

**Statistiques calculées** :

- **on_time_rate** : % de vols avec retard ≤ 15 minutes
- **delay_rate** : % de vols avec retard > 15 minutes
- **cancellation_rate** : % de vols annulés
- **average_delay_minutes** : Retard moyen (uniquement vols en retard)
- **max_delay_minutes** : Retard maximum observé
- **average_duration_minutes** : Durée de vol moyenne

---

## 6. Le FlightService - Logique métier

**Chemin** : `flight/services/flight_service.py`
**Lignes** : 468

### Structure

```python
class FlightStatistics:
    """Dataclass pour les statistiques calculées."""
    flight_iata: str
    total_flights: int
    on_time_count: int
    delayed_count: int
    cancelled_count: int
    on_time_rate: float      # Calculé automatiquement
    delay_rate: float        # Calculé automatiquement
    cancellation_rate: float # Calculé automatiquement
    average_delay_minutes: Optional[float]
    max_delay_minutes: Optional[int]
    average_duration_minutes: Optional[float]

class FlightService:
    def __init__(self, aviationstack_client, flights_collection):
        self.client = aviationstack_client
        self.flights_collection = flights_collection  # MongoDB
```

### Méthode `get_flight_status()` (lignes 130-211)

```python
async def get_flight_status(self, flight_iata: str) -> Optional[Flight]:
    """
    1. Appelle le Gateway pour obtenir le vol
    2. Stocke TOUS les vols retournés dans MongoDB
    3. Retourne le vol le plus récent
    """
    flight_iata = flight_iata.upper()

    # Appelle le Gateway (cache géré par Gateway)
    flights = await self.client.get_flights(flight_iata=flight_iata, limit=100)

    if not flights:
        return None

    current_flight = flights[0]  # Le plus récent

    # Stocke TOUS les vols pour l'historique
    if self.flights_collection is not None:
        for flight in flights:
            # Upsert = Insert ou Update si existe déjà
            await self.flights_collection.update_one(
                {
                    "flight_iata": flight.flight_iata,
                    "flight_date": flight.flight_date
                },
                {
                    "$set": {
                        **flight.model_dump(),
                        "queried_at": datetime.utcnow()
                    }
                },
                upsert=True  # Clé : évite les doublons
            )

    return current_flight
```

**Point clé - Upsert** :

- `upsert=True` signifie : "insert si n'existe pas, update si existe"
- Clé unique : `(flight_iata, flight_date)`
- Évite les doublons si on consulte plusieurs fois le même vol

### Méthode `get_flight_history()` (lignes 217-344)

```python
async def get_flight_history(self, flight_iata, start_date, end_date) -> List[Flight]:
    """
    Récupère l'historique depuis MongoDB (pas l'API !).

    L'historique est construit au fil du temps via get_flight_status().
    """
    # Requête MongoDB
    query = {
        "flight_iata": flight_iata.upper(),
        "flight_date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }

    cursor = self.flights_collection.find(query).sort("flight_date", 1)
    flights_data = await cursor.to_list(length=None)

    # Convertit en objets Flight (en évitant les doublons)
    all_flights = []
    seen_dates = set()

    for data in flights_data:
        data.pop("_id", None)        # Retire l'ID MongoDB
        data.pop("queried_at", None) # Retire le timestamp de requête

        if data["flight_date"] in seen_dates:
            continue
        seen_dates.add(data["flight_date"])

        flight = Flight(**data)
        all_flights.append(flight)

    return all_flights
```

### Méthode `get_flight_statistics()` (lignes 350-467)

```python
async def get_flight_statistics(self, flight_iata, start_date, end_date):
    """
    1. Récupère l'historique
    2. Calcule les statistiques
    """
    flights = await self.get_flight_history(flight_iata, start_date, end_date)

    if not flights:
        return None

    # Comptage
    total = len(flights)
    on_time = 0
    delayed = 0
    cancelled = 0
    delays = []
    durations = []

    for flight in flights:
        if flight.flight_status == "cancelled":
            cancelled += 1
        elif flight.flight_status in ["active", "landed", "scheduled"]:
            delay_min = flight.departure.delay_minutes or 0

            if delay_min > 15:  # Définition : > 15 min = en retard
                delayed += 1
                delays.append(delay_min)
            else:
                on_time += 1

            # Calcul de la durée
            if flight.departure.scheduled_time and flight.arrival.scheduled_time:
                dep_time = datetime.fromisoformat(flight.departure.scheduled_time)
                arr_time = datetime.fromisoformat(flight.arrival.scheduled_time)
                duration = (arr_time - dep_time).total_seconds() / 60
                if duration > 0:
                    durations.append(duration)

    # Moyennes (utilise statistics.mean)
    avg_delay = mean(delays) if delays else None
    max_delay = max(delays) if delays else None
    avg_duration = mean(durations) if durations else None

    return FlightStatistics(
        flight_iata=flight_iata,
        total_flights=total,
        on_time_count=on_time,
        delayed_count=delayed,
        cancelled_count=cancelled,
        average_delay_minutes=avg_delay,
        max_delay_minutes=max_delay,
        average_duration_minutes=avg_duration
    )
```

---

## 7. Modèles Domain

### Flight (`models/domain/flight.py`)

**Structure hiérarchique** :

```text
Flight
├── flight_iata: "AF447"
├── flight_number: "447"
├── flight_date: "2025-11-28"
├── flight_status: "scheduled"
├── departure: Departure
│   ├── airport_iata: "CDG"
│   ├── airport_name: "Charles de Gaulle"
│   ├── scheduled_time: "2025-11-28T10:30:00+00:00"
│   ├── estimated_time: ...
│   ├── actual_time: ...
│   ├── delay_minutes: 0
│   ├── terminal: "2F"
│   └── gate: "K42"
├── arrival: Arrival
│   └── (même structure que Departure)
├── airline_name: "Air France"
├── airline_iata: "AF"
└── airline_icao: "AFR"
```

### Différence avec le modèle Airport/Flight

| Service | Modèle Flight |
|---------|---------------|
| Airport | Simplifié (FlightSchedule avec scheduled, estimated, actual) |
| Flight | Complet (Departure/Arrival avec terminal, gate, airport_name) |

**Pourquoi ?** Le service Flight a besoin de plus de détails pour :

- Afficher les terminaux et portes
- Calculer les durées de vol
- Stocker l'historique complet

---

## 8. Stockage MongoDB - Historique

### Schéma du document

```json
{
  "_id": ObjectId("..."),
  "flight_iata": "AF447",
  "flight_number": "447",
  "flight_date": "2025-11-28",
  "flight_status": "landed",
  "departure": {
    "airport_iata": "CDG",
    "airport_name": "Charles de Gaulle",
    "scheduled_time": "2025-11-28T10:30:00+00:00",
    "estimated_time": "2025-11-28T10:45:00+00:00",
    "actual_time": "2025-11-28T10:42:00+00:00",
    "delay_minutes": 12,
    "terminal": "2F",
    "gate": "K42"
  },
  "arrival": { ... },
  "airline_name": "Air France",
  "airline_iata": "AF",
  "airline_icao": "AFR",
  "queried_at": ISODate("2025-11-28T15:30:00Z")
}
```

### Index créés

```python
await flights_collection.create_index("flight_iata")
await flights_collection.create_index("flight_date")
await flights_collection.create_index([("flight_iata", 1), ("flight_date", 1)])
```

| Index | Usage |
|-------|-------|
| `flight_iata` | Rechercher tous les vols d'un numéro |
| `flight_date` | Filtrer par période |
| `(flight_iata, flight_date)` | Upsert sans doublons |

### Stratégie d'accumulation

```text
Jour 1 : GET /flights/AF447
         → Stocke AF447 du 2025-11-25, 2025-11-26, 2025-11-27

Jour 2 : GET /flights/AF447
         → Stocke AF447 du 2025-11-26, 2025-11-27, 2025-11-28
         → Les jours existants sont mis à jour (upsert)

Jour 3 : GET /flights/AF447/history?start_date=2025-11-25&end_date=2025-11-28
         → Retourne 4 vols depuis MongoDB
```

---

## 9. Calcul des statistiques

### Définitions

| Métrique | Définition |
|----------|------------|
| **À l'heure** | Retard ≤ 15 minutes |
| **En retard** | Retard > 15 minutes |
| **Annulé** | `flight_status == "cancelled"` |
| **Durée** | arrival.scheduled_time - departure.scheduled_time |

### Algorithme

```python
for flight in flights:
    if flight.flight_status == "cancelled":
        cancelled += 1
    else:
        delay = flight.departure.delay_minutes or 0
        if delay > 15:
            delayed += 1
            delays.append(delay)  # Pour la moyenne
        else:
            on_time += 1

        # Durée = arrivée - départ
        if departure.scheduled_time and arrival.scheduled_time:
            duration = (arr_time - dep_time).seconds / 60
            durations.append(duration)

# Calcul des taux
on_time_rate = on_time / total * 100
delay_rate = delayed / total * 100
cancellation_rate = cancelled / total * 100

# Moyennes
average_delay = mean(delays) if delays else None
average_duration = mean(durations) if durations else None
```

---

## 10. Métriques Prometheus

**Fichier** : `flight/monitoring/metrics.py`

### Métriques définies

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `flight_lookups_total` | Counter | type, status | Recherches de vols |
| `flight_lookup_latency_seconds` | Histogram | type | Latence des recherches |
| `flight_mongodb_operations_total` | Counter | operation, status | Opérations MongoDB |
| `flight_flights_stored_total` | Counter | - | Vols stockés |
| `flight_history_flights_count` | Histogram | - | Vols par historique |
| `flight_statistics_calculated_total` | Counter | - | Stats calculées |
| `flight_statistics_flights_analyzed` | Histogram | - | Vols analysés |
| `flight_last_on_time_rate` | Gauge | flight_iata | Taux ponctualité |
| `flight_last_delay_rate` | Gauge | flight_iata | Taux retard |
| `flight_last_average_delay_minutes` | Gauge | flight_iata | Retard moyen |

### Particularité : Gauges par vol

```python
# Après calcul des statistiques
last_on_time_rate.labels(flight_iata="AF447").set(85.5)
last_delay_rate.labels(flight_iata="AF447").set(10.0)
last_average_delay.labels(flight_iata="AF447").set(22.3)
```

Ces gauges permettent de voir les dernières statistiques de chaque vol dans Grafana.

---

## 11. Flux complet d'une requête

### Exemple : GET /flights/AF447/statistics?start_date=2025-11-01&end_date=2025-11-28

```text
1. [Client HTTP]
   │
   ▼
2. [FastAPI Router] api/routes/flights.py:264
   - Valide flight_iata (min 2, max 10 chars)
   - Valide dates (regex YYYY-MM-DD)
   - Vérifie start_date <= end_date
   │
   ▼
3. [FlightService.get_flight_statistics()] services/flight_service.py:350
   │
   ▼
4. [FlightService.get_flight_history()] services/flight_service.py:217
   │
   ▼
5. [MongoDB Query]
   - Collection: flights
   - Query: { flight_iata: "AF447", flight_date: { $gte: "2025-11-01", $lte: "2025-11-28" } }
   - Sort: flight_date ascending
   │
   ▼
6. [FlightService] Conversion documents → objets Flight
   - Retire _id et queried_at
   - Déduplique par flight_date
   │
   ▼
7. [FlightService] Calcul des statistiques
   - Parcourt chaque vol
   - Compte on_time, delayed, cancelled
   - Calcule moyennes
   │
   ▼
8. [Métriques Prometheus]
   - statistics_calculated.inc()
   - last_on_time_rate.labels(flight_iata="AF447").set(...)
   │
   ▼
9. [FastAPI Router]
   - Crée FlightStatisticsResponse
   - Retourne JSON
```

---

## 12. Problèmes rencontrés et solutions

### 1. Pas d'historique au premier appel

**Problème** : L'historique vient de MongoDB, mais au premier appel la base est vide.

**Solution** : L'historique se construit au fil du temps.

- Chaque appel à `GET /flights/{iata}` stocke les vols retournés
- L'API Aviationstack retourne ~2-3 jours de vols à chaque appel
- Au fil des consultations, l'historique s'enrichit

**Message pour l'utilisateur** :

```text
"Aucun historique pour AF447. Consultez d'abord GET /flights/AF447 pour accumuler des données."
```

### 2. Doublons dans MongoDB

**Problème** : Consulter le même vol plusieurs fois = doublons.

**Solution** : Upsert avec clé composite.

```python
await collection.update_one(
    {"flight_iata": flight.flight_iata, "flight_date": flight.flight_date},
    {"$set": {...}},
    upsert=True
)
```

### 3. Vols sans retard enregistré

**Problème** : `flight.departure.delay_minutes` peut être `None`.

**Solution** : Traiter `None` comme "à l'heure".

```python
delay_min = flight.departure.delay_minutes or 0
if delay_min > 15:
    delayed += 1
else:
    on_time += 1  # None = pas de retard
```

### 4. Dates invalides

**Problème** : L'utilisateur peut envoyer des dates mal formatées.

**Solution** : Validation double.

```python
# 1. Regex dans Query()
start_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$")

# 2. Parse explicite dans le handler
try:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
except ValueError:
    raise HTTPException(400, "Invalid date format")
```

### 5. MongoDB non disponible

**Problème** : Si MongoDB est down, l'historique ne fonctionne pas.

**Solution** : Graceful degradation.

```python
if self.flights_collection is None:
    logger.warning("MongoDB non disponible, historique vide")
    return []
```

Le service continue à fonctionner, mais l'historique est vide.

---

## 13. Points clés pour la présentation

### Ce qui différencie ce service

1. **Accumulation d'historique** : Pattern intelligent où chaque consultation enrichit la base
2. **Upsert MongoDB** : Évite les doublons tout en mettant à jour les données
3. **Statistiques calculées** : Vrais calculs métier (taux, moyennes)
4. **Graceful degradation** : Fonctionne même si MongoDB est down

### Questions potentielles du jury

**Q: Pourquoi l'historique vient de MongoDB et pas de l'API ?**
> R: L'API Aviationstack ne permet pas de requêter l'historique arbitraire. On accumule les données au fil du temps pour construire notre propre historique.

**Q: Comment définissez-vous "en retard" ?**
> R: Un vol est considéré en retard si le delay_minutes est > 15 minutes. C'est le standard industrie.

**Q: Que se passe-t-il si on consulte l'historique sans avoir fait d'appels préalables ?**
> R: On retourne une liste vide avec un message suggérant de consulter d'abord le statut du vol.

**Q: Pourquoi upsert plutôt qu'insert ?**
> R: Pour éviter les doublons. Si on consulte AF447 deux jours de suite, les vols communs sont mis à jour plutôt que dupliqués.

**Q: Comment gérez-vous les vols annulés dans les statistiques ?**
> R: Ils sont comptés séparément (cancelled_count) et n'affectent pas on_time_count ni delayed_count.

### Schéma à montrer

```text
┌─────────────────────────────────────────────────────────────┐
│                    Service Flight                            │
├─────────────────────────────────────────────────────────────┤
│  GET /flights/{iata}        │  GET /flights/{iata}/history  │
│         ↓                   │             ↓                  │
│  Gateway → Aviationstack    │       MongoDB Query            │
│         ↓                   │             ↓                  │
│  Stocke dans MongoDB ←──────┼─────── Lit depuis MongoDB      │
│         ↓                   │             ↓                  │
│  Retourne vol actuel        │  Retourne liste de vols        │
├─────────────────────────────┴───────────────────────────────┤
│              GET /flights/{iata}/statistics                  │
│                          ↓                                   │
│                   get_flight_history()                       │
│                          ↓                                   │
│              Calcul on_time/delayed/cancelled                │
│                          ↓                                   │
│              Retourne FlightStatisticsResponse               │
└─────────────────────────────────────────────────────────────┘
```
