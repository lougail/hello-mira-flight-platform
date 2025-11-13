# Test pour vérifier que Python fonctionne
print("Hello depuis le service Airport !")
print("Python fonctionne correctement ✅")

# Test des imports de base
try:
    import json
    import datetime
    print("Imports de base : OK ✅")
except ImportError as e:
    print(f"Erreur import : {e} ❌")