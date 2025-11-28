"""
Metriques Prometheus pour l'API Gateway.

Centralise toutes les metriques liees aux appels Aviationstack :
- Cache hits/misses
- Appels API (succes/erreur)
- Request coalescing
- Circuit breaker
- Rate limiting
"""

from prometheus_client import Counter, Gauge

# ============================================================================
# METRIQUES CACHE
# ============================================================================

cache_hits = Counter(
    'gateway_cache_hits_total',
    'Nombre total de cache hits (donnees trouvees en cache)',
    ['endpoint']
)

cache_misses = Counter(
    'gateway_cache_misses_total',
    'Nombre total de cache misses (appel API requis)',
    ['endpoint']
)

# ============================================================================
# METRIQUES API AVIATIONSTACK
# ============================================================================

api_calls = Counter(
    'gateway_api_calls_total',
    'Nombre total d\'appels a l\'API Aviationstack',
    ['endpoint', 'status']  # status: success, error, rate_limited
)

# ============================================================================
# METRIQUES REQUEST COALESCING
# ============================================================================

coalesced_requests = Counter(
    'gateway_coalesced_requests_total',
    'Nombre de requetes coalescees (fusionnees avec une requete en cours)',
    ['endpoint']
)

# ============================================================================
# METRIQUES CIRCUIT BREAKER
# ============================================================================

circuit_breaker_state = Gauge(
    'gateway_circuit_breaker_state',
    'Etat du circuit breaker (0=closed, 1=half_open, 2=open)',
    []
)

# ============================================================================
# METRIQUES RATE LIMITING
# ============================================================================

rate_limit_used = Gauge(
    'gateway_rate_limit_used',
    'Nombre d\'appels API utilises ce mois',
    []
)

rate_limit_remaining = Gauge(
    'gateway_rate_limit_remaining',
    'Nombre d\'appels API restants ce mois',
    []
)

# ============================================================================
# QUERIES PROMQL UTILES
# ============================================================================

"""
Exemples de queries Prometheus :

1. Hit-rate du cache (%) :
   gateway_cache_hits_total / (gateway_cache_hits_total + gateway_cache_misses_total) * 100

2. Appels API par minute :
   rate(gateway_api_calls_total[1m]) * 60

3. Taux de coalescing (%) :
   sum(rate(gateway_coalesced_requests_total[5m])) /
   (sum(rate(gateway_coalesced_requests_total[5m])) + sum(rate(gateway_api_calls_total[5m]))) * 100

4. Circuit breaker ouvert :
   gateway_circuit_breaker_state == 2

5. Quota API restant :
   gateway_rate_limit_remaining
"""
