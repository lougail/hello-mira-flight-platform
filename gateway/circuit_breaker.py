"""
Circuit Breaker Pattern pour l'API Gateway.

Protege contre les cascading failures en stoppant les appels
vers un service defaillant.

Etats:
- CLOSED: Normal, les requetes passent
- OPEN: Service KO, requetes rejetees immediatement
- HALF_OPEN: Test de recovery, quelques requetes passent
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Etats du circuit breaker."""
    CLOSED = "closed"      # Normal - requetes passent
    OPEN = "open"          # Bloque - service KO
    HALF_OPEN = "half_open"  # Test - quelques requetes passent


class CircuitBreakerError(Exception):
    """Levee quand le circuit est ouvert."""
    def __init__(self, message: str, reset_at: datetime):
        self.message = message
        self.reset_at = reset_at
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit Breaker avec les parametres suivants:
    - failure_threshold: Nombre d'echecs avant ouverture (defaut: 5)
    - recovery_timeout: Temps avant passage en HALF_OPEN (defaut: 30s)
    - half_open_max_calls: Requetes autorisees en HALF_OPEN (defaut: 3)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # Etat interne
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

        # Lock pour thread-safety
        self._lock = asyncio.Lock()

        logger.info(
            f"CircuitBreaker initialized: threshold={failure_threshold}, "
            f"recovery={recovery_timeout}s, half_open_max={half_open_max_calls}"
        )

    @property
    def state(self) -> CircuitState:
        """Retourne l'etat actuel du circuit."""
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    async def _check_state(self) -> None:
        """Verifie et met a jour l'etat du circuit."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                # Verifie si on peut passer en HALF_OPEN
                if self._last_failure_time:
                    elapsed = datetime.utcnow() - self._last_failure_time
                    if elapsed >= timedelta(seconds=self.recovery_timeout):
                        logger.info("🔄 Circuit OPEN -> HALF_OPEN (recovery timeout)")
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0

    async def can_execute(self) -> bool:
        """Verifie si une requete peut passer."""
        await self._check_state()

        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            # OPEN
            return False

    async def record_success(self) -> None:
        """Enregistre un succes."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                # Apres N succes en HALF_OPEN, on ferme le circuit
                if self._success_count >= self.half_open_max_calls:
                    logger.info("✅ Circuit HALF_OPEN -> CLOSED (recovery success)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset le compteur d'echecs apres un succes
                self._failure_count = 0

    async def record_failure(self) -> None:
        """Enregistre un echec."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                # Un echec en HALF_OPEN rouvre le circuit
                logger.warning("⚠️ Circuit HALF_OPEN -> OPEN (failure during recovery)")
                self._state = CircuitState.OPEN
                self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        f"🔴 Circuit CLOSED -> OPEN "
                        f"({self._failure_count} failures >= {self.failure_threshold})"
                    )
                    self._state = CircuitState.OPEN

    def get_reset_time(self) -> Optional[datetime]:
        """Retourne le moment ou le circuit passera en HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            return self._last_failure_time + timedelta(seconds=self.recovery_timeout)
        return None

    def get_stats(self) -> dict:
        """Retourne les statistiques du circuit breaker."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "reset_at": self.get_reset_time().isoformat() if self.get_reset_time() else None
        }
