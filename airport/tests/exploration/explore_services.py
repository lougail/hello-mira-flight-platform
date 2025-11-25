"""
Tests rapides pour les services.
"""
import sys
from pathlib import Path

# Ajoute le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import CacheService, GeocodingService, AirportService


def test_imports():
    """Teste que tous les services s'importent correctement."""
    print("✅ CacheService importé")
    print("✅ GeocodingService importé")
    print("✅ AirportService importé")


def test_geocoding_distance():
    """Teste le calcul de distance (Paris -> Londres)."""
    geocoding = GeocodingService()
    
    # Paris: 48.8566, 2.3522
    # Londres: 51.5074, -0.1278
    distance = geocoding.calculate_distance(
        48.8566, 2.3522,
        51.5074, -0.1278
    )
    
    # Distance réelle : ~344 km
    print(f"Distance Paris-Londres : {distance:.1f} km")
    assert 340 < distance < 350, f"Distance incorrecte : {distance}"
    print("✅ Calcul de distance correct")


def test_geocoding_validate():
    """Teste la validation des coordonnées."""
    geocoding = GeocodingService()
    
    # Valides
    assert geocoding.validate_coordinates(48.8566, 2.3522) == True
    assert geocoding.validate_coordinates(0, 0) == True
    assert geocoding.validate_coordinates(-90, -180) == True
    assert geocoding.validate_coordinates(90, 180) == True
    
    # Invalides
    assert geocoding.validate_coordinates(91, 0) == False
    assert geocoding.validate_coordinates(0, 181) == False
    assert geocoding.validate_coordinates("48", "2") == False # type: ignore
    
    print("✅ Validation des coordonnées correcte")


def test_cache_service_structure():
    """Teste la structure du CacheService (sans MongoDB)."""
    # Test sans collection MongoDB (juste la structure)
    cache = CacheService(collection=None, ttl=300)
    
    assert cache.ttl == 300
    assert cache.collection is None
    
    print("✅ CacheService structure correcte")


def test_airport_service_structure():
    """Teste que AirportService s'initialise correctement."""
    # On ne peut pas tester sans client, mais on vérifie la structure
    from services.airport_service import AirportService
    
    # Vérifie que la classe existe et a les bonnes méthodes
    assert hasattr(AirportService, 'get_airport_by_iata')
    assert hasattr(AirportService, 'find_nearest_airport')
    assert hasattr(AirportService, 'get_departures')
    
    print("✅ AirportService structure correcte")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("TESTS RAPIDES DES SERVICES")
    print("="*50 + "\n")
    
    try:
        test_imports()
        test_geocoding_distance()
        test_geocoding_validate()
        test_cache_service_structure()
        test_airport_service_structure()
        
        print("\n" + "="*50)
        print("✅ TOUS LES TESTS PASSENT !")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        exit(1)