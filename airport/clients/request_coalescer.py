"""
Request Coalescer - Fusion de requêtes identiques concurrentes.

Responsabilités :
- Éviter les appels API redondants (plusieurs requêtes identiques simultanées)
- Mutualiser les résultats entre requêtes coalescées
- Tracker les métriques de coalescing pour Prometheus
- Gérer la mémoire (cleanup des tasks terminées)

Implémentation : Task Dictionary Pattern avec asyncio.Lock
"""

import asyncio
import logging
from typing import Dict, Callable, Any, Awaitable, Coroutine, TypeVar, Optional
from functools import wraps

from monitoring.metrics import coalesced_requests

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RequestCoalescer:
    """
    Coalescer générique pour éviter les appels API dupliqués.

    Usage:
        coalescer = RequestCoalescer(service_name="airport")

        @coalescer.coalesce
        async def get_airport(iata_code: str):
            # Appel API réel
            return await api_client.get(f"/airports/{iata_code}")

        # Ces 3 appels simultanés ne déclencheront qu'UN seul appel API
        results = await asyncio.gather(
            get_airport("CDG"),
            get_airport("CDG"),
            get_airport("CDG")
        )
    """

    def __init__(self, service_name: str = "airport"):
        """
        Initialise le coalescer.

        Args:
            service_name: Nom du service pour les métriques (airport, flight)
        """
        self.service_name = service_name

        # Dictionnaire des requêtes en vol : {key: asyncio.Task}
        self._in_flight: Dict[str, asyncio.Task] = {}

        # Lock pour protéger l'accès au dictionnaire (thread-safe)
        self._lock = asyncio.Lock()

        logger.debug(f"RequestCoalescer initialized for service: {service_name}")

    def coalesce(self, func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Awaitable[T]]:
        """
        Décorateur pour activer le coalescing sur une fonction async.

        Args:
            func: Fonction async à wrapper

        Returns:
            Fonction wrappée avec coalescing
        """
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Génère une clé unique basée sur la fonction et les arguments
            cache_key = self._make_key(func.__name__, args, kwargs)
            endpoint = func.__name__  # Pour les métriques

            # Double-check locking pattern
            async with self._lock:
                # Si une requête identique est déjà en cours, on la réutilise
                if cache_key in self._in_flight:
                    logger.debug(f"🔗 Coalescing request: {cache_key}")
                    coalesced_requests.labels(
                        service=self.service_name,
                        endpoint=endpoint
                    ).inc()

                    # Attend le résultat de la requête en cours
                    return await self._in_flight[cache_key]

                # Sinon, on crée une nouvelle tâche
                logger.debug(f"🚀 New request: {cache_key}")
                task = asyncio.create_task(func(*args, **kwargs))
                self._in_flight[cache_key] = task

            try:
                # Exécute la requête
                result = await task
                return result
            finally:
                # Cleanup : retire la tâche terminée du dictionnaire
                async with self._lock:
                    self._in_flight.pop(cache_key, None)
                    logger.debug(f"✅ Request completed and cleaned: {cache_key}")

        return wrapper

    async def execute(
        self,
        key: str,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        endpoint: Optional[str] = None,
        **kwargs
    ) -> T:
        """
        Exécute une fonction avec coalescing (alternative au décorateur).

        Args:
            key: Clé unique pour cette requête (ex: "airports/CDG")
            func: Fonction async à exécuter
            endpoint: Nom de l'endpoint pour les métriques
            *args, **kwargs: Arguments pour func

        Returns:
            Résultat de la fonction

        Example:
            >>> result = await coalescer.execute(
            ...     key="airports/CDG",
            ...     func=api_client.get,
            ...     endpoint="airports",
            ...     url="/airports/CDG"
            ... )
        """
        endpoint_name = endpoint or key.split('/')[0]

        # Double-check locking pattern
        async with self._lock:
            if key in self._in_flight:
                logger.debug(f"🔗 Coalescing request: {key}")
                coalesced_requests.labels(
                    service=self.service_name,
                    endpoint=endpoint_name
                ).inc()
                return await self._in_flight[key]

            logger.debug(f"🚀 New request: {key}")
            task = asyncio.create_task(func(*args, **kwargs))
            self._in_flight[key] = task

        try:
            result = await task
            return result
        finally:
            async with self._lock:
                self._in_flight.pop(key, None)
                logger.debug(f"✅ Request completed: {key}")

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Génère une clé unique pour une requête.

        Args:
            func_name: Nom de la fonction
            args: Arguments positionnels
            kwargs: Arguments nommés

        Returns:
            Clé unique (string)
        """
        # Convertit les args/kwargs en string pour la clé
        args_str = '_'.join(str(arg) for arg in args)
        kwargs_str = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))

        parts = [func_name]
        if args_str:
            parts.append(args_str)
        if kwargs_str:
            parts.append(kwargs_str)

        return ':'.join(parts)

    def get_stats(self) -> dict:
        """
        Retourne les statistiques actuelles du coalescer.

        Returns:
            Dict avec le nombre de requêtes en vol
        """
        return {
            "service": self.service_name,
            "in_flight_requests": len(self._in_flight),
            "active_keys": list(self._in_flight.keys())
        }
