import urllib.request
import urllib.error
import json
from pathlib import Path

# Lit la clé depuis le .env
api_key = None
env_path = Path("../.env")

if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("AVIATIONSTACK_API_KEY"):
                api_key = line.split("=")[1].strip()
                break

# VÉRIFICATION que la clé existe avant de l'utiliser
if not api_key:
    print("❌ Clé API non trouvée dans le fichier .env")
    exit()

# Maintenant on est sûr que api_key n'est pas None
print(f"📌 Clé utilisée : {api_key[:10]}... (longueur: {len(api_key)})")

# URL simple pour tester
url = f"http://api.aviationstack.com/v1/flights?access_key={api_key}&limit=1"

print(f"\n🔍 Test de l'endpoint /flights avec limit=1...")

try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    print("✅ API fonctionne !")
    
    if 'pagination' in data:
        print(f"Total disponible : {data['pagination'].get('total', 0)} vols")
    
    if 'data' in data and len(data['data']) > 0:
        print(f"Premier vol trouvé : {data['data'][0].get('flight', {}).get('iata', 'N/A')}")
    else:
        print("Aucune donnée de vol disponible")
        
except urllib.error.HTTPError as e:
    print(f"❌ Erreur HTTP {e.code} : {e.reason}")
    if e.code == 403:
        print("\n⚠️ Erreur 403 : Accès refusé")
        print("Possible que le plan gratuit ne donne pas accès aux données temps réel")