# 📊 Monitoring et Observabilité - Documentation Technique

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Monitoring](#architecture-monitoring)
3. [Prometheus](#prometheus)
4. [Grafana](#grafana)
5. [Métriques Disponibles](#métriques-disponibles)
6. [Queries PromQL](#queries-promql)
7. [Alertes](#alertes)
8. [Configuration](#configuration)

---

## Vue d'Ensemble

Le système de monitoring utilise le stack **Prometheus + Grafana** :

| Composant | Rôle | Port |
|-----------|------|------|
| **Prometheus** | Collecte et stockage des métriques | 9090 |
| **Grafana** | Visualisation et alertes | 3000 |

### Métriques Collectées

- **HTTP** : Latence, status codes, throughput (via prometheus_fastapi_instrumentator)
- **Gateway** : Cache hits/misses, API calls, coalescing, circuit breaker
- **Rate Limit** : Utilisation du quota API mensuel

---

## Architecture Monitoring

```text
┌─────────────────────────────────────────────────────────────────┐
│                         GRAFANA                                 │
│                        Port 3000                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Dashboard: Hello Mira Metrics              │    │
│  │                                                         │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │ Cache Hit    │ │ API Calls    │ │ Rate Limit   │     │    │
│  │  │ Rate: 65%    │ │ /min: 12     │ │ Used: 1234   │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  │                                                         │    │
│  │  ┌────────────────────────────────────────────────────┐ │    │
│  │  │          HTTP Latency (p95) Over Time              │ │    │
│  │  │  ───────────────────────────────────────────────── │ │    │
│  │  │  150ms ┤          ╱╲                               │ │    │
│  │  │  100ms ┤     ╱╲  ╱  ╲     ╱╲                       │ │    │
│  │  │   50ms ┤ ───╱  ╲╱    ╲───╱  ╲───                   │ │    │
│  │  └────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                    │
│                            │ PromQL Queries                     │
│                            ▼                                    │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                       PROMETHEUS                                 │
│                        Port 9090                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                   Time Series DB                        │     │
│  │                                                         │     │
│  │  gateway_cache_hits_total{endpoint="airports"} 89       │     │
│  │  gateway_cache_misses_total{endpoint="airports"} 34     │     │
│  │  gateway_api_calls_total{endpoint="airports"} 34        │     │
│  │  gateway_rate_limit_used 1234                           │     │
│  │  http_request_duration_seconds_bucket{...}              │     │
│  └─────────────────────────────────────────────────────────┘     │
│                            │                                     │
│                            │ Scrape /metrics                     │
│                            │ every 10-15s                        │
└────────────────────────────┼────────────────────────────────────-┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Gateway    │    │   Airport    │    │   Flight     │
│   :8004      │    │   :8001      │    │   :8002      │
│  /metrics    │    │  /metrics    │    │  /metrics    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│             prometheus_fastapi_instrumentator                  │
│                                                                │
│  Expose automatiquement :                                      │
│  • http_request_duration_seconds (histogram)                   │
│  • http_requests_total (counter)                               │
│  • Plus les métriques custom du Gateway                        │
└────────────────────────────────────────────────────────────────┘
```

---

## Prometheus

### Configuration

**Fichier** : `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s      # Scrape metrics every 15 seconds
  evaluation_interval: 15s  # Evaluate rules every 15 seconds

  external_labels:
    monitor: 'hello-mira-platform'
    environment: 'development'

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'

  # Gateway - API Gateway pour Aviationstack (port 8004)
  - job_name: 'gateway'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['gateway:8004']
        labels:
          service: 'gateway'
          microservice: 'gateway'

  # Airport microservice (port 8001)
  - job_name: 'airport'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['airport:8001']
        labels:
          service: 'airport'
          microservice: 'airport'

  # Flight microservice (port 8002)
  - job_name: 'flight'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['flight:8002']
        labels:
          service: 'flight'
          microservice: 'flight'

  # Assistant microservice (port 8003)
  - job_name: 'assistant'
    scrape_interval: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['assistant:8003']
        labels:
          service: 'assistant'
          microservice: 'assistant'
```

### Docker Compose Prometheus (Extrait)

```yaml
prometheus:
  image: prom/prometheus:v2.54.0
  container_name: hello-mira-prometheus
  restart: unless-stopped

  depends_on:
    - airport
    - flight
    - assistant

  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus

  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.enable-lifecycle'
    - '--storage.tsdb.retention.time=15d'

  ports:
    - "9090:9090"

  healthcheck:
    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Accès Prometheus

- **UI** : <http://localhost:9090>
- **Targets** : <http://localhost:9090/targets>
- **API** : <http://localhost:9090/api/v1/query>

---

## Grafana

### Configuration Auto-Provisioning

**Structure** :

```text
monitoring/grafana/
├── dashboards/
│   └── hello-mira-metrics.json    # Dashboard principal
└── provisioning/
    ├── dashboards/
    │   └── default.yml             # Config provisioning dashboards
    └── datasources/
        └── grafana-datasources.yml # Config Prometheus datasource
```

### Datasource Prometheus

**Fichier** : `grafana-datasources.yml`

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

### Docker Compose Grafana (Extrait)

```yaml
grafana:
  image: grafana/grafana:10.2.2
  container_name: hello-mira-grafana
  restart: unless-stopped

  depends_on:
    prometheus:
      condition: service_healthy

  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    GF_AUTH_ANONYMOUS_ENABLED: "true"
    GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer

  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro

  ports:
    - "3000:3000"
```

### Accès Grafana

- **UI** : <http://localhost:3000>
- **Login** : admin / admin (ou `GRAFANA_PASSWORD`)
- **Dashboards** : <http://localhost:3000/dashboards>

---

## Métriques Disponibles

### Métriques Gateway (Custom)

**Fichier** : `gateway/monitoring/metrics.py`

#### Cache

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `gateway_cache_hits_total` | Counter | endpoint | Nombre de cache hits |
| `gateway_cache_misses_total` | Counter | endpoint | Nombre de cache misses |

#### API Calls Gateway

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `gateway_api_calls_total` | Counter | endpoint, status | Appels API Aviationstack |

Status possibles : `success`, `error`, `rate_limited`

#### Request Coalescing Gateway

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `gateway_coalesced_requests_total` | Counter | endpoint | Requêtes fusionnées |

#### Circuit Breaker Gateway

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `gateway_circuit_breaker_state` | Gauge | - | État (0=closed, 1=half_open, 2=open) |

#### Rate Limiting

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `gateway_rate_limit_used` | Gauge | - | Appels API utilisés ce mois |
| `gateway_rate_limit_remaining` | Gauge | - | Appels restants ce mois |

### Métriques HTTP (Auto-générées)

Générées par `prometheus_fastapi_instrumentator` :

| Métrique | Type | Description |
|----------|------|-------------|
| `http_request_duration_seconds` | Histogram | Latence des requêtes |
| `http_requests_total` | Counter | Nombre total de requêtes |
| `http_requests_created` | Counter | Timestamp première requête |

Labels automatiques : `handler`, `method`, `status`

---

## Queries PromQL

### Cache Performance

```promql
# Hit-rate du cache (%)
(
  sum(gateway_cache_hits_total)
  /
  (sum(gateway_cache_hits_total) + sum(gateway_cache_misses_total))
) * 100

# Hit-rate par endpoint
(
  gateway_cache_hits_total{endpoint="airports"}
  /
  (gateway_cache_hits_total{endpoint="airports"} + gateway_cache_misses_total{endpoint="airports"})
) * 100
```

### API Calls PromQL

```promql
# Appels API par minute
rate(gateway_api_calls_total[1m]) * 60

# Appels API par endpoint (5 dernières minutes)
sum by(endpoint) (increase(gateway_api_calls_total[5m]))

# Taux d'erreur API
sum(rate(gateway_api_calls_total{status="error"}[5m]))
/
sum(rate(gateway_api_calls_total[5m])) * 100
```

### Request Coalescing PromQL

```promql
# Taux de coalescing (économies)
sum(rate(gateway_coalesced_requests_total[5m]))
/
(
  sum(rate(gateway_coalesced_requests_total[5m]))
  + sum(rate(gateway_api_calls_total[5m]))
) * 100

# Requêtes coalescées par minute
rate(gateway_coalesced_requests_total[1m]) * 60
```

### Circuit Breaker PromQL

```promql
# État actuel (0=OK, 1=HALF_OPEN, 2=OPEN)
gateway_circuit_breaker_state

# Alerte : circuit ouvert
gateway_circuit_breaker_state == 2
```

### Rate Limit

```promql
# Quota restant
gateway_rate_limit_remaining

# Pourcentage utilisé
(gateway_rate_limit_used / 10000) * 100

# Prédiction épuisement (jours restants)
gateway_rate_limit_remaining / (rate(gateway_rate_limit_used[1h]) * 24)
```

### HTTP Latency

```promql
# Latence p95 par service
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)

# Latence moyenne par endpoint
sum(rate(http_request_duration_seconds_sum[5m])) by (handler)
/
sum(rate(http_request_duration_seconds_count[5m])) by (handler)

# Requêtes par seconde par service
sum(rate(http_requests_total[1m])) by (service)
```

---

## Alertes

### Exemples de Règles d'Alerte

#### Circuit Breaker Open

```yaml
groups:
- name: gateway
  rules:
  - alert: CircuitBreakerOpen
    expr: gateway_circuit_breaker_state == 2
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Circuit breaker ouvert"
      description: "Le circuit breaker est ouvert depuis plus d'1 minute"
```

#### Rate Limit Low

```yaml
  - alert: RateLimitLow
    expr: gateway_rate_limit_remaining < 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Quota API bas"
      description: "Moins de 1000 appels API restants ce mois"
```

#### Cache Hit Rate Low

```yaml
  - alert: LowCacheHitRate
    expr: |
      (
        sum(gateway_cache_hits_total)
        /
        (sum(gateway_cache_hits_total) + sum(gateway_cache_misses_total))
      ) < 0.5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Cache hit rate bas"
      description: "Le hit rate du cache est sous 50%"
```

#### High Latency

```yaml
  - alert: HighLatency
    expr: |
      histogram_quantile(0.95,
        sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
      ) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Latence élevée"
      description: "La latence p95 dépasse 2 secondes"
```

---

## Configuration

### Variables d'Environnement

| Variable | Service | Défaut | Description |
|----------|---------|--------|-------------|
| `GRAFANA_PASSWORD` | Grafana | admin | Mot de passe admin |
| `GF_AUTH_ANONYMOUS_ENABLED` | Grafana | true | Accès anonyme |

### Rétention des Données

```yaml
# Prometheus : 15 jours de rétention
command:
  - '--storage.tsdb.retention.time=15d'
```

### Personnalisation Dashboard

Le dashboard JSON est dans `monitoring/grafana/dashboards/hello-mira-metrics.json`.

Pour modifier :

1. Éditer dans Grafana UI
2. Exporter en JSON (Share → Export)
3. Remplacer le fichier JSON
4. Redémarrer Grafana

---

## Debugging

### Vérifier les Targets Prometheus

```bash
# Via API
curl http://localhost:9090/api/v1/targets

# Ou via UI
open http://localhost:9090/targets
```

### Vérifier les Métriques d'un Service

```bash
# Gateway
curl http://localhost:8004/metrics | grep gateway_

# Airport
curl http://localhost:8001/metrics | grep http_

# Flight
curl http://localhost:8002/metrics | grep http_
```

### Tester une Query PromQL

```bash
# Via API
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=gateway_rate_limit_remaining'

# Résultat
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {"__name__": "gateway_rate_limit_remaining"},
        "value": [1732800000, "8766"]
      }
    ]
  }
}
```

### Logs

```bash
# Logs Prometheus
docker-compose logs -f prometheus

# Logs Grafana
docker-compose logs -f grafana
```
