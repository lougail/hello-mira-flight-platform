# 🎬 Script de Démonstration - Hello Mira Flight Platform

**Durée** : 12-15 minutes

**Objectif** : Démontrer l'architecture, les optimisations, et l'IA conversationnelle

---

## 📋 Checklist Pré-Démonstration

### ✅ Avant de Commencer

- [ ] Services démarrés : `docker-compose ps` (tous "Up (healthy)")
- [ ] Grafana accessible : <http://localhost:3000> (admin/admin)
- [ ] Terminal prêt avec commandes curl
- [ ] Navigateur avec 4 onglets ouverts :
  - <http://localhost:8001/docs> (Airport API)
  - <http://localhost:8002/docs> (Flight API)
  - <http://localhost:8003/docs> (Assistant API)
  - <http://localhost:3000> (Grafana)

### ⚙️ Si Services Non Démarrés

```bash
cd hello-mira-flight-platform
docker-compose up -d
sleep 30  # Attendre health checks
docker-compose ps  # Vérifier tous "Up (healthy)"
```

---

## 🎯 Partie 1 : Architecture & Choix Techniques (3-4 min)

### 1.1 Vue d'Ensemble (1 min)

**À dire** :

"J'ai conçu une plateforme intelligente pour voyageurs avec 3 microservices :

- **Airport** : Recherche d'aéroports (GPS, adresse, IATA)
- **Flight** : Statut temps réel + historique + statistiques
- **Assistant** : IA conversationnelle avec LangGraph et Mistral"

**À montrer** :

```bash
# Montrer docker-compose.yml
code docker-compose.yml  # Scroller jusqu'aux services

# Compter les services
docker-compose ps
```

**Pointer** :

- 6 conteneurs (3 APIs + MongoDB + Prometheus + Grafana)
- Health checks sur tous les services
- Dépendances gérées (depends_on + condition: service_healthy)

### 1.2 Stack Technique (1 min)

**À dire** :

"Stack moderne 2025 :

- **FastAPI** 0.122.0 avec **Pydantic** pour validation
- **MongoDB** pour cache + persistance
- **LangGraph** 1.0.3 (orchestration IA - production ready depuis nov 2025)
- **httpx** async pour toutes les requêtes HTTP
- **Prometheus + Grafana** pour monitoring temps réel"

**Montrer** :

```bash
# Versions dans requirements.txt
cat airport/requirements.txt | grep -E "fastapi|pydantic|httpx"
cat assistant/requirements.txt | grep -E "langgraph|langchain"
```

### 1.3 Choix Architecturaux Clés (1-2 min)

**À expliquer** :

1. **Pourquoi microservices ?**
   - Séparation responsabilités
   - Scalabilité indépendante
   - Tests isolés

2. **Pourquoi MongoDB ?**
   - Cache flexible (TTL natif)
   - Pas de schéma rigide (API externe peut changer)
   - Index composites performants

3. **Pourquoi LangGraph ?**
   - Orchestration multi-agents (7 outils)
   - Production-ready (v1.0 stable)
   - Meilleur que LangChain pour workflows complexes

---

## 🔧 Partie 2 : Démonstration API (4-5 min)

### 2.1 Airport Service (1.5 min)

**Ouvrir** : <http://localhost:8001/docs>

**Demo 1 - Recherche par IATA** :

```bash
curl http://localhost:8001/api/v1/airports/CDG | python -m json.tool
```

**Pointer** :

- Réponse rapide (cache ou API)
- Coordonnées GPS précises
- Timezone Europe/Paris

**Demo 2 - Recherche par GPS** :

```bash
curl "http://localhost:8001/api/v1/airports/nearest-by-coords?latitude=48.8566&longitude=2.3522&country_code=FR"
```

**À dire** :

"Recherche par coordonnées GPS : trouve l'aéroport le plus proche dans le pays spécifié"

**Demo 3 - Vols au départ** :

```bash
curl "http://localhost:8001/api/v1/airports/CDG/departures?limit=3" | python -m json.tool
```

**Pointer** :

- Liste paginée (limit/offset)
- Statut en temps réel
- Retards calculés

### 2.2 Flight Service (1.5 min)

**Ouvrir** : <http://localhost:8002/docs>

**Demo 4 - Statut vol** :

