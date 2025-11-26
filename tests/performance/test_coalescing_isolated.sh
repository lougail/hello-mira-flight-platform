#!/bin/bash

# Test ISOLÉ : Request Coalescing uniquement
# Stratégie : Tester sur données NON en cache pour isoler le coalescing

set -e

echo "=========================================="
echo "🔗 TEST ISOLÉ : COALESCING UNIQUEMENT"
echo "=========================================="
echo ""
echo "Stratégie : Requêtes simultanées sur données fraîches (pas de cache)"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Nettoyer le cache MongoDB avant le test
echo -e "${YELLOW}🧹 Nettoyage du cache MongoDB...${NC}"
docker exec hello-mira-mongo mongosh --quiet --eval "
  use hello_mira;
  db.airport_cache.deleteMany({});
  db.flight_cache.deleteMany({});
  print('Cache cleared');
"
echo ""

sleep 2

# Test 1 : Coalescing sur Airport (données fraîches)
echo -e "${BLUE}Test 1 : 10 requêtes simultanées CDG (pas en cache)${NC}"
echo "Attendu : 1 API call, 9 requêtes coalescées"
echo ""

start=$(date +%s)
for i in {1..10}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
wait
end=$(date +%s)
elapsed=$((end - start))

echo -e "${GREEN}✅ Terminé en ${elapsed}s${NC}"
echo ""

sleep 5

# Test 2 : Coalescing sur Flight (données fraîches)
echo -e "${BLUE}Test 2 : 10 requêtes simultanées LH400 (pas en cache)${NC}"
echo "Attendu : 1 API call, 9 requêtes coalescées"
echo ""

start=$(date +%s)
for i in {1..10}; do
    curl -s "http://localhost:8002/api/v1/flights/LH400" > /dev/null &
done
wait
end=$(date +%s)
elapsed=$((end - start))

echo -e "${GREEN}✅ Terminé en ${elapsed}s${NC}"
echo ""

sleep 5

# Test 3 : Mix de requêtes différentes (vérifier pas de cross-coalescing)
echo -e "${BLUE}Test 3 : 15 requêtes (5×CDG, 5×JFK, 5×ORY)${NC}"
echo "Attendu : 3 API calls (1 par aéroport), 12 requêtes coalescées"
echo ""

start=$(date +%s)
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
done
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/JFK" > /dev/null &
done
for i in {1..5}; do
    curl -s "http://localhost:8001/api/v1/airports/ORY" > /dev/null &
done
wait
end=$(date +%s)
elapsed=$((end - start))

echo -e "${GREEN}✅ Terminé en ${elapsed}s${NC}"
echo ""

sleep 10

# Résultats Prometheus
echo "=========================================="
echo "📊 MÉTRIQUES COALESCING (Prometheus)"
echo "=========================================="
echo ""

echo -e "${YELLOW}🔗 Requêtes coalescées :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=coalesced_requests_total" | python -m json.tool | grep -A 2 '"value"'

echo ""
echo -e "${YELLOW}📡 API Calls :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=aviationstack_api_calls_total" | python -m json.tool | grep -A 2 '"value"'

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Test coalescing isolé terminé${NC}"
echo "=========================================="
echo ""
echo "Vérification dans Grafana :"
echo "  🎯 Taux de Coalescing Global : devrait être > 80%"
echo "  📊 Courbe bleue (coalescées) >> courbe orange (API)"
echo ""
