"""
API Gateway pour Aviationstack.

Point unique d'acces a l'API externe avec:
- Rate limiting (10000 calls/mois, reset le 1er)
- Cache MongoDB
- Request coalescing (fusion des requetes identiques)
- Circuit breaker (protection contre les pannes)
- Monitoring Prometheus centralise

Port: 8004
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from prometheus_fastapi_instrumentator import Instrumentator
import httpx

from config import settings
from rate_limiter import RateLimiter, RateLimitExceeded
from cache import CacheService
from circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState
from request_coalescer import RequestCoalescer
from monitoring.metrics import (
    cache_hits, cache_misses, api_calls, coalesced_requests,
    circuit_breaker_state, rate_limit_used, rate_limit_remaining
)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Services globaux
mongo_client: Optional[AsyncMongoClient] = None
rate_limiter: Optional[RateLimiter] = None
cache_service: Optional[CacheService] = None
http_client: Optional[httpx.AsyncClient] = None
circuit_breaker: Optional[CircuitBreaker] = None
request_coalescer: Optional[RequestCoalescer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup et shutdown."""
    global mongo_client, rate_limiter, cache_service, http_client
    global circuit_breaker, request_coalescer

    logger.info("=" * 60)
    logger.info("🚀 Starting Aviationstack Gateway")
    logger.info("=" * 60)

    # MongoDB
    try:
        mongo_client = AsyncMongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000
        )
        await mongo_client.admin.command('ping')
        db = mongo_client[settings.mongodb_database]

        # Rate limiter collection
        rate_limit_col = db["api_rate_limit"]
        rate_limiter = RateLimiter(collection=rate_limit_col, max_calls=10000)
        logger.info("✅ Rate limiter ready (10000 calls/month)")

        # Cache collection
        cache_col = db["gateway_cache"]
        await cache_col.create_index("expires_at", expireAfterSeconds=0)
        cache_service = CacheService(collection=cache_col, ttl=settings.cache_ttl)
        logger.info(f"✅ Cache ready (TTL={settings.cache_ttl}s)")

    except Exception as e:
        logger.error(f"❌ MongoDB failed: {e}")
        rate_limiter = None
        cache_service = None

    # HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20)
    )
    logger.info("✅ HTTP client ready")

    # Circuit Breaker (5 echecs -> ouverture, 30s recovery)
    circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30,
        half_open_max_calls=3
    )
    logger.info("✅ Circuit breaker ready (threshold=5, recovery=30s)")

    # Request Coalescer
    request_coalescer = RequestCoalescer()
    logger.info("✅ Request coalescer ready")

    logger.info("=" * 60)
    logger.info("✅ Gateway started on port 8004")
    logger.info("=" * 60)

    yield

    # Shutdown
    if http_client:
        await http_client.aclose()
    if mongo_client:
        await mongo_client.close()
    logger.info("✅ Gateway stopped")


