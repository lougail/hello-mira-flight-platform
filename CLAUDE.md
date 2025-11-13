# 🚀 Hello Mira - Références du Projet

## 📍 Liens Essentiels

### GitHub

**Repo principal :** <https://github.com/lougail/hello-mira-flight-platform>

### Notion

**Documentation restitution :** <https://www.notion.so/Test-Technique-Hello-Mira-Restitution-2aafac9ba33881c4a959d082b5288f79>

**Pages Notion :**

- 🤔 Analyse & Réflexion Initiale : <https://www.notion.so/2aafac9ba33881a489fddfcbccee785c>
- 🏗️ Choix Architecturaux : <https://www.notion.so/2aafac9ba33881599008c9081f6a1515>
- 💡 Solutions Techniques : <https://www.notion.so/2aafac9ba33881519c30f2161cbcb88f>
- 🚧 Défis & Résolutions : <https://www.notion.so/2aafac9ba33881edaa93d85eed46e38a>
- 📈 Métriques & Performance : <https://www.notion.so/2aafac9ba33881cbb63cca5ff8f22d85>
- 🔮 Vision & Évolutions : <https://www.notion.so/2aafac9ba33881de8b00dd0e5050d6c1>
- 💬 Q&A Préparation : <https://www.notion.so/2aafac9ba338817d8a8ed6521b57daa2>

### API Externe

**Aviationstack :** <https://aviationstack.com>
**Clé API :** Stockée dans `.env` (commence par 858189fdc6...)

---

## 📊 État Actuel du Projet

**Dernière mise à jour :** 13 novembre 2024

### ✅ Fait

- Structure dossiers créée
- Configuration (.env, .gitignore)
- API Aviationstack testée et validée (77020 vols accessibles)
- 3 fichiers de test créés dans `airport/`:
  - `test_simple.py` - Vérification Python
  - `test_api.py` - Lecture clé .env
  - `test_api_reel.py` - Test API réel

### 🔄 En Cours

- **Partie 1 : Microservice Airport**
  - Décision architecture en cours (Options A/B/C)

### ⏳ À Faire

- Partie 2 : Microservice Flight
- Partie 3 : Optimisations (cache, async, coalescing)
- Partie 4 : Assistant IA
- Bonus : Frontend React

---

## 🎯 Restitution

**Date :** 26 ou 28 novembre 2024
**Jury :**

- Cédric (CEO)
- Pavlo (CTO)
- Lorenzo (Senior Dev)

**Focus évaluation :**

- Démarche et construction
- Capacité à expliquer
- Rigueur du design API
- Originalité

---

## 📝 Notes Importantes

### Process de Travail

1. ✅ Toujours documenter les décisions dans Notion
2. ✅ Expliquer le POURQUOI, pas juste le COMMENT
3. ✅ Faire des commits Git propres avec messages clairs
4. ✅ Tester chaque feature avant de passer à la suivante

### Règles Git

🚫 **Claude ne fait JAMAIS de commandes git**
✅ **Claude donne les commandes à Louis avec explications**

# Test Technique - Hello Mira

Hello Mira dÃ©veloppe une **plateforme intelligente pour les voyageurs**, combinant IA et donnÃ©es contextuelles (vols, destinations, sÃ©curitÃ©, mÃ©tÃ©o...).

Ce test Ã©value ta capacitÃ© Ã  concevoir, implÃ©menter et intÃ©grer plusieurs microservices cohÃ©rents - tout en ajoutant une couche d'intelligence conversationnelle.

## Stack imposÃ©e

| Composant | Technologie |
|-----------|-------------|
| Backend | Python â€“ FastAPI (REST) |
| Base de donnÃ©es | MongoDB |
| Authentification | Supabase |
| Frontend | React |
| API externe | [Aviationstack](https://aviationstack.com) |
| Gestion des secrets | .env |

## Livrables

1. **Code source complet** (/airport, /flight, /assistant, /frontend)
2. **README.md clair** (installation, variables, endpoints)
3. **Docker Compose** pour tout lancer
4. **Rendu** : lien github
5. **Collection Postman** ou requests.http
6. **Exemples de prompts et rÃ©ponses** (capture ou JSON)
7. **(Bonus) Interface React fonctionnelle**

## DÃ©roulÃ© du test

- RÃ©alise les partie 1 Ã  4 dans l'ordre
- Si tu te sens chaud, tu peux rÃ©aliser les bonus selon ton envie ou ton inspiration :-)
- Plus qu'un code qui fonctionne parfaitement, **l'originalitÃ© et la rigueur du design API seront valorisÃ©es**
- **Important** : Tu as le droit d'utiliser une IDE Argentique, mais tu dois pouvoir Ãªtre capable d'expliquer dans le dÃ©tail le code et le modifier.

---

## Partie 1 - Microservice airport

### Objectif

