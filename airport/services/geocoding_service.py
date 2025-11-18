"""
Service de géocodage et calcul de distances géographiques.

Responsabilités :
- Convertir une adresse en coordonnées GPS
- Calculer la distance entre deux points (formule de Haversine)
- Utilise l'API Nominatim (OpenStreetMap) - gratuite

Note : Nominatim a une politique d'usage équitable :
- Max 1 requête/seconde
- User-Agent obligatoire
- Pas besoin de clé API
"""

import math
import logging
from typing import Optional, Tuple
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Service pour le géocodage et les calculs de distance.
    
    Usage:
        geocoding = GeocodingService()
        coords = await geocoding.geocode_address("Lille, France")
        distance = geocoding.calculate_distance(48.8566, 2.3522, 50.6292, 3.0573)
    """
    
    def __init__(self):
        """Initialise le service de géocodage."""
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.user_agent = f"HelloMira-Airport-Service/{settings.app_version}"
    
    # ========================================================================
    # CALCUL DE DISTANCE (FORMULE DE HAVERSINE)
    # ========================================================================
    
    @staticmethod
    def calculate_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcule la distance entre deux points GPS (formule de Haversine).
        
        La formule de Haversine donne la distance orthodromique (great-circle)
        entre deux points sur une sphère à partir de leurs latitudes/longitudes.
        
        Args:
            lat1, lon1: Coordonnées du point 1 (en degrés)
            lat2, lon2: Coordonnées du point 2 (en degrés)
            
        Returns:
            Distance en kilomètres
            
        Example:
            >>> # Distance Paris → Londres
            >>> distance = GeocodingService.calculate_distance(
            ...     48.8566, 2.3522,  # Paris
            ...     51.5074, -0.1278  # Londres
            ... )
            >>> print(f"{distance:.1f} km")  # ~344.0 km
        """
        # Rayon moyen de la Terre en km
        R = 6371.0
        
        # Convertit les degrés en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calcule les différences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Formule de Haversine
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    # ========================================================================
    # GÉOCODAGE (ADRESSE → COORDONNÉES GPS)
    # ========================================================================
    
    async def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convertit une adresse en coordonnées GPS.
        
        Utilise l'API Nominatim d'OpenStreetMap (gratuite, sans clé).
        
        Args:
            address: Adresse à géocoder (ex: "Lille, France", "10 rue de Rivoli Paris")
            
        Returns:
            Tuple (latitude, longitude) ou None si non trouvé
            
        Example:
            >>> coords = await geocoding.geocode_address("Lille, France")
            >>> if coords:
            ...     print(f"Coordonnées : {coords[0]}, {coords[1]}")
            ... else:
            ...     print("Adresse non trouvée")
        """
        logger.info(f"Géocodage de l'adresse : {address}")
        
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1  # Ajoute des détails sur l'adresse
        }
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.nominatim_url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                if not data or len(data) == 0:
                    logger.warning(f"Adresse non trouvée : {address}")
                    return None
                
                result = data[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                
                # Log avec le nom du lieu trouvé
                display_name = result.get("display_name", "Unknown")
                logger.info(
                    f"Adresse géocodée : {display_name} → ({lat:.4f}, {lon:.4f})"
                )
                
                return (lat, lon)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP lors du géocodage ({e.response.status_code}): {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Erreur réseau lors du géocodage : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du géocodage : {e}")
            return None
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Valide des coordonnées GPS.
        
        Args:
            latitude: Latitude (doit être entre -90 et 90)
            longitude: Longitude (doit être entre -180 et 180)
            
        Returns:
            True si valides, False sinon
            
        Example:
            >>> geocoding.validate_coordinates(48.8566, 2.3522)  # Paris
            True
            >>> geocoding.validate_coordinates(100, 2.3522)  # Invalide
            False
        """
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False
        
        if latitude < -90 or latitude > 90:
            return False
        
        if longitude < -180 or longitude > 180:
            return False
        
        return True