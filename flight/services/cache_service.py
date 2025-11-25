"""
Service de cache MongoDB générique et réutilisable.

Responsabilités :
- Lire/écrire dans MongoDB avec TTL
- Gérer l'expiration automatique
- Logger les hits/miss pour optimisation

Réutilisable pour :
- Partie 1 (Airport) : cache des aéroports
- Partie 2 (Flight) : cache des vols
- Partie 3 (Optimisation) : métriques de cache
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from monitoring.metrics import cache_hits, cache_misses, cache_expired

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service de cache générique avec MongoDB.
    
    Usage:
        cache = CacheService(mongo_collection, ttl=300)
        data = await cache.get("airport:CDG")
        await cache.set("airport:CDG", {"name": "Charles de Gaulle"})
    """
    
    def __init__(self, collection, ttl: int = 300, service_name: str = "flight", cache_type: str = "default"):
        """
        Initialise le service de cache.

        Args:
            collection: Collection MongoDB (PyMongo AsyncMongoClient collection)
            ttl: Time To Live en secondes (défaut: 5 minutes)
            service_name: Nom du service pour les métriques (airport, flight, assistant)
            cache_type: Type de cache pour les métriques (airports, flights, etc.)
        """
        self.collection = collection
        self.ttl = ttl
        self.service_name = service_name
        self.cache_type = cache_type
        
    async def get(self, key: str) -> Optional[dict]:
        """
        Récupère une valeur depuis le cache.
        
        Args:
            key: Clé de cache (ex: "airport:CDG")
            
        Returns:
            Données si trouvées et non expirées, sinon None
            
        Example:
            >>> data = await cache.get("airport:CDG")
            >>> if data:
            ...     print(f"Cache hit: {data['name']}")
            ... else:
            ...     print("Cache miss")
        """
        if self.collection is None:
            return None
            
        try:
            cached = await self.collection.find_one({"_id": key})

            if not cached:
                logger.debug(f"Cache miss: {key}")
                cache_misses.labels(service=self.service_name, cache_type=self.cache_type).inc()
                return None

            # Vérifie l'expiration
            expires_at = cached.get("expires_at")
            if expires_at and expires_at < datetime.utcnow():
                logger.debug(f"Cache expired: {key}")
                cache_expired.labels(service=self.service_name, cache_type=self.cache_type).inc()
                # Nettoie l'entrée expirée
                await self.collection.delete_one({"_id": key})
                return None

            logger.debug(f"Cache hit: {key}")
            cache_hits.labels(service=self.service_name, cache_type=self.cache_type).inc()
            return cached.get("data")
            
        except Exception as e:
            logger.error(f"Erreur lecture cache pour {key}: {e}")
            return None
    
    async def set(self, key: str, data: dict):
        """
        Sauvegarde une valeur dans le cache.
        
        Args:
            key: Clé de cache
            data: Données à cacher (dict JSON-serializable)
            
        Example:
            >>> await cache.set(
            ...     "airport:CDG",
            ...     {"name": "Charles de Gaulle", "iata": "CDG"}
            ... )
        """
        if self.collection is None:
            return
            
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)
            
            await self.collection.replace_one(
                {"_id": key},
                {
                    "_id": key,
                    "data": data,
                    "created_at": datetime.utcnow(),
                    "expires_at": expires_at
                },
                upsert=True
            )
            
            logger.debug(f"Cached: {key} (TTL: {self.ttl}s)")
            
        except Exception as e:
            logger.error(f"Erreur écriture cache pour {key}: {e}")
    
    async def delete(self, key: str):
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé de cache
            
        Example:
            >>> await cache.delete("airport:CDG")
        """
        if self.collection is None:
            return
            
        try:
            await self.collection.delete_one({"_id": key})
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Erreur suppression cache pour {key}: {e}")
    
    async def clear_all(self):
        """
        Vide tout le cache (utile pour les tests).
        
        Example:
            >>> await cache.clear_all()
        """
        if self.collection is None:
            return
            
        try:
            result = await self.collection.delete_many({})
            logger.info(f"Cache cleared: {result.deleted_count} entrées supprimées")
        except Exception as e:
            logger.error(f"Erreur vidage cache: {e}")