```bash
curl http://localhost:8002/api/v1/flights/AF282 | python -m json.tool
```

**Pointer** :

- Départ + Arrivée complets
- Terminal, gate, retard
- Données enrichies vs Airport

**Demo 5 - Statistiques** :

```bash
curl "http://localhost:8002/api/v1/flights/AF282/statistics?start_date=2025-10-01&end_date=2025-11-27" | python -m json.tool
```

**À dire** :

"Agrégations MongoDB : taux ponctualité, retard moyen, annulations"

### 2.3 Assistant IA (1-2 min)

**Ouvrir** : <http://localhost:8003/docs>

**Demo 6 - Question en langage naturel** :

```bash
curl -X POST "http://localhost:8003/api/v1/assistant/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Je suis sur le vol AF282, à quelle heure j'\''arrive ?"}'
```

**Pointer** :

- Réponse en français naturel
- Données structurées extraites
- Orchestration transparente

**Demo 7 - Interprétation seule** :

```bash
curl -X POST "http://localhost:8003/api/v1/assistant/interpret" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Trouve-moi l'\''aéroport le plus proche de Lille"}'
```

**À dire** :

"Intent detection : comprend ce que l'utilisateur veut sans exécuter"

---

## 🚀 Partie 3 : Optimisations & Performance (3-4 min)

### 3.1 Problème à Résoudre (30 sec)

**À expliquer** :

"Challenge : API Aviationstack plan gratuit = 100 calls/mois
Application temps réel = centaines de requêtes/jour

Solution : Cache intelligent + Request Coalescing"

### 3.2 Démonstration Monitoring (2 min)

**Ouvrir** : <http://localhost:3000> (Grafana)

**Naviguer** : Dashboard "Hello Mira - Flight Platform Metrics"

**Montrer les 5 sections** :

1. **⚡ Temps Réel (5 min)** :
   - Cache Hit Rate Airport : **~65%**
   - Cache Hit Rate Flight : **~65%**
   - Taux Coalescing : **~27%**

2. **📊 Cumulatif** :
   - Total Cache Hits
   - Total Requêtes Coalescées
   - Économie visualisée

3. **📊 Performance** :
   - Latence p50 / p95
   - Requêtes HTTP/sec

4. **🤖 Assistant IA** :
   - Taux succès 100%
   - Latence médiane

5. **🌐 Quota API** :
   - Total appels Aviationstack
   - Répartition par endpoint

**À dire** :

"Résultat mesuré : **~70% d'économie d'appels API** grâce à cache + coalescing combinés"

### 3.3 Test Live Performance (1-2 min)

**Si temps disponible** :

```bash
# Générer du trafic
./scripts/generate_traffic_intensive.sh 50

# Attendre 15s (scraping Prometheus)
sleep 15

# Rafraîchir Grafana et montrer :
# - Cache hits augmentent
# - Coalescing détecte doublons
# - API calls limités
```

**Sinon** : Montrer les résultats déjà capturés dans README ligne 1100-1110

---

## 🤖 Partie 4 : IA Conversationnelle - LangGraph (2-3 min)

### 4.1 Architecture LangGraph (1 min)

**Montrer** : `assistant/agents/assistant_agent.py`

**Expliquer** :

"LangGraph = orchestrateur multi-agents

- **7 outils** exposés au LLM (5 airport + 2 flight)
- **Graph stateful** : mémorisation entre appels
- **Mistral AI** avec function calling natif
- **Multi-langue** : Détecte automatiquement FR/EN/ES et répond dans la même langue
- **Enrichissement pays** : Données de vol avec `arrival_country` pour filtrer par destination"

**Schéma mental** :

```text
User Prompt → Interpret → Select Tool → Execute → Format Answer
```

### 4.2 Outils Disponibles (1 min)

**Lister** :

```bash
# Voir les outils
cat assistant/tools/airport_tools.py | grep "@tool"
cat assistant/tools/flight_tools.py | grep "@tool"
```

**7 outils** :

1. `get_airport_by_iata` - Recherche par code IATA
2. `search_airports` - Recherche par nom/ville
3. `get_nearest_airport` - Aéroport le plus proche (GPS ou adresse)
4. `get_departures` - Vols au départ d'un aéroport
5. `get_arrivals` - Vols à l'arrivée d'un aéroport
6. `get_flight_status` - Statut d'un vol
7. `get_flight_statistics` - Statistiques d'un vol

