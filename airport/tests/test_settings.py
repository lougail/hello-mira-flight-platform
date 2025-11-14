"""Test de la configuration."""
import sys
from pathlib import Path

# Ajoute le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

def test_config():
    """Teste le chargement de la configuration."""
    print("=" * 50)
    print("TEST DE CONFIGURATION")
    print("=" * 50)
    
    # Infos de base
    print(f"\n✅ Configuration chargée avec succès !")
    print(f"   App: {settings.app_name}")
    print(f"   Version: {settings.app_version}")
    print(f"   Debug: {settings.debug}")
    
    # API
    print(f"\n🔑 API Aviationstack:")
    print(f"   Clé: {settings.aviationstack_api_key[:8]}...")
    print(f"   URL: {settings.aviationstack_base_url}")
    print(f"   Timeout: {settings.aviationstack_timeout}s")
    
    # MongoDB
    print(f"\n🗄️ MongoDB:")
    print(f"   URI: {settings.mongodb_uri_safe}")
    print(f"   Database: {settings.mongodb_database}")
    
    # Cache
    print(f"\n💾 Cache:")
    print(f"   TTL: {settings.cache_ttl}s ({settings.cache_ttl // 60} minutes)")
    
    # Validation
    print(f"\n🔍 Validation:")
    validation = settings.validate_config()
    for check, result in validation.items():
        emoji = "✅" if result else "❌"
        print(f"   {emoji} {check}: {result}")
    
    # Résultat final
    all_ok = all(validation.values())
    print(f"\n{'=' * 50}")
    if all_ok:
        print("✅ TOUS LES TESTS PASSENT !")
    else:
        print("❌ CERTAINS TESTS ÉCHOUENT")
    print("=" * 50)
    
    return all_ok

if __name__ == "__main__":
    success = test_config()
    exit(0 if success else 1)