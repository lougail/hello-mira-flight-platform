# 📚 API Reference - Hello Mira Flight Platform

> **Guide rapide des endpoints** pour éviter les erreurs d'appels API.
> Document créé le 26 novembre 2025.

---

## 📌 Table des Matières

- [URLs de Base](#urls-de-base)
- [Airport Service (Port 8001)](#airport-service-port-8001)
- [Flight Service (Port 8002)](#flight-service-port-8002)
- [Assistant Service (Port 8003)](#assistant-service-port-8003)
- [Monitoring](#monitoring)
- [Codes de Statut HTTP](#codes-de-statut-http)

---

## URLs de Base

| Service | URL Locale | URL Docker |
|---------|-----------|-----------|
| Airport | `http://localhost:8001/api/v1` | `http://airport:8001/api/v1` |
| Flight | `http://localhost:8002/api/v1` | `http://flight:8002/api/v1` |
| Assistant | `http://localhost:8003/api/v1` | `http://assistant:8003/api/v1` |

---

## Airport Service (Port 8001)

### Health Check Airport

```bash
GET /api/v1/health

curl http://localhost:8001/api/v1/health
```

**Réponse :**

```json
{
  "status": "healthy",
  "service": "airport",
  "version": "1.0.0"
}
```

---

### 1. Get Airport by IATA Code

```bash
GET /api/v1/airports/{iata_code}

curl http://localhost:8001/api/v1/airports/CDG
```

**Paramètres :**

- `iata_code` (path, required) : Code IATA 3 lettres (ex: CDG, JFK, LHR)

**Réponse 200 :**

```json
{
  "iata_code": "CDG",
  "airport_name": "Charles de Gaulle International Airport",
  "city_name": "Paris",
  "country_name": "France",
  "country_iso2": "FR",
  "latitude": 49.012798,
  "longitude": 2.55,
  "timezone": "Europe/Paris"
}
```

**Erreur 404 :**

```json
{
  "detail": "Airport not found with IATA code: XXX"
}
```

---

### 2. Search Airports by Location Name

⚠️ **ATTENTION** : Nécessite `name` ET `country_code` comme paramètres de query string.

```bash
GET /api/v1/airports/search?name={location}&country_code={country}

# Exemples corrects :
curl "http://localhost:8001/api/v1/airports/search?name=Lille&country_code=FR&limit=3"
curl "http://localhost:8001/api/v1/airports/search?name=Paris&country_code=FR"
curl "http://localhost:8001/api/v1/airports/search?name=Lyon&country_code=FR&limit=5&offset=0"
```

**Paramètres :**

- `name` (query, required) : Nom du lieu (min 2 caractères) - ville, région, etc.
- `country_code` (query, required) : Code pays ISO 2 lettres en MAJUSCULES (ex: FR, US, GB)
- `limit` (query, optional) : Nombre max de résultats (1-50, défaut: 10)
- `offset` (query, optional) : Décalage pour pagination (défaut: 0)

**Réponse 200 :**

```json
{
  "airports": [
    {
      "iata_code": "LIL",
      "airport_name": "Lesquin",
      "city_name": "Lille",
      "country_name": "France",
      "country_iso2": "FR",
      "latitude": 50.563332,
      "longitude": 3.086886,
      "timezone": "Europe/Paris"
    }
  ],
  "total": 1,
  "limit": 3,
  "offset": 0
}
```

---

### 3. Find Nearest Airport by GPS Coordinates

⚠️ **ATTENTION** : Nécessite `latitude`, `longitude` ET `country_code`.

```bash
GET /api/v1/airports/nearest-by-coords?latitude={lat}&longitude={lon}&country_code={country}

# Exemples corrects :
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=50.6292&longitude=3.0573&country_code=FR"
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=48.8566&longitude=2.3522&country_code=FR"
```

**Paramètres :**

- `latitude` (query, required) : Latitude GPS (-90 à 90)
- `longitude` (query, required) : Longitude GPS (-180 à 180)
- `country_code` (query, required) : Code pays ISO 2 lettres en MAJUSCULES

**Réponse 200 :**

```json
{
  "iata_code": "LIL",
  "airport_name": "Lesquin",
  "city_name": "Lille",
  "country_name": "France",
  "country_iso2": "FR",
  "latitude": 50.563332,
  "longitude": 3.086886,
  "timezone": "Europe/Paris"
}
```

---

### 4. Find Nearest Airport by Address

```bash
GET /api/v1/airports/nearest-by-address?address={address}&country_code={country}

# Exemples :
curl "http://localhost:8001/api/v1/airports/nearest-by-address?address=Lille,France&country_code=FR"
curl "http://localhost:8001/api/v1/airports/nearest-by-address?address=10%20rue%20de%20Rivoli%20Paris&country_code=FR"
```

**Paramètres :**

- `address` (query, required) : Adresse textuelle (min 3 caractères)
- `country_code` (query, required) : Code pays ISO 2 lettres en MAJUSCULES

**Note :** L'adresse est géocodée automatiquement via OpenStreetMap.

---

### 5. Get Departing Flights

```bash
GET /api/v1/airports/{iata_code}/departures

# Exemples :
curl http://localhost:8001/api/v1/airports/CDG/departures
curl "http://localhost:8001/api/v1/airports/CDG/departures?limit=5&offset=0"
```

**Paramètres :**

- `iata_code` (path, required) : Code IATA 3 lettres de l'aéroport
- `limit` (query, optional) : Nombre max de vols (1-100, défaut: 10)
- `offset` (query, optional) : Décalage pour pagination (défaut: 0)

**Réponse 200 :**

```json
{
  "flights": [
    {
      "flight_iata": "AF447",
      "flight_number": "447",
      "airline_name": "Air France",
      "airline_iata": "AF",
      "departure_airport": "CDG",
      "arrival_airport": "JFK",
      "flight_status": "scheduled",
      "scheduled_departure": "2025-11-26T10:30:00Z",
      "estimated_departure": null,
      "actual_departure": null,
      "scheduled_arrival": "2025-11-26T13:15:00Z",
      "estimated_arrival": null,
      "actual_arrival": null,
      "delay_minutes": 0
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0,
  "airport_iata": "CDG"
}
```

---

### 6. Get Arriving Flights

```bash
GET /api/v1/airports/{iata_code}/arrivals

# Exemples :
curl http://localhost:8001/api/v1/airports/CDG/arrivals
curl "http://localhost:8001/api/v1/airports/CDG/arrivals?limit=10"
```

**Paramètres :** Identiques à `/departures`

---

## Flight Service (Port 8002)

### Health Check Flight

```bash
GET /api/v1/health

curl http://localhost:8002/api/v1/health
```

---

### 1. Get Flight Status

```bash
GET /api/v1/flights/{flight_iata}

# Exemples :
curl http://localhost:8002/api/v1/flights/AF447
curl http://localhost:8002/api/v1/flights/BA117
curl http://localhost:8002/api/v1/flights/LH400
```

**Paramètres :**

- `flight_iata` (path, required) : Code IATA du vol (ex: AF447)

**Réponse 200 :**

```json
{
  "flight_iata": "AF447",
  "flight_number": "447",
  "airline_name": "Air France",
  "airline_iata": "AF",
  "departure_airport": "CDG",
  "arrival_airport": "JFK",
  "flight_status": "active",
  "scheduled_departure": "2025-11-26T10:30:00Z",
  "estimated_departure": "2025-11-26T10:45:00Z",
  "actual_departure": "2025-11-26T10:47:00Z",
  "scheduled_arrival": "2025-11-26T13:15:00Z",
  "estimated_arrival": "2025-11-26T13:33:00Z",
  "actual_arrival": null,
  "delay_minutes": 18
}
```

**Erreur 404 :**

```json
{
  "detail": "Flight not found with IATA code: AF9999"
}
```

---

### 2. Get Flight History

```bash
GET /api/v1/flights/{flight_iata}/history?start_date={start}&end_date={end}

# Exemples :
curl "http://localhost:8002/api/v1/flights/AF447/history?start_date=2025-11-01&end_date=2025-11-14"
curl "http://localhost:8002/api/v1/flights/BA117/history?start_date=2025-10-15&end_date=2025-11-15"
```

**Paramètres :**

- `flight_iata` (path, required) : Code IATA du vol
- `start_date` (query, required) : Date de début au format YYYY-MM-DD
- `end_date` (query, required) : Date de fin au format YYYY-MM-DD

**Limites :**

- Période max : 90 jours
- Données historiques : 3 mois en arrière (API Aviationstack Basic Plan)

**Réponse 200 :**

```json
{
  "flight_iata": "AF447",
  "flights": [
    {
      "flight_iata": "AF447",
      "flight_date": "2025-11-01",
      "flight_status": "landed",
      "delay_minutes": 15,
      "scheduled_departure": "2025-11-01T10:30:00Z",
      "actual_departure": "2025-11-01T10:45:00Z",
      "scheduled_arrival": "2025-11-01T13:15:00Z",
      "actual_arrival": "2025-11-01T13:30:00Z"
    }
  ],
  "total": 14,
  "start_date": "2025-11-01",
  "end_date": "2025-11-14"
}
```

---

### 3. Get Flight Statistics

```bash
GET /api/v1/flights/{flight_iata}/statistics?start_date={start}&end_date={end}

# Exemples :
curl "http://localhost:8002/api/v1/flights/AF447/statistics?start_date=2025-10-01&end_date=2025-11-14"
curl "http://localhost:8002/api/v1/flights/BA117/statistics?start_date=2025-09-01&end_date=2025-11-30"
```

**Paramètres :** Identiques à `/history`

**Réponse 200 :**

```json
{
  "flight_iata": "AF447",
  "total_flights": 45,
  "on_time_count": 32,
  "delayed_count": 11,
  "cancelled_count": 2,
  "on_time_rate": 71.1,
  "delay_rate": 24.4,
  "cancellation_rate": 4.4,
  "average_delay_minutes": 18.5,
  "max_delay_minutes": 127,
  "average_duration_minutes": 485,
  "start_date": "2025-10-01",
  "end_date": "2025-11-14"
}
```

---

## Assistant Service (Port 8003)

**Fonctionnalités clés :**

- Multi-langue automatique : Détecte la langue du prompt et répond dans la même langue (FR, EN, ES...)
- Enrichissement des données de vol avec pays de destination (`arrival_country`)
- 7 outils disponibles : 5 airport + 2 flight

### Health Check Assistant

```bash
GET /api/v1/health

curl http://localhost:8003/api/v1/health
```

---

### 1. Interpret Intent Only

```bash
POST /api/v1/assistant/interpret
Content-Type: application/json

# Exemple :
curl -X POST http://localhost:8003/api/v1/assistant/interpret \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Je suis sur le vol AF447, à quelle heure j'\''arrive ?"
  }'
```

**Body :**

```json
{
  "prompt": "Votre question en langage naturel"
}
```

**Réponse 200 :**

```json
{
  "intent": "get_flight_status",
  "entities": {
    "flight_iata": "AF447"
  },
  "confidence": 0.95
}
```

**Intentions supportées :**

- `get_flight_status` : Statut d'un vol
- `search_airports` : Recherche d'aéroports
- `get_departures` : Vols au départ
- `get_arrivals` : Vols à l'arrivée
- `get_nearest_airport` : Aéroport le plus proche
- `get_flight_statistics` : Statistiques d'un vol

---

### 2. Get Natural Language Answer (Full Orchestration)

```bash
POST /api/v1/assistant/answer
Content-Type: application/json

# Exemples :
curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Je suis sur le vol AF447, à quelle heure j'\''arrive ?"
  }'

curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Quels vols partent de CDG cet après-midi ?"
  }'

curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Trouve-moi l'\''aéroport le plus proche de Lille"
  }'

curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Donne-moi les statistiques du vol BA117"
  }'

# Exemples en anglais (multi-langue) :
curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the status of flight AF447?"
  }'

curl -X POST http://localhost:8003/api/v1/assistant/answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me flights to Japan from CDG"
  }'
```

**Body :**

```json
{
  "prompt": "Votre question en langage naturel"
}
```

**Réponse 200 :**

```json
{
  "answer": "Le vol AF447 est prévu à 13h15 (heure locale) avec un retard estimé de 18 minutes. L'arrivée estimée est maintenant à 13h33.",
  "data": {
    "flight_iata": "AF447",
    "flight_status": "active",
    "scheduled_arrival": "2025-11-26T13:15:00Z",
    "estimated_arrival": "2025-11-26T13:33:00Z",
    "delay_minutes": 18
  }
}
```

---

## Monitoring

### Prometheus Metrics

Tous les services exposent des métriques Prometheus sur `/metrics` :

```bash
# Airport metrics
curl http://localhost:8001/metrics

# Flight metrics
curl http://localhost:8002/metrics

# Assistant metrics
curl http://localhost:8003/metrics
```

### Grafana Dashboard

- URL : `http://localhost:3000`
- Login : `admin`
- Password : `admin`

---

## Codes de Statut HTTP

| Code | Signification | Cas d'usage |
|------|---------------|-------------|
| 200 | OK | Requête réussie |
| 400 | Bad Request | Paramètres invalides ou manquants |
| 404 | Not Found | Ressource non trouvée (aéroport, vol) |
| 500 | Internal Server Error | Erreur serveur |
| 503 | Service Unavailable | Service non configuré |

---

## ⚠️ Erreurs Fréquentes à Éviter

### 1. Endpoint `/airports/search`

❌ **FAUX** :

```bash
# NE PAS utiliser /airports/search/coordinates
curl http://localhost:8001/api/v1/airports/search/coordinates

# NE PAS oublier country_code
curl "http://localhost:8001/api/v1/airports/search?name=Lille"
```

✅ **CORRECT** :

```bash
# Utiliser les query params name ET country_code
curl "http://localhost:8001/api/v1/airports/search?name=Lille&country_code=FR&limit=3"
```

### 2. Endpoint `/airports/nearest-by-coords`

❌ **FAUX** :

```bash
# NE PAS utiliser comme path parameters
curl http://localhost:8001/api/v1/airports/nearest-by-coords/50.6292/3.0573
```

✅ **CORRECT** :

```bash
# Utiliser les query params
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=50.6292&longitude=3.0573&country_code=FR"
```

### 3. Dates pour Flight History/Statistics

❌ **FAUX** :

```bash
# Format de date invalide
curl "http://localhost:8002/api/v1/flights/AF447/history?start_date=01-11-2025&end_date=14-11-2025"
```

✅ **CORRECT** :

```bash
# Format YYYY-MM-DD requis
curl "http://localhost:8002/api/v1/flights/AF447/history?start_date=2025-11-01&end_date=2025-11-14"
```

---

## 📝 Notes Importantes

1. **Cache MongoDB** : Les services Airport et Flight utilisent un cache intelligent avec TTL configurable pour limiter les appels à l'API Aviationstack.

2. **Mode DEMO** : L'Assistant peut fonctionner en mode DEMO avec données mockées si `DEMO_MODE=true` dans `.env`.

3. **Limites API Aviationstack** :
   - Plan gratuit : 100 requêtes/mois
   - Historique : 3 mois en arrière max
   - Données temps réel limitées

4. **Pagination** : Tous les endpoints de liste supportent `limit` et `offset` pour la pagination.

5. **CORS** : Tous les services ont CORS activé pour accepter les requêtes cross-origin du frontend.

6. **Logs** : Tous les appels API sont loggés avec les paramètres pour faciliter le debugging.

---

**Document maintenu à jour au 26 novembre 2025**
**Version stack : FastAPI 0.122.0, PyMongo 4.15.4, LangGraph 1.0.3**