### 4.3 Mode DEMO (30 sec)

**À expliquer** :

"Mode DEMO activable pour tests sans consommer quota API :

- Données mockées cohérentes (3 aéroports, 2 vols)
- Réponses instantanées
- Idéal pour démonstrations/développement"

```bash
# Vérifier mode DEMO
docker-compose logs assistant | grep "DEMO MODE"
```

---

## ✅ Partie 5 : Tests & Qualité (1-2 min)

### 5.1 Tests End-to-End (1 min)

**À dire** :

"16 tests e2e - 100% passent :

- 4 tests Airport (IATA, coords, cache)
- 6 tests Flight (status, history, stats, coalescing)
- 6 tests Assistant (orchestration complète)"

**Montrer** :

```bash
# Si temps : lancer les tests
pytest tests/e2e/ -v

# Sinon : montrer résultats dans README
```

### 5.2 CI/CD Ready (30 sec)

**Pointer** :

- Health checks sur tous services
- Tests automatisables
- Docker Compose isolation
- Prêt pour GitHub Actions

---

## 🎤 Questions Fréquentes & Réponses Rapides

### Q1 : "Pourquoi pas Redis pour le cache ?"

**R** : MongoDB offre :

- TTL natif sur collections
- Requêtes complexes (stats, historique)
- Un seul système pour cache + persistance

### Q2 : "Comment gérer la montée en charge ?"

**R** :

- Microservices scalables indépendamment
- Cache réduit charge API externe
- MongoDB sharding si besoin
- Load balancer devant APIs

### Q3 : "Sécurité des API keys ?"

**R** :

- `.env` non versionné (`.gitignore`)
- Variables d'environnement Docker
- En prod : secrets management (Vault, AWS Secrets)

### Q4 : "Que se passe-t-il si Aviationstack tombe ?"

**R** :

- Cache sert données récentes (TTL 5 min)
- Mode DEMO comme fallback
- Logs d'erreur structurés
- Health checks détectent problème

---

## 🎯 Conclusion (30 sec)

**Message clé** :

"Plateforme production-ready qui combine :

- Architecture microservices moderne
- Optimisations mesurées (70% économie API)
- IA conversationnelle avec LangGraph
- Monitoring temps réel Prometheus/Grafana
- Tests automatisés complets"

**Dernière phrase** :

"Prêt pour questions techniques !"

---

## 📊 Timing Breakdown

| Section | Durée | Pourcentage |
|---------|-------|-------------|
| 1. Architecture | 3-4 min | 25% |
| 2. API Demo | 4-5 min | 33% |
| 3. Optimisations | 3-4 min | 25% |
| 4. LangGraph | 2-3 min | 17% |
| 5. Tests | 1-2 min | 8% |
| **TOTAL** | **13-18 min** | **108%** |

**Ajustement** : Sauter section 5 si temps limité à 15 min.

---

## 🔧 Troubleshooting Live Demo

### Si un service est down

```bash
docker-compose restart <service>
sleep 15
```

### Si Grafana ne montre pas de données

```bash
# Vérifier Prometheus scrape
curl http://localhost:9090/api/v1/targets

# Regénérer du trafic
./scripts/generate_traffic_intensive.sh 20
sleep 15
```

### Si API retourne erreur

- **429 quota** → Activer mode DEMO
- **Connection refused** → Vérifier MongoDB health
- **Timeout** → Services pas encore ready

---

## 📝 Notes pour la Présentation

### ✅ À Faire

- Parler lentement et clairement
- Expliquer le "pourquoi" avant le "comment"
- Montrer le code seulement si demandé
- Valoriser les choix techniques originaux

### ❌ À Éviter

- Trop de détails techniques non demandés
- Lire les slides/code
- S'excuser pour ce qui manque
- Minimiser le travail accompli

### 💡 Points de Différenciation

1. **LangGraph 1.0** (très récent, production-ready)
2. **Request Coalescing** (pattern avancé, rare)
3. **Monitoring complet** (19 panels, 5 sections)
4. **Tests e2e 100%** (qualité démontrée)
5. **Documentation exhaustive** (README 1400+ lignes)
