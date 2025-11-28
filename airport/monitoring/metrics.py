"""
Metriques Prometheus pour le service Airport.

Metriques custom pour le monitoring du service :
- Recherches d'aeroports (IATA, nom, proximite)
- Geocodage (appels Nominatim)
- Vols (departs, arrivees)

Architecture :
- Les metriques API Aviationstack restent dans le Gateway
- Ce fichier ajoute des metriques specifiques au service Airport
"""

from prometheus_client import Counter, Histogram, Gauge

# ============================================================================
# METRIQUES RECHERCHES D'AEROPORTS
# ============================================================================

airport_lookups = Counter(
    'airport_lookups_total',
    'Nombre total de recherches d\'aeroports',
    ['type', 'status']  # type: iata, name, nearest, nearest_by_address, location / status: success, not_found, error
)

airport_lookup_latency = Histogram(
    'airport_lookup_latency_seconds',
    'Latence des recherches d\'aeroports en secondes',
    ['type'],
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0)
)

airports_found = Histogram(
    'airport_airports_found',
    'Nombre d\'aeroports trouves par recherche',
    ['type'],  # type: name, location
    buckets=(0, 1, 5, 10, 20, 50, 100)
)

# ============================================================================
# METRIQUES GEOCODAGE (NOMINATIM)
# ============================================================================

geocoding_calls = Counter(
    'airport_geocoding_calls_total',
    'Nombre total d\'appels au service de geocodage Nominatim',
    ['status']  # status: success, not_found, error
)

geocoding_latency = Histogram(
    'airport_geocoding_latency_seconds',
    'Latence des appels de geocodage en secondes',
    [],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0, 10.0)
)

# ============================================================================
# METRIQUES VOLS (DEPARTS / ARRIVEES)
# ============================================================================

flight_queries = Counter(
    'airport_flight_queries_total',
    'Nombre de requetes de vols (departs/arrivees)',
    ['type', 'status']  # type: departures, arrivals / status: success, error
)

flight_query_latency = Histogram(
    'airport_flight_query_latency_seconds',
    'Latence des requetes de vols en secondes',
    ['type'],  # type: departures, arrivals
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0)
)

flights_returned = Histogram(
    'airport_flights_returned',
    'Nombre de vols retournes par requete',
    ['type'],  # type: departures, arrivals
    buckets=(0, 1, 5, 10, 20, 50, 100)
)

# ============================================================================
# METRIQUES CALCUL DE DISTANCE
# ============================================================================

distance_calculations = Counter(
    'airport_distance_calculations_total',
    'Nombre de calculs de distance effectues',
    []
)

nearest_airport_distance = Gauge(
    'airport_last_nearest_distance_km',
    'Distance du dernier aeroport le plus proche trouve (km)',
    []
)

# ============================================================================
# QUERIES PROMQL UTILES
# ============================================================================

"""
Exemples de queries Prometheus :

1. Recherches d'aeroports par type :
   sum(rate(airport_lookups_total[5m])) by (type)

2. Latence P95 des recherches :
   histogram_quantile(0.95, rate(airport_lookup_latency_seconds_bucket[5m]))

3. Taux de succes du geocodage :
   sum(rate(airport_geocoding_calls_total{status="success"}[5m])) /
   sum(rate(airport_geocoding_calls_total[5m])) * 100

4. Vols par type (departs vs arrivees) :
   sum(rate(airport_flight_queries_total[5m])) by (type)

5. Nombre moyen d'aeroports trouves par recherche de nom :
   rate(airport_airports_found_sum{type="name"}[5m]) /
   rate(airport_airports_found_count{type="name"}[5m])

6. Latence moyenne du geocodage :
   rate(airport_geocoding_latency_seconds_sum[5m]) /
   rate(airport_geocoding_latency_seconds_count[5m])

7. Distance moyenne de l'aeroport le plus proche :
   airport_last_nearest_distance_km
"""