import os
from pathlib import Path

# Remonte d'un niveau pour lire le .env
env_path = Path("../.env")

# Lit le fichier .env manuellement (méthode simple)
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith("AVIATIONSTACK_API_KEY"):
                # Extrait la clé
                api_key = line.split("=")[1].strip()
                print(f"✅ Clé trouvée : {api_key[:10]}...")
                break
else:
    print("❌ Fichier .env non trouvé !")
    api_key = None

# Test simple de l'API
if api_key:
    print("\n📡 Test de connexion à Aviationstack...")
    print("(On fera le vrai test après)")
else:
    print("⚠️ Pas de clé API")