CrÃ©er un microservice permettant d'interroger les **aÃ©roports**.

### FonctionnalitÃ©s attendues

**Trouver un aÃ©roport :**

- Ã  proximitÃ© d'une **adresse** (gÃ©ocodage autorisÃ©)
- Ã  proximitÃ© de **coordonnÃ©es GPS**
- par **nom** ou **code IATA**

**Lister :**

- les **vols au dÃ©part** et leurs statuts
- les **vols Ã  l'arrivÃ©e** et leurs statuts

### API externe

Utilise **Aviationstack** (endpoints airports, flights).

### Optimisation

Cache MongoDB (TTL configurable) pour limiter les appels.

---

## Partie 2 - Microservice flight

### Objectif

CrÃ©er un microservice pour consulter les **vols** individuels.

### FonctionnalitÃ©s

- **Statut d'un vol** (en cours ou prÃ©vu)
- **Historique d'un vol** sur une pÃ©riode
- **Statistiques agrÃ©gÃ©es** : taux de retard, durÃ©e moyenne, etc.

### DonnÃ©es

Stocker localement les vols consultÃ©s pour l'historique.

---

## Partie 3 - Optimisation

### Objectif

AmÃ©liorer la **performance et le coÃ»t** des appels API.

### Exigences

- **Cache intelligent** (Mongo ou mÃ©moire)
- **Asynchronisme** (async/await, httpx)
- **Coalescing** : mutualiser les appels identiques simultanÃ©s
- **Logs de performance** : latence, hit-rate cache, nombre d'appels

---

## Partie 4 - Assistant IA : du prompt Ã  l'action

CrÃ©er un endpoint intelligent capable de comprendre une phrase en langage naturel, d'en dÃ©duire l'action et de rÃ©pondre Ã  l'utilisateur.

### Objectif

Ã€ partir d'un **prompt texte**, ton systÃ¨me doit :

1. **InterprÃ©ter** l'intention (vol, aÃ©roport, horaires, etc.)
2. **Extraire** les paramÃ¨tres utiles
3. **Appeler** les microservices correspondants
4. **GÃ©nÃ©rer** une rÃ©ponse claire (texte + donnÃ©es structurÃ©es)

### Exemples

| EntrÃ©e utilisateur | RÃ©sultat attendu |
|-------------------|------------------|
| "Je suis sur le vol AV15, Ã  quelle heure vais-je arriver ?" | ETA et statut du vol AV15 |
| "Quels vols partent de CDG cet aprÃ¨s-midi ?" | Liste des dÃ©parts Ã  CDG |
| "Trouve-moi l'aÃ©roport le plus proche de Lille" | Nom et code de l'aÃ©roport le plus proche |

### Endpoints

**POST /assistant/interpret**  
Renvoie un JSON d'intention.

**POST /assistant/answer**  
Orchestre : interprÃ©tation â†’ exÃ©cution â†’ rÃ©ponse textuelle.

### Sortie exemple

```json
{
  "answer": "Le vol AV15 est prÃ©vu Ã  21h47 (heure locale) avec un retard de 18 min.",
  "data": {
    "flight_number": "AV15",
    "scheduled_arrival": "2025-11-12T21:47:00Z",
    "estimated_arrival": "2025-11-12T22:05:00Z",
    "delay_minutes": 18
  }
}
```

---

## BONUS 1 - Interface conversationnelle (Frontend React)

### Objectif

CrÃ©er une interface web minimaliste qui permet :

1. **D'interagir par prompt texte** avec le backend :
   - un champ "Que voulez-vous savoir ?" envoie le prompt Ã  /assistant/answer
   - affichage de la rÃ©ponse textuelle + des donnÃ©es clÃ©s (heures, retards, aÃ©roport...)

2. **De naviguer visuellement** :
   - rechercher un aÃ©roport
   - consulter les vols au dÃ©part / Ã  l'arrivÃ©e
   - afficher le dÃ©tail d'un vol

### Bonus UX

- Historique local des prompts
- Animation de chargement
- Drapeau ou logo du pays d'arrivÃ©e/dÃ©part
- Mode sombre ðŸŒ™

### Technique

- Authentification Supabase (obligatoire)
- Communication via REST (fetch ou axios)
- Ã‰tat gÃ©rÃ© par React Query ou Zustand
- Architecture modulaire (components + hooks)

---

## BONUS 2 - Suivi asynchrone

Service ou tÃ¢che background qui met Ã  jour pÃ©riodiquement le statut d'un vol et notifie les changements.

---

## BONUS 3 - IA enrichie

AmÃ©liorer /assistant/interpret :

- prise en compte de l'historique de la session
- tolÃ©rance aux fautes de frappe ou alias d'aÃ©roports
- multi-langue (FR/EN)

---

## BONUS 4 - A toi de le proposer ;-)
