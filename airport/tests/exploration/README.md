# Scripts d'Exploration - Airport Service

## 📋 Contexte

Ces scripts **ne sont PAS des tests automatisés**. Ils ont été utilisés pendant le développement pour explorer empiriquement l'API Aviationstack et valider la structure des données.

## 🎯 Objectif

Conformément à la méthodologie "**Toujours Tester Avant de Coder**" (voir `CLAUDE.md`), ces scripts permettent de :

1. **Découvrir la vraie structure** de l'API externe sans se fier uniquement à la documentation
2. **Valider les hypothèses** sur les modèles Pydantic
3. **Identifier les champs disponibles** et leurs types
4. **Générer des samples JSON** pour les tests unitaires (voir `../mocks/`)

## 📁 Scripts Disponibles

### `explore_settings.py`

- Valide le chargement de la configuration
- Vérifie les variables d'environnement
- Teste la connexion MongoDB

**Usage** :

```bash
cd airport
python tests/exploration/explore_settings.py
```

### `explore_api_structure.py`

- Interroge l'API Aviationstack réelle
- Affiche la structure exacte des réponses JSON
- Sauvegarde des samples dans `../mocks/`

**Usage** :

```bash
cd airport
python tests/exploration/explore_api_structure.py
```

**Génère** :

- `mocks/airport_response_sample.json`
- `mocks/flight_response_sample.json`

### `explore_models.py`

- Teste le mapping Pydantic ↔ API Aviationstack
- Valide que les modèles correspondent à la vraie structure

### `explore_client.py`

- Teste le client Aviationstack
- Valide les appels HTTP
- Vérifie la gestion des erreurs

### `explore_services.py`

- Teste les services (cache, geocoding, etc.)
- Valide les interactions MongoDB
- Vérifie les transformations de données

## ⚠️ Important

- Ces scripts font des **appels API réels** (consomme le quota Aviationstack)
- Ils ne sont **pas exécutés par pytest** (nom `explore_*` au lieu de `test_*`)
- Ils servent de **documentation empirique** de la démarche de développement

## 🔗 Relation avec les Tests

Ces scripts ont permis de créer :

1. **Mock data** dans `../mocks/` pour tests unitaires
2. **Fixtures** réalistes dans `../conftest.py`
3. **Modèles Pydantic** validés dans `../../models/`

## 📚 Voir Aussi

- Tests unitaires : `../unit/`
- Tests d'intégration : `../integration/`
- Documentation méthodologie : `../../../CLAUDE.md`
