#!/bin/bash

# Script de test du Request Coalescing
# Partie 3 - Optimisation du test technique Hello Mira

set -e

echo ""
echo "=========================================="
echo "🧪 TEST DE COALESCING"
echo "Hello Mira Flight Platform"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Service Airport
echo -e "${BLUE}🧪 TEST 1: Airport Service (CDG)${NC}"
echo "Envoi de 5 requêtes simultanées..."
time (
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  wait
)
echo -e "${GREEN}✅ Terminé${NC}"
echo ""

sleep 2

# Test 2: Service Flight
echo -e "${BLUE}🧪 TEST 2: Flight Service (AF447)${NC}"
echo "Envoi de 5 requêtes simultanées..."
time (
  curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
  curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
  curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
  curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
  curl -s "http://localhost:8002/api/v1/flights/AF447" > /dev/null &
  wait
)
echo -e "${GREEN}✅ Terminé${NC}"
echo ""

sleep 2

# Test 3: Mix de requêtes
echo -e "${BLUE}🧪 TEST 3: Mix CDG + JFK (Airport)${NC}"
echo "Envoi de 6 requêtes (3 CDG + 3 JFK)..."
time (
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/CDG" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/JFK" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/JFK" > /dev/null &
  curl -s "http://localhost:8001/api/v1/airports/JFK" > /dev/null &
  wait
)
echo -e "${GREEN}✅ Terminé${NC}"
echo ""

sleep 2

# Vérification des métriques
echo "=========================================="
echo "📊 MÉTRIQUES PROMETHEUS"
echo "=========================================="
echo ""

echo -e "${YELLOW}🔗 Requêtes coalescées (total) :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=coalesced_requests_total" | python -m json.tool | grep -A 5 "service"

echo ""
echo -e "${YELLOW}📡 Appels API Aviationstack (total) :${NC}"
curl -s "http://localhost:9090/api/v1/query?query=aviationstack_api_calls_total" | python -m json.tool | grep -A 5 "service"

echo ""
echo "=========================================="
echo "📈 VÉRIFICATION GRAFANA"
echo "=========================================="
echo ""
echo "👉 Ouvre Grafana : http://localhost:3000"
echo "   Dashboard : Hello Mira - Metrics"
echo "   Section : 🔗 COALESCING DES REQUÊTES"
echo ""
echo "📊 Attendu :"
echo "   - Taux de coalescing : ~80%"
echo "   - Graphique : requêtes coalescées vs API calls"
echo ""
echo "📝 Vérification des logs :"
echo "   docker logs hello-mira-airport --tail 50"
echo "   docker logs hello-mira-flight --tail 50"
echo ""
echo -e "${GREEN}✅ Tests terminés avec succès !${NC}"
echo ""
