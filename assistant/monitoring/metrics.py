"""
Metriques Prometheus pour le service Assistant.

Metriques custom pour le monitoring de l'IA :
- Appels LLM (Mistral AI)
- Latence des appels LLM
- Intentions detectees
- Appels aux tools
- Erreurs
"""

from prometheus_client import Counter, Histogram, Gauge

# ============================================================================
# METRIQUES LLM (Mistral AI)
# ============================================================================

llm_calls = Counter(
    'assistant_llm_calls_total',
    'Nombre total d\'appels au LLM Mistral',
    ['node', 'model']  # node: interpret, reinterpret, respond
)

llm_latency = Histogram(
    'assistant_llm_latency_seconds',
    'Latence des appels LLM en secondes',
    ['node', 'model'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)
)

llm_errors = Counter(
    'assistant_llm_errors_total',
    'Nombre d\'erreurs LLM',
    ['node', 'error_type']  # error_type: timeout, rate_limit, api_error, etc.
)

# ============================================================================
# METRIQUES INTENTIONS
# ============================================================================

intent_detected = Counter(
    'assistant_intent_detected_total',
    'Nombre d\'intentions detectees par type',
    ['intent']  # intent: get_flight_status, get_departures, search_airports, etc.
)

# ============================================================================
# METRIQUES TOOLS
# ============================================================================

tool_calls = Counter(
    'assistant_tool_calls_total',
    'Nombre d\'appels aux tools',
    ['tool', 'status']  # tool: get_flight_status_tool, etc. / status: success, error
)

tool_latency = Histogram(
    'assistant_tool_latency_seconds',
    'Latence des appels aux tools en secondes',
    ['tool'],
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0)
)

tool_errors = Counter(
    'assistant_tool_errors_total',
    'Nombre d\'erreurs d\'execution des tools',
    ['tool', 'error_type']
)

# ============================================================================
# METRIQUES GRAPH / WORKFLOW
# ============================================================================

graph_iterations = Histogram(
    'assistant_graph_iterations',
    'Nombre d\'iterations ReAct par requete',
    [],
    buckets=(1, 2, 3, 4, 5)
)

# ============================================================================
# QUERIES PROMQL UTILES
# ============================================================================

"""
Exemples de queries Prometheus :

1. Appels LLM par minute :
   rate(assistant_llm_calls_total[1m]) * 60

2. Latence LLM P95 :
   histogram_quantile(0.95, rate(assistant_llm_latency_seconds_bucket[5m]))

3. Distribution des intentions :
   sum(rate(assistant_intent_detected_total[5m])) by (intent)

4. Taux d'erreur LLM :
   rate(assistant_llm_errors_total[5m]) / rate(assistant_llm_calls_total[5m]) * 100

5. Tools les plus utilises :
   topk(5, sum(rate(assistant_tool_calls_total[5m])) by (tool))

6. Latence moyenne des tools :
   rate(assistant_tool_latency_seconds_sum[5m]) / rate(assistant_tool_latency_seconds_count[5m])
"""
