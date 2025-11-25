"""
Test du client Aviationstack avec de vraies données.
"""
import asyncio
import sys
from pathlib import Path

# Ajoute le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.aviationstack_client import AviationstackClient, AviationstackError


async def test_client():
    """Test les principales fonctions du client."""
    print("=" * 50)
    print("TEST CLIENT AVIATIONSTACK")
    print("=" * 50)
    
    async with AviationstackClient(enable_rate_limit=False) as client:
        # Test 1 : Récupérer un aéroport
        try:
            print("\n🔍 Test get_airport_by_iata('CDG')...")
            airport = await client.get_airport_by_iata("CDG")
            if airport:
                print(f"✅ Trouvé : {airport.name} ({airport.iata_code})")
                print(f"   Coordonnées : {airport.coordinates.latitude}, {airport.coordinates.longitude}")
            else:
                print("⚠️ Aéroport CDG non trouvé")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        # Test 2 : Rechercher des aéroports
        try:
            print("\n🔍 Test search_airports(country='FR', limit=3)...")
            airports = await client.search_airports(country="FR", limit=3)
            print(f"✅ Trouvé {len(airports)} aéroports français :")
            for ap in airports[:3]:
                print(f"   - {ap.iata_code}: {ap.name}")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        # Test 3 : Récupérer des vols
        try:
            print("\n🔍 Test get_flights(limit=2)...")
            flights = await client.get_flights(limit=2)
            print(f"✅ Trouvé {len(flights)} vols :")
            for flight in flights:
                print(f"   - {flight.flight_iata}: {flight.departure_airport} → {flight.arrival_airport}")
                print(f"     Status: {flight.status.value}")
        except Exception as e:
            print(f"❌ Erreur : {e}")
    
    print("\n" + "=" * 50)
    print("✅ TESTS TERMINÉS")
    print("=" * 50)


if __name__ == "__main__":
    # Lance le test async
    asyncio.run(test_client())