"""
Test pour comprendre la structure exacte des réponses Aviationstack.
On va mapper nos modèles Pydantic sur la VRAIE structure.
"""

import httpx
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Charge le .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
BASE_URL = "http://api.aviationstack.com/v1"

def test_airport_structure():
    """Teste la structure de /airports."""
    print("\n" + "="*50)
    print("TEST STRUCTURE AIRPORT")
    print("="*50)
    
    # Essayons différents paramètres
    attempts = [
        {"access_key": API_KEY, "limit": 1},  # Sans filtre
        {"access_key": API_KEY, "limit": 1, "iata_code": "CDG"},  # Avec code IATA
        {"access_key": API_KEY, "limit": 1, "search": "Charles"},  # Avec search
    ]
    
    for i, params in enumerate(attempts, 1):
        print(f"\n🔍 Tentative {i} avec params: {params}")
        response = httpx.get(f"{BASE_URL}/airports", params=params)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Erreur API: {data['error']}")
        elif "data" in data and data["data"]:
            airport = data["data"][0]
            print("\n✅ Structure d'un Airport trouvée :")
            print(json.dumps(airport, indent=2))
            
            print("\n🔑 Clés disponibles :")
            for key in airport.keys():
                print(f"  - {key}: {type(airport[key]).__name__}")
            
            return data
        else:
            print(f"⚠️ Pas de données : {data}")
    
    return None

def test_flight_structure():
    """Teste la structure de /flights."""
    print("\n" + "="*50)
    print("TEST STRUCTURE FLIGHT")
    print("="*50)
    
    response = httpx.get(
        f"{BASE_URL}/flights",
        params={
            "access_key": API_KEY,
            "limit": 1
        }
    )
    
    data = response.json()
    
    # Affiche la structure
    if "data" in data and data["data"]:
        flight = data["data"][0]
        print("\n📋 Structure d'un Flight :")
        print(json.dumps(flight, indent=2))
        
        print("\n🔑 Clés principales :")
        for key in flight.keys():
            value_type = type(flight[key]).__name__
            if value_type == "dict":
                print(f"  - {key}: dict avec {len(flight[key])} clés")
            else:
                print(f"  - {key}: {value_type}")
    
    return data

if __name__ == "__main__":
    try:
        airport_data = test_airport_structure()
        flight_data = test_flight_structure()
        
        # Sauvegarde pour analyse
        with open("results/airport_response_sample.json", "w") as f:
            json.dump(airport_data, f, indent=2)
        
        with open("results/flight_response_sample.json", "w") as f:
            json.dump(flight_data, f, indent=2)
            
        print("\n✅ Samples sauvegardés dans :")
        print("  - airport_response_sample.json")
        print("  - flight_response_sample.json")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")