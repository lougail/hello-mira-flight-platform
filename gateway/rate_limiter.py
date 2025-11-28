"""
Rate Limiter avec reset mensuel.

Le compteur se réinitialise le 1er de chaque mois pour
correspondre au cycle de facturation Aviationstack.
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Levée quand la limite mensuelle est atteinte."""
    pass


class RateLimiter:
    """
    Rate limiter partagé via MongoDB.

    - 10000 appels/mois (Basic Plan)
    - Reset automatique le 1er du mois
    - Compteur partagé entre tous les services via MongoDB
    """

    def __init__(self, collection=None, max_calls: int = 10000):
        self.collection = collection
        self.max_calls = max_calls
        self._key = "aviationstack_api_calls"

    def _get_month_key(self) -> str:
        """Retourne '2025-11' pour novembre 2025."""
        now = datetime.utcnow()
        return f"{now.year}-{now.month:02d}"

    def _get_next_reset(self) -> datetime:
        """Retourne le 1er du mois suivant."""
        now = datetime.utcnow()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        return datetime(now.year, now.month + 1, 1)

    async def check_and_increment(self):
        """
        Vérifie le quota et incrémente le compteur.

        Raises:
            RateLimitExceeded: Si 10000 appels atteints ce mois
        """
        if self.collection is None:
            logger.warning("RateLimiter: MongoDB non disponible")
            return

        now = datetime.utcnow()
        month = self._get_month_key()

        try:
            doc = await self.collection.find_one({"_id": self._key})

            # Reset si nouveau mois
            if doc and doc.get("month") == month:
                count = doc.get("count", 0)
            else:
                count = 0
                logger.info(f"🔄 Nouveau mois {month}, compteur reset")

            if count >= self.max_calls:
                reset = self._get_next_reset().strftime("%d/%m/%Y")
                raise RateLimitExceeded(
                    f"Limite atteinte: {count}/{self.max_calls} appels. Reset le {reset}"
                )

            # Incrémente
            await self.collection.replace_one(
                {"_id": self._key},
                {
                    "_id": self._key,
                    "month": month,
                    "count": count + 1,
                    "max_calls": self.max_calls,
                    "updated_at": now
                },
                upsert=True
            )

            logger.debug(f"API calls: {count + 1}/{self.max_calls}")

        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"RateLimiter error: {e}")

    async def get_usage(self) -> dict:
        """Retourne les stats d'utilisation."""
        if self.collection is None:
            return {"error": "MongoDB non disponible"}

        month = self._get_month_key()

        try:
            doc = await self.collection.find_one({"_id": self._key})

            if doc and doc.get("month") == month:
                used = doc.get("count", 0)
            else:
                used = 0

            return {
                "month": month,
                "used": used,
                "limit": self.max_calls,
                "remaining": max(0, self.max_calls - used),
                "reset_date": self._get_next_reset().isoformat(),
                "percentage": round(used / self.max_calls * 100, 1)
            }
        except Exception as e:
            return {"error": str(e)}
