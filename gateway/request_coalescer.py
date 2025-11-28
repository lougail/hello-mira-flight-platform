"""
Request Coalescer pour l'API Gateway.

Fusionne les requetes identiques concurrentes en une seule requete API.
Evite de gaspiller le quota quand plusieurs services demandent
la meme donnee au meme moment.
"""

import asyncio
import logging
from typing import Dict, Callable, Any, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RequestCoalescer:
    """
    Coalescer centralise pour le gateway.

    Usage:
        coalescer = RequestCoalescer()

        # Ces 3 appels simultanees ne declenchent qu'UN appel API
        results = await asyncio.gather(
            coalescer.execute("airports:CDG", fetch_airport, "CDG"),
            coalescer.execute("airports:CDG", fetch_airport, "CDG"),
            coalescer.execute("airports:CDG", fetch_airport, "CDG")
        )
    """

    def __init__(self):
        # Dictionnaire des requetes en vol : {key: asyncio.Task}
        self._in_flight: Dict[str, asyncio.Task] = {}
        # Lock pour thread-safety
        self._lock = asyncio.Lock()
        # Compteurs pour stats
        self._total_requests = 0
        self._coalesced_requests = 0

        logger.info("RequestCoalescer initialized")

    async def execute(
        self,
        key: str,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute une fonction avec coalescing.

        Args:
            key: Cle unique pour cette requete (ex: "airports:iata_code=CDG")
            func: Fonction async a executer
            *args, **kwargs: Arguments pour func

        Returns:
            Resultat de la fonction
        """
        self._total_requests += 1

        async with self._lock:
            # Si une requete identique est en cours, on attend son resultat
            if key in self._in_flight:
                self._coalesced_requests += 1
                logger.debug(f"🔗 Coalescing request: {key}")
                # Libere le lock puis attend le resultat
                task = self._in_flight[key]

        # Hors du lock pour eviter deadlock
        if key in self._in_flight:
            try:
                return await self._in_flight[key]
            except Exception:
                # Si la tache a echoue, on laisse passer pour retry
                pass

        # Nouvelle requete
        async with self._lock:
            # Double-check au cas ou une autre tache a ete creee entre temps
            if key in self._in_flight:
                logger.debug(f"🔗 Coalescing request (race): {key}")
                self._coalesced_requests += 1

            logger.debug(f"🚀 New request: {key}")
            task = asyncio.create_task(func(*args, **kwargs))
            self._in_flight[key] = task

        try:
            result = await task
            return result
        finally:
            # Cleanup
            async with self._lock:
                self._in_flight.pop(key, None)
                logger.debug(f"✅ Request completed: {key}")

    def get_stats(self) -> dict:
        """Retourne les statistiques du coalescer."""
        saved = self._coalesced_requests
        total = self._total_requests
        rate = (saved / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "coalesced_requests": saved,
            "actual_api_calls": total - saved,
            "savings_rate": f"{rate:.1f}%",
            "in_flight": len(self._in_flight)
        }