app = FastAPI(
    title="Aviationstack Gateway",
    version="1.0.0",
    description="API Gateway centralisé pour Aviationstack",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Prometheus instrumentation (HTTP metrics + /metrics endpoint)
Instrumentator().instrument(app).expose(app)


async def _do_api_call(endpoint: str, params: Dict[str, Any], cache_key: str) -> Dict[str, Any]:
    """
    Execute l'appel API reel (utilise par le coalescer).
    """
    # Check rate limit
    if rate_limiter:
        try:
            await rate_limiter.check_and_increment()
            # Update rate limit metrics
            usage = await rate_limiter.get_usage()
            rate_limit_used.set(usage.get("used", 0))
            rate_limit_remaining.set(usage.get("remaining", 0))
        except RateLimitExceeded as e:
            logger.warning(f"⚠️ Rate limit exceeded")
            api_calls.labels(endpoint=endpoint, status="rate_limited").inc()
            raise HTTPException(status_code=429, detail=str(e))

    # Call API
    params_with_key = {**params, "access_key": settings.aviationstack_api_key}
    url = f"{settings.aviationstack_base_url}/{endpoint}"

    safe_params = {k: v for k, v in params.items() if k != "access_key"}
    logger.info(f"🌐 API call: {endpoint} params={safe_params}")

    try:
        response = await http_client.get(url, params=params_with_key)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            # Record failure for circuit breaker
            if circuit_breaker:
                await circuit_breaker.record_failure()
                _update_circuit_breaker_metric()
            api_calls.labels(endpoint=endpoint, status="error").inc()
            raise HTTPException(status_code=400, detail=data["error"])

        # Record success for circuit breaker
        if circuit_breaker:
            await circuit_breaker.record_success()
            _update_circuit_breaker_metric()

        # Cache result
        if cache_service:
            await cache_service.set(cache_key, data)

        # Metrics
        api_calls.labels(endpoint=endpoint, status="success").inc()

        logger.info(f"✅ API success: {endpoint} -> {len(data.get('data', []))} results")
        return data

    except httpx.HTTPError as e:
        # Record failure for circuit breaker
        if circuit_breaker:
            await circuit_breaker.record_failure()
            _update_circuit_breaker_metric()
        api_calls.labels(endpoint=endpoint, status="error").inc()
        logger.error(f"❌ API error: {e}")
        raise HTTPException(status_code=502, detail=f"Aviationstack error: {e}")


def _update_circuit_breaker_metric():
    """Met a jour la metrique du circuit breaker."""
    if circuit_breaker:
        state_map = {
            CircuitState.CLOSED: 0,
            CircuitState.HALF_OPEN: 1,
            CircuitState.OPEN: 2
        }
        circuit_breaker_state.set(state_map.get(circuit_breaker.state, 0))


async def call_aviationstack(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appelle l'API Aviationstack avec:
    - Cache MongoDB
    - Circuit breaker (protection pannes)
    - Request coalescing (fusion requetes identiques)
    - Rate limiting
    """
    # 1. Check cache first (avant tout)
    cache_key = f"{endpoint}:{sorted(params.items())}"
    if cache_service:
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"✅ Cache HIT: {endpoint}")
            cache_hits.labels(endpoint=endpoint).inc()
            return cached
        else:
            cache_misses.labels(endpoint=endpoint).inc()

    # 2. Check circuit breaker
    if circuit_breaker:
        _update_circuit_breaker_metric()
        if not await circuit_breaker.can_execute():
            reset_time = circuit_breaker.get_reset_time()
            logger.warning(f"🔴 Circuit OPEN - rejecting request: {endpoint}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Service temporarily unavailable (circuit breaker open)",
                    "retry_after": reset_time.isoformat() if reset_time else None
                }
            )

    # 3. Use request coalescer to avoid duplicate concurrent calls
    if request_coalescer:
        # Check if this request will be coalesced
        stats_before = request_coalescer.get_stats()
        result = await request_coalescer.execute(
            key=cache_key,
            func=_do_api_call,
            endpoint=endpoint,
            params=params,
            cache_key=cache_key
        )
        stats_after = request_coalescer.get_stats()
        # If coalesced count increased, this request was coalesced
        if stats_after["coalesced_requests"] > stats_before["coalesced_requests"]:
            coalesced_requests.labels(endpoint=endpoint).inc()
        return result
    else:
        return await _do_api_call(endpoint, params, cache_key)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"service": "Aviationstack Gateway", "status": "running"}


@app.get("/health")
async def health():
    usage = await rate_limiter.get_usage() if rate_limiter else {}
    cb_state = circuit_breaker.state.value if circuit_breaker else "disabled"

    # Determine overall status based on circuit breaker
    if circuit_breaker and circuit_breaker.is_open:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "rate_limit": usage,
        "cache": "enabled" if cache_service else "disabled",
        "circuit_breaker": cb_state
    }


@app.get("/usage")
async def get_usage():
    """Retourne l'utilisation du quota API."""
    if not rate_limiter:
        raise HTTPException(status_code=503, detail="Rate limiter not available")
    return await rate_limiter.get_usage()


@app.get("/stats")
async def get_stats():
    """Retourne les statistiques completes du gateway."""
    return {
        "rate_limit": await rate_limiter.get_usage() if rate_limiter else None,
        "circuit_breaker": circuit_breaker.get_stats() if circuit_breaker else None,
        "request_coalescer": request_coalescer.get_stats() if request_coalescer else None,
        "cache": cache_service.get_stats() if cache_service else {"enabled": False}
    }


@app.get("/airports")
async def get_airports(
    iata_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    country_iso2: Optional[str] = Query(None),
    limit: int = Query(100, le=100)
):
    """Proxy vers /airports de Aviationstack."""
    params = {"limit": limit}
    if iata_code:
        params["iata_code"] = iata_code.upper()
    if search:
        params["search"] = search
    if country_iso2:
        params["country_iso2"] = country_iso2.upper()

    return await call_aviationstack("airports", params)


@app.get("/flights")
async def get_flights(
    flight_iata: Optional[str] = Query(None),
    dep_iata: Optional[str] = Query(None),
    arr_iata: Optional[str] = Query(None),
    airline_iata: Optional[str] = Query(None),
    flight_status: Optional[str] = Query(None),
    flight_date: Optional[str] = Query(None),
    limit: int = Query(100, le=100)
):
    """Proxy vers /flights de Aviationstack."""
    params = {"limit": limit}
    if flight_iata:
        params["flight_iata"] = flight_iata.upper()
    if dep_iata:
        params["dep_iata"] = dep_iata.upper()
    if arr_iata:
        params["arr_iata"] = arr_iata.upper()
    if airline_iata:
        params["airline_iata"] = airline_iata.upper()
    if flight_status:
        params["flight_status"] = flight_status.lower()
    if flight_date:
        params["flight_date"] = flight_date

    return await call_aviationstack("flights", params)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
