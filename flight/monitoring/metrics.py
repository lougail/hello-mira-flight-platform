"""
Métriques Prometheus custom pour le monitoring de performance.

Conformément à la Partie 3 - Optimisation du test technique :
- ✅ Latence : fournie par prometheus-fastapi-instrumentator
- ✅ Nombre d'appels HTTP : fourni par prometheus-fastapi-instrumentator
- ✅ Hit-rate cache : métriques custom ci-dessous
- ✅ Nombre d'appels API Aviationstack : métriques custom ci-dessous
"""

from prometheus_client import Counter

# ============================================================================
# MÉTRIQUES CACHE MONGODB
# ============================================================================

cache_hits = Counter(
    'cache_hits_total',
    'Nombre total de cache hits (données trouvées en cache)',
    ['service', 'cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Nombre total de cache misses (données non trouvées, appel API requis)',
    ['service', 'cache_type']
)

cache_expired = Counter(
    'cache_expired_total',
    'Nombre total de clés expirées (TTL dépassé)',
    ['service', 'cache_type']
)

# ============================================================================
# MÉTRIQUES API EXTERNE AVIATIONSTACK
# ============================================================================

api_calls = Counter(
    'aviationstack_api_calls_total',
    'Nombre total d\'appels à l\'API Aviationstack (consommation quota)',
    ['service', 'endpoint', 'status']
)

coalesced_requests = Counter(
    'coalesced_requests_total',
    'Nombre total de requêtes coalescées (requêtes identiques fusionnées)',
    ['service', 'endpoint']
)

# ============================================================================
# QUERIES PROMQL UTILES (pour documentation)
# ============================================================================

"""
Exemples de queries Prometheus pour exploiter ces métriques :

1. Hit-rate du cache (%) :
   sum(rate(cache_hits_total{service="flight"}[5m])) /
   (sum(rate(cache_hits_total{service="flight"}[5m])) + sum(rate(cache_misses_total{service="flight"}[5m]))) * 100

2. Nombre d'appels API Aviationstack par minute :
   rate(aviationstack_api_calls_total{service="flight"}[1m]) * 60

3. Total cache misses sur la dernière heure :
   increase(cache_misses_total{service="flight"}[1h])

4. Taux de clés expirées :
   rate(cache_expired_total{service="flight"}[5m])

5. Taux de coalescing (% de requêtes fusionnées) :
   sum(rate(coalesced_requests_total{service="flight"}[5m])) /
   (sum(rate(coalesced_requests_total{service="flight"}[5m])) + sum(rate(aviationstack_api_calls_total{service="flight"}[5m]))) * 100
"""
