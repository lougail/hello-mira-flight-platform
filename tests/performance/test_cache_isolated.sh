#!/bin/bash

# Test ISOLÉ : Cache MongoDB uniquement
# Stratégie : Requêtes séquentielles (pas de coalescing) pour mesurer le cache

set -e

echo "=========================================="
echo "💾 TEST ISOLÉ : CACHE MONGODB UNIQUEMENT"
echo "=========================================="
echo ""
echo "Stratégie : Requêtes séquentielles espacées (évite le coalescing)"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Nettoyer le cache avant le test
echo -e "${YELLOW}🧹 Nettoyage du cache MongoDB...${NC}"
docker exec hello-mira-mongo mongosh --quiet --eval "
  use hello_mira;
  db.airport_cache.deleteMany({});
  db.flight_cache.deleteMany({});
  print('Cache cleared');
"
echo ""

sleep 2

# Test 1 : Premier appel = MISS, suivants = HIT
echo -e "${BLUE}Test 1 : Cache Airport (CDG)${NC}"
echo "Séquence : 1 MISS + 5 HITS"
echo ""

echo "Appel 1 (MISS attendu) :"
curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null
echo "✓ Premier appel (devrait déclencher API)"
sleep 2

echo "Appels 2-6 (HITS attendus) :"
for i in {2..6}; do
    curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null
    echo -n "✓ Appel $i (devrait venir du cache) "
    sleep 1
done
echo ""
echo -e "${GREEN}✅ Séquence terminée${NC}"
echo ""

sleep 5

# Test 2 : Cache Flight
echo -e "${BLUE}Test 2 : Cache Flight (BA117)${NC}"
echo "Séquence : 1 MISS + 5 HITS"
echo ""

echo "Appel 1 (MISS attendu) :"
curl -s "http://localhost:8002/api/v1/flights/BA117" > /dev/null
echo "✓ Premier appel (devrait déclencher API)"
sleep 2

echo "Appels 2-6 (HITS attendus) :"
for i in {2..6}; do
    curl -s "http://localhost:8002/api/v1/flights/BA117" > /dev/null
    echo -n "✓ Appel $i (devrait venir du cache) "
    sleep 1
done
echo ""
echo -e "${GREEN}✅ Séquence terminée${NC}"
echo ""

sleep 5

# Test 3 : Multiple aéroports pour vérifier isolation cache
echo -e "${BLUE}Test 3 : Cache multi-aéroports (JFK, ORY, LHR)${NC}"
echo "3 aéroports × (1 MISS + 3 HITS) = 3 API calls, 9 cache hits"
echo ""

for airport in JFK ORY LHR; do
    echo "--- $airport ---"
    curl -s "http://localhost:8001/api/v1/airports/$airport" > /dev/null
    echo "✓ MISS (API call)"
    sleep 1

    for i in {1..3}; do
        curl -s "http://localhost:8001/api/v1/airports/$airport" > /dev/null
        echo -n "✓ HIT "
        sleep 0.5
    done
    echo ""
done

echo -e "${GREEN}✅ Test multi-aéroports terminé${NC}"
echo ""

sleep 10

# Résultats Prometheus
echo "=========================================="
echo "📊 MÉTRIQUES CACHE (Prometheus)"
echo "=========================================="
echo ""

echo -e "${YELLOW}💾 Cache Hits :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=cache_hits_total" | python -m json.tool | grep -A 2 '"value"'

echo ""
echo -e "${YELLOW}❌ Cache Misses :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=cache_misses_total" | python -m json.tool | grep -A 2 '"value"'

echo ""
echo -e "${YELLOW}📡 API Calls :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=aviationstack_api_calls_total" | python -m json.tool | grep -A 2 '"value"'

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Test cache isolé terminé${NC}"
echo "=========================================="
echo ""
echo "Calcul du Hit Rate :"
echo "  Hit Rate = Hits / (Hits + Misses)"
echo ""
echo "Vérification dans Grafana :"
echo "  🎯 Cache Hit Rate - Airport : devrait être > 70%"
echo "  🎯 Cache Hit Rate - Flight : devrait être > 70%"
echo ""
