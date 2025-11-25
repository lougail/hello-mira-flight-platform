# Scripts d'Exploration - Flight Service

## 📋 Contexte

Ces scripts **ne sont PAS des tests automatisés**. Ils ont été utilisés pendant le développement pour explorer empiriquement l'API Aviationstack (endpoint /flights) et valider les fonctionnalités du service Flight.

## 🎯 Objectif

Conformément à la méthodologie "**Toujours Tester Avant de Coder**" (voir `CLAUDE.md`), ces scripts permettent de :

1. **Découvrir la structure** des données de vols (statuts, horaires, retards)
2. **Tester les calculs** de statistiques (taux de retard, durée moyenne)
3. **Valider l'historique** MongoDB (insertion, requêtes temporelles)
4. **Vérifier les edge cases** (vols annulés, changements de statut)

## 📁 Scripts Potentiels

> **Note** : Cette structure est préparée pour accueillir des scripts d'exploration futurs.

### Exemples de scripts utiles :

- `explore_flight_status.py` : Tester les différents statuts de vol
- `explore_statistics.py` : Valider les calculs d'agrégation
- `explore_history.py` : Tester l'insertion et requêtes historique
- `explore_cache.py` : Vérifier le comportement du cache pour les vols

## 🔬 Méthodologie Empirique

Pour le service Flight, l'approche empirique est particulièrement importante pour :

1. **Statuts de vol** : Comprendre quels champs sont présents selon le statut
   - Vol "scheduled" : seulement horaires prévus
   - Vol "active" : position actuelle, vitesse, altitude
   - Vol "landed" : horaires réels, retards calculés

2. **Calculs de retard** : Vérifier la logique
   - Retard au départ vs retard à l'arrivée
   - Gestion des valeurs négatives (avance)
   - Vols sans données réelles (null)

3. **Historique** : Tester les requêtes temporelles
   - Filtres par date (start_date, end_date)
   - Agrégations MongoDB (avg, min, max)
   - Gestion des doublons

## ⚠️ Important

- Ces scripts font des **appels API réels** (consomme le quota Aviationstack)
- Ils ne sont **pas exécutés par pytest** (nom `explore_*` au lieu de `test_*`)
- Ils servent de **documentation empirique** du processus de développement

## 🔗 Relation avec les Tests

Ces scripts ont permis de créer :

1. **Mock data** dans `../mocks/` pour tests unitaires
2. **Fixtures** réalistes dans `../conftest.py`
3. **Logique métier** validée dans `../../services/flight_service.py`
4. **Modèles de calcul** pour statistiques dans `../../services/flight_service.py`

## 📚 Voir Aussi

- Tests unitaires : `../unit/`
- Tests d'intégration : `../integration/`
- Service Flight : `../../services/flight_service.py`
- Documentation méthodologie : `../../../CLAUDE.md`
