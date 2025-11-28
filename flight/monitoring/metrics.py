"""
Metriques Prometheus pour le service Flight.

Metriques custom pour le monitoring du service :
- Recherches de vols (status, history, statistics)
- Operations MongoDB (stockage historique)
- Statistiques calculees

Architecture :
- Les metriques API Aviationstack restent dans le Gateway
- Ce fichier ajoute des metriques specifiques au service Flight
"""

from prometheus_client import Counter, Histogram, Gauge

# ============================================================================
# METRIQUES RECHERCHES DE VOLS
# ============================================================================

flight_lookups = Counter(
    'flight_lookups_total',
    'Nombre total de recherches de vols',
    ['type', 'status']  # type: status, history, statistics / status: success, not_found, error
)

flight_lookup_latency = Histogram(
    'flight_lookup_latency_seconds',
    'Latence des recherches de vols en secondes',
    ['type'],  # type: status, history, statistics
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0)
)

# ============================================================================
# METRIQUES MONGODB (HISTORIQUE)
# ============================================================================

mongodb_operations = Counter(
    'flight_mongodb_operations_total',
    'Nombre d\'operations MongoDB',
    ['operation', 'status']  # operation: store, retrieve / status: success, error
)

flights_stored = Counter(
    'flight_flights_stored_total',
    'Nombre de vols stockes dans l\'historique MongoDB',
    []
)

history_flights_count = Histogram(
    'flight_history_flights_count',
    'Nombre de vols retournes par requete historique',
    [],
    buckets=(0, 1, 5, 10, 20, 30, 50, 100)
)

# ============================================================================
# METRIQUES STATISTIQUES
# ============================================================================

statistics_calculated = Counter(
    'flight_statistics_calculated_total',
    'Nombre de calculs de statistiques effectues',
    []
)

statistics_flights_analyzed = Histogram(
    'flight_statistics_flights_analyzed',
    'Nombre de vols analyses par calcul de statistiques',
    [],
    buckets=(0, 1, 5, 10, 20, 30, 50, 100)
)

# Metriques de performance des vols (dernieres statistiques calculees)
last_on_time_rate = Gauge(
    'flight_last_on_time_rate',
    'Dernier taux de ponctualite calcule (%)',
    ['flight_iata']
)

last_delay_rate = Gauge(
    'flight_last_delay_rate',
    'Dernier taux de retard calcule (%)',
    ['flight_iata']
)

last_average_delay = Gauge(
    'flight_last_average_delay_minutes',
    'Dernier retard moyen calcule (minutes)',
    ['flight_iata']
)

# ============================================================================
# QUERIES PROMQL UTILES
# ============================================================================

"""
Exemples de queries Prometheus :

1. Recherches de vols par type et par minute :
   sum(rate(flight_lookups_total[1m])) by (type) * 60

2. Latence P95 des recherches :
   histogram_quantile(0.95, rate(flight_lookup_latency_seconds_bucket[5m]))

3. Taux de succes des recherches :
   sum(rate(flight_lookups_total{status="success"}[5m])) / sum(rate(flight_lookups_total[5m])) * 100

4. Vols stockes par minute :
   rate(flight_flights_stored_total[1m]) * 60

5. Moyenne de vols par requete historique :
   rate(flight_history_flights_count_sum[5m]) / rate(flight_history_flights_count_count[5m])

6. Taux de ponctualite moyen :
   avg(flight_last_on_time_rate)

7. Vols les plus en retard :
   topk(5, flight_last_delay_rate)
"""