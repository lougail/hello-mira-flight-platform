"""Cache MongoDB simple."""

from datetime import datetime, timedelta
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Cache avec TTL via MongoDB."""

    def __init__(self, collection=None, ttl: int = 300):
        self.collection = collection
        self.ttl = ttl
        # Compteurs pour les stats
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        if self.collection is None:
            self._misses += 1
            return None

        try:
            doc = await self.collection.find_one({"_id": key})
            if doc and doc.get("expires_at", datetime.min) > datetime.utcnow():
                self._hits += 1
                return doc.get("data")
            self._misses += 1
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._misses += 1
            return None

    def get_stats(self) -> dict:
        """Retourne les statistiques du cache."""
        total = self._hits + self._misses
        hit_rate = round(self._hits / total * 100, 1) if total > 0 else 0.0
        return {
            "enabled": self.collection is not None,
            "ttl_seconds": self.ttl,
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate": f"{hit_rate}%"
        }

    async def set(self, key: str, data: Any) -> bool:
        """Stocke une valeur dans le cache."""
        if self.collection is None:
            return False

        try:
            await self.collection.replace_one(
                {"_id": key},
                {
                    "_id": key,
                    "data": data,
                    "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl),
                    "created_at": datetime.utcnow()
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
