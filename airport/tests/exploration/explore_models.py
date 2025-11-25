"""
Test des modèles Pydantic avec les vraies données API.
Vérifie que tout parse correctement.
"""

import json
from pathlib import Path
import sys

# Ajoute le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    Airport, Flight, FlightStatus,
    AirportApiResponse, FlightApiResponse
)


def test_airport_models():
    """Teste les modèles Airport avec vraies données."""
    print("\n" + "="*50)
    print("TEST MODÈLES AIRPORT")
    print("="*50)
    
    # Charge les vraies données
    with open("results/airport_response_sample.json", "r") as f:
        response = json.load(f)
    
    if response and "data" in response and response["data"]:
        raw_airport = response["data"][0]
        print(f"\n📋 Données brutes : {raw_airport['airport_name']}")
        
        # Test 1 : Parse en modèle API
        try:
            api_model = AirportApiResponse(**raw_airport)
            print(f"✅ Modèle API créé : {api_model.iata_code}")
        except Exception as e:
            print(f"❌ Erreur modèle API : {e}")
            return False
        
        # Test 2 : Conversion en modèle domaine
        try:
            domain_model = Airport.from_api_response(raw_airport)
            print(f"✅ Modèle domaine créé : {domain_model.name}")
            print(f"   - Coordonnées : {domain_model.coordinates.latitude}, {domain_model.coordinates.longitude}")
            print(f"   - Timezone : {domain_model.timezone}")
        except Exception as e:
            print(f"❌ Erreur modèle domaine : {e}")
            return False
        
        # Test 3 : Validation des types
        assert isinstance(domain_model.coordinates.latitude, float), "Latitude doit être float"
        assert isinstance(domain_model.coordinates.longitude, float), "Longitude doit être float"
        assert domain_model.iata_code == domain_model.iata_code.upper(), "IATA doit être en majuscules"
        
        print("✅ Tous les tests Airport passent !")
        return True
    else:
        print("❌ Pas de données airport dans le sample")
        return False


def test_flight_models():
    """Teste les modèles Flight avec vraies données."""
    print("\n" + "="*50)
    print("TEST MODÈLES FLIGHT")
    print("="*50)
    
    # Charge les vraies données
    with open("results/flight_response_sample.json", "r") as f:
        response = json.load(f)
    
    if response and "data" in response and response["data"]:
        raw_flight = response["data"][0]
        print(f"\n📋 Vol : {raw_flight['flight']['iata']}")
        
        # Test 1 : Parse en modèle API
        try:
            api_model = FlightApiResponse(**raw_flight)
            print(f"✅ Modèle API créé : {api_model.flight.iata}")
            print(f"   - Status : {api_model.flight_status}")
            print(f"   - Départ : {api_model.departure.airport}")
            print(f"   - Arrivée : {api_model.arrival.airport}")
        except Exception as e:
            print(f"❌ Erreur modèle API : {e}")
            return False
        
        # Test 2 : Conversion en modèle domaine
        try:
            domain_model = Flight.from_api_response(raw_flight)
            print(f"✅ Modèle domaine créé : {domain_model.flight_iata}")
            print(f"   - Status : {domain_model.status}")
            print(f"   - Route : {domain_model.departure_airport} → {domain_model.arrival_airport}")
        except Exception as e:
            print(f"❌ Erreur modèle domaine : {e}")
            return False
        
        # Test 3 : Test de l'enum
        assert isinstance(domain_model.status, FlightStatus), "Status doit être un FlightStatus"
        print(f"   - Enum status valide : {domain_model.status.value}")
        
        print("✅ Tous les tests Flight passent !")
        return True
    else:
        print("❌ Pas de données flight dans le sample")
        return False


def test_validation():
    """Teste les validations Pydantic."""
    print("\n" + "="*50)
    print("TEST VALIDATIONS")
    print("="*50)
    
    from models import Coordinates
    
    # Test 1 : Coordonnées valides
    try:
        coords = Coordinates(latitude=48.8566, longitude=2.3522)
        print(f"✅ Coordonnées Paris valides")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    
    # Test 2 : Latitude invalide
    try:
        coords = Coordinates(latitude=91, longitude=2.3522)
        print(f"❌ Latitude 91 aurait dû échouer !")
    except Exception as e:
        print(f"✅ Validation correcte : latitude > 90 rejetée")
    
    # Test 3 : Codes IATA
    from models import Airport
    
    # Test avec minuscules (doit être converti)
    test_data = {
        "iata_code": "cdg",  # minuscules
        "icao_code": "lfpg", # minuscules
        "name": "Charles de Gaulle",
        "city": "Paris",
        "country": "France",
        "country_code": "fr",  # minuscules
        "coordinates": {"latitude": 49.0097, "longitude": 2.5479},
        "timezone": "Europe/Paris"
    }
    
    try:
        airport = Airport(**test_data)
        assert airport.iata_code == "CDG", "IATA doit être en majuscules"
        assert airport.icao_code == "LFPG", "ICAO doit être en majuscules"
        assert airport.country_code == "FR", "Country code doit être en majuscules"
        print(f"✅ Conversion majuscules OK : {airport.iata_code}")
    except Exception as e:
        print(f"❌ Erreur conversion : {e}")
    
    print("✅ Toutes les validations passent !")
    return True


if __name__ == "__main__":
    print("\n🚀 TEST COMPLET DES MODÈLES")
    
    # Lance tous les tests
    results = {
        "Airport": test_airport_models(),
        "Flight": test_flight_models(),
        "Validation": test_validation()
    }
    
    # Résumé
    print("\n" + "="*50)
    print("RÉSUMÉ DES TESTS")
    print("="*50)
    
    for test_name, success in results.items():
        emoji = "✅" if success else "❌"
        print(f"{emoji} {test_name}: {'PASS' if success else 'FAIL'}")
    
    # Code de sortie
    all_pass = all(results.values())
    if all_pass:
        print("\n🎉 TOUS LES TESTS PASSENT !")
        exit(0)
    else:
        print("\n❌ CERTAINS TESTS ÉCHOUENT")
        exit(1)