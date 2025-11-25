#!/bin/bash

# Test complet : Cache MongoDB + Request Coalescing
# Partie 3 - Optimisation du test technique Hello Mira

set -e

echo ""
echo "=========================================="
echo "🧪 TEST COMPLET : CACHE + COALESCING"
echo "Hello Mira Flight Platform"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour attendre et afficher un message
wait_and_show() {
    echo -e "${YELLOW}⏳ Attente de $1 secondes (scraping Prometheus)...${NC}"
    sleep $1
}

# ============================================================================
# PHASE 1 : TEST DU COALESCING (requêtes simultanées)
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1 : TEST DU COALESCING${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo "📌 Objectif : Vérifier que les requêtes simultanées identiques sont fusionnées"
echo ""

# Test 1.1 : Airport CDG - 10 requêtes simultanées
echo -e "${BLUE}Test 1.1 : 10 requêtes simultanées pour CDG (airport)${NC}"
echo "Attendu : 1 API call, 9 requêtes coalescées"
echo ""
start_time=$(date +%s)
for i in {1..10}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
wait
end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo -e "${GREEN}✅ 10 requêtes terminées en ${elapsed}s${NC}"
echo ""

wait_and_show 5

# Test 1.2 : Flight - 10 requêtes simultanées
echo -e "${BLUE}Test 1.2 : 10 requêtes simultanées pour AF447 (flight)${NC}"
echo "Attendu : 1 API call, 9 requêtes coalescées"
echo ""
start_time=$(date +%s)
for i in {1..10}; do
    curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
done
wait
end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo -e "${GREEN}✅ 10 requêtes terminées en ${elapsed}s${NC}"
echo ""

wait_and_show 5

# Test 1.3 : Mix de requêtes différentes
echo -e "${BLUE}Test 1.3 : Mix de requêtes (CDG×5 + JFK×5)${NC}"
echo "Attendu : 2 API calls (1 pour CDG, 1 pour JFK), 8 requêtes coalescées"
echo ""
start_time=$(date +%s)
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/JFK" > /dev/null &
done
wait
end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo -e "${GREEN}✅ 10 requêtes terminées en ${elapsed}s${NC}"
echo ""

wait_and_show 10

# ============================================================================
# PHASE 2 : TEST DU CACHE (requêtes séquentielles)
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2 : TEST DU CACHE MONGODB${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo "📌 Objectif : Vérifier que les requêtes répétées utilisent le cache"
echo "TTL configuré : 300s (5 minutes)"
echo ""

# Test 2.1 : Premier appel CDG (cache miss attendu)
echo -e "${BLUE}Test 2.1 : Premier appel ORY (cache MISS attendu)${NC}"
echo "Attendu : Cache miss, API call"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://localhost:8001/api/v1/airports/ORY")
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Status: 200 OK${NC}"
else
    echo -e "${RED}❌ Status: $http_code${NC}"
fi
echo ""

wait_and_show 3

# Test 2.2 : Deuxième appel immédiat (cache hit attendu)
echo -e "${BLUE}Test 2.2 : Deuxième appel ORY immédiat (cache HIT attendu)${NC}"
echo "Attendu : Cache hit, PAS d'API call"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://localhost:8001/api/v1/airports/ORY")
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ Status: 200 OK (devrait venir du cache)${NC}"
else
    echo -e "${RED}❌ Status: $http_code${NC}"
fi
echo ""

wait_and_show 3

# Test 2.3 : Série de requêtes identiques (toutes devraient utiliser le cache)
echo -e "${BLUE}Test 2.3 : 5 requêtes séquentielles ORY (toutes devraient HIT le cache)${NC}"
echo "Attendu : 5 cache hits, 0 API calls"
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/ORY" > /dev/null
    echo -n "."
    sleep 0.5
done
echo ""
echo -e "${GREEN}✅ 5 requêtes séquentielles terminées${NC}"
echo ""

wait_and_show 5

# Test 2.4 : Autre aéroport pour Flight service
echo -e "${BLUE}Test 2.4 : Cache test pour Flight (LH400)${NC}"
echo "Premier appel (MISS) puis second appel (HIT)"
curl -s "http://localhost:8002/api/v1/flights/LH400" > /dev/null
echo -n "."
sleep 2
curl -s "http://localhost:8002/api/v1/flights/LH400" > /dev/null
echo -n "."
sleep 2
curl -s "http://localhost:8002/api/v1/flights/LH400" > /dev/null
echo ""
echo -e "${GREEN}✅ 3 requêtes LH400 terminées${NC}"
echo ""

wait_and_show 10

# ============================================================================
# PHASE 3 : TEST COMBINÉ (cache + coalescing)
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3 : TEST COMBINÉ${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo "📌 Objectif : Vérifier que cache ET coalescing fonctionnent ensemble"
echo ""

# Test 3.1 : Requêtes simultanées sur donnée en cache
echo -e "${BLUE}Test 3.1 : 8 requêtes simultanées CDG (déjà en cache)${NC}"
echo "Attendu : Cache hit immédiat, coalescing de la lecture cache"
for i in {1..8}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
wait
echo -e "${GREEN}✅ 8 requêtes simultanées terminées (devrait être très rapide grâce au cache)${NC}"
echo ""

wait_and_show 5

# Test 3.2 : Requêtes simultanées sur donnée NON en cache
echo -e "${BLUE}Test 3.2 : 8 requêtes simultanées LHR (pas encore en cache)${NC}"
echo "Attendu : 1 API call (coalescé), puis mis en cache"
for i in {1..8}; do
    curl -s "http://localhost:8001/api/v1/airports/LHR" > /dev/null &
done
wait
echo -e "${GREEN}✅ 8 requêtes simultanées terminées${NC}"
echo ""

wait_and_show 10

# ============================================================================
# RÉSULTATS PROMETHEUS
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📊 RÉSULTATS PROMETHEUS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🔗 Métriques de Coalescing :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=coalesced_requests_total" | python -m json.tool | grep -A 3 '"value"'
echo ""

echo -e "${YELLOW}📡 Métriques d'API Calls :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=aviationstack_api_calls_total" | python -m json.tool | grep -A 3 '"value"'
echo ""

echo -e "${YELLOW}💾 Métriques de Cache Hits :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=cache_hits_total" | python -m json.tool | grep -A 3 '"value"'
echo ""

echo -e "${YELLOW}❌ Métriques de Cache Misses :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=cache_misses_total" | python -m json.tool | grep -A 3 '"value"'
echo ""

# ============================================================================
# CALCULS ET VÉRIFICATIONS
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}✅ VÉRIFICATIONS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

echo "📝 Vérifications manuelles à faire dans Grafana :"
echo ""
echo "1. 🎯 Taux de Coalescing Global"
echo "   ➜ Devrait être > 50%"
echo "   ➜ Indique que plus de la moitié des requêtes sont fusionnées"
echo ""
echo "2. 🎯 Cache Hit Rate - Airport"
echo "   ➜ Devrait être > 40%"
echo "   ➜ Indique que le cache évite des appels API"
echo ""
echo "3. 🎯 Cache Hit Rate - Flight"
echo "   ➜ Devrait être > 20%"
echo "   ➜ Peut être plus faible (moins de requêtes répétées)"
echo ""
echo "4. 📊 Total Appels API Aviationstack"
echo "   ➜ Devrait être << nombre total de requêtes HTTP"
echo "   ➜ Économie grâce au cache + coalescing"
echo ""
echo "5. 📈 Graphique Coalescing vs API Calls"
echo "   ➜ Courbe bleue (coalesced) > Courbe orange (API calls)"
echo "   ➜ Preuve visuelle de l'optimisation"
echo ""

echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ TESTS TERMINÉS${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "👉 Ouvre Grafana : http://localhost:3000"
echo "   Dashboard : Hello Mira - Metrics"
echo ""
echo "👉 Prometheus : http://localhost:9090"
echo "   Query : coalesced_requests_total"
echo ""
echo "👉 Logs Docker :"
echo "   docker logs hello-mira-airport --tail 100"
echo "   docker logs hello-mira-flight --tail 100"
echo ""
