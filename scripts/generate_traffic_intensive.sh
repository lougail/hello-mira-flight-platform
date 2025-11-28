#!/bin/bash
# ============================================================================
# Script de génération de trafic pour Hello Mira Flight Platform
# ============================================================================
# Usage: ./scripts/generate_traffic_intensive.sh [iterations]
# Default: 50 iterations = ~300 requêtes
#
# Architecture testée :
#   - Gateway (8004) : Cache, coalescing, appels API Aviationstack
#   - Airport (8001) : Recherche aéroports, geocoding, départs/arrivées
#   - Flight (8002)  : Statut vols, historique, statistiques
#   - Assistant (8003) : LLM, intentions, tools
#
# ============================================================================

ITERATIONS=${1:-50}

echo "🚀 Génération de trafic - Hello Mira Flight Platform"
echo "=================================================="
echo "📊 Iterations: $ITERATIONS (~$(($ITERATIONS * 8)) requêtes)"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Compteurs
total_requests=0
gateway_requests=0
airport_requests=0
flight_requests=0
assistant_requests=0

# Ports des services
GATEWAY_PORT=8004
AIRPORT_PORT=8001
FLIGHT_PORT=8002
ASSISTANT_PORT=8003

echo -e "${YELLOW}🔥 Démarrage du test de charge...${NC}"
echo ""

# ============================================================================
# VÉRIFICATION DES SERVICES
# ============================================================================
echo -e "${BLUE}[Check]${NC} Vérification des services..."

check_service() {
    local name=$1
    local port=$2
    local endpoint=$3

    if curl -s --connect-timeout 2 "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (port $port)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (port $port) - NON DISPONIBLE"
        return 1
    fi
}

services_ok=true
check_service "Gateway" $GATEWAY_PORT "/health" || services_ok=false
check_service "Airport" $AIRPORT_PORT "/api/v1/health" || services_ok=false
check_service "Flight" $FLIGHT_PORT "/api/v1/health" || services_ok=false
check_service "Assistant" $ASSISTANT_PORT "/api/v1/health" || services_ok=false

if [ "$services_ok" = false ]; then
    echo ""
    echo -e "${RED}❌ Certains services ne sont pas disponibles.${NC}"
    echo "   Lancez : docker-compose up -d"
    exit 1
fi

echo ""

# ============================================================================
# RÉCUPÉRATION DES VOLS RÉELS DEPUIS L'API
# ============================================================================
echo -e "${BLUE}[Init]${NC} Récupération des vols réels depuis l'API..."

# Récupère les vols pour avoir des données réalistes
DEPARTURES_DATA=$(curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/CDG/departures?limit=50")

# Extrait les flight_iata
REAL_FLIGHTS=$(echo "$DEPARTURES_DATA" | \
    python -c "import sys, json; data = json.load(sys.stdin); print(' '.join([f['flight_iata'] for f in data.get('flights', [])[:10] if f.get('flight_iata')]))" 2>/dev/null)

# Extrait les aéroports de destination
AIRPORTS_SEPARATION=$(echo "$DEPARTURES_DATA" | \
    python -c "
import sys, json
data = json.load(sys.stdin)

destinations = []
seen = set()
for flight in data.get('flights', []):
    arr = flight.get('arrival_iata')
    if arr and arr != 'CDG' and arr not in seen:
        destinations.append(arr)
        seen.add(arr)

traffic_airports = destinations[:10]
coalescing_airport = destinations[10] if len(destinations) > 10 else 'BCN'

print(f\"{' '.join(traffic_airports)}|{coalescing_airport}\")
" 2>/dev/null)

# Parse le résultat
AIRPORTS_DATA="${AIRPORTS_SEPARATION%|*}"
COALESCING_AIRPORT="${AIRPORTS_SEPARATION#*|}"

# Fallback
if [ -z "$REAL_FLIGHTS" ]; then
    echo -e "${YELLOW}⚠${NC}  Utilisation de codes génériques (vols)"
    REAL_FLIGHTS="AF1234 BA5678 LH9012"
fi

if [ -z "$AIRPORTS_DATA" ]; then
    echo -e "${YELLOW}⚠${NC}  Utilisation de codes génériques (aéroports)"
    AIRPORTS_DATA="JFK LHR ORY LAX SFO DXB NRT SIN HKG BKK"
    COALESCING_AIRPORT="BCN"
fi

# Convertit en tableaux
FLIGHTS_ARRAY=($REAL_FLIGHTS)
AIRPORTS_ARRAY=($AIRPORTS_DATA)

echo -e "${GREEN}✓${NC} ${#FLIGHTS_ARRAY[@]} vols : ${FLIGHTS_ARRAY[@]:0:3}..."
echo -e "${GREEN}✓${NC} ${#AIRPORTS_ARRAY[@]} aéroports : ${AIRPORTS_ARRAY[@]:0:3}..."
echo -e "${GREEN}✓${NC} Aéroport coalescing : $COALESCING_AIRPORT"
echo ""

# ============================================================================
# FONCTIONS DE GÉNÉRATION DE TRAFIC
# ============================================================================

# --- GATEWAY ---
generate_gateway_traffic() {
    local AIRPORT=${AIRPORTS_ARRAY[$RANDOM % ${#AIRPORTS_ARRAY[@]}]}
    local RAND_TYPE=$((RANDOM % 2))

    if [ $RAND_TYPE -eq 0 ]; then
        # Appel airports
        curl -s "http://localhost:$GATEWAY_PORT/api/v1/airports?iata=$AIRPORT" > /dev/null 2>&1
    else
        # Appel flights
        local FLIGHT=${FLIGHTS_ARRAY[$RANDOM % ${#FLIGHTS_ARRAY[@]}]}
        curl -s "http://localhost:$GATEWAY_PORT/api/v1/flights?flight_iata=$FLIGHT" > /dev/null 2>&1
    fi
    ((gateway_requests++))
    ((total_requests++))
}

# --- AIRPORT ---
generate_airport_traffic() {
    local TRAFFIC_AIRPORTS=("CDG" "${AIRPORTS_ARRAY[@]}")
    local AIRPORT=${TRAFFIC_AIRPORTS[$RANDOM % ${#TRAFFIC_AIRPORTS[@]}]}
    local RAND_TYPE=$((RANDOM % 4))

    case $RAND_TYPE in
        0)
            # Recherche par IATA
            curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/$AIRPORT" > /dev/null 2>&1
            ;;
        1)
            # Recherche par nom
            curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/search?name=Paris" > /dev/null 2>&1
            ;;
        2)
            # Départs
            curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/$AIRPORT/departures?limit=5" > /dev/null 2>&1
            ;;
        3)
            # Aéroport le plus proche (geocoding)
            curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/nearest-by-address?address=Paris&country_code=FR" > /dev/null 2>&1
            ;;
    esac
    ((airport_requests++))
    ((total_requests++))
}

# --- FLIGHT ---
generate_flight_traffic() {
    local FLIGHT=${FLIGHTS_ARRAY[$RANDOM % ${#FLIGHTS_ARRAY[@]}]}
    local RAND_TYPE=$((RANDOM % 3))

    case $RAND_TYPE in
        0)
            # Statut du vol
            curl -s "http://localhost:$FLIGHT_PORT/api/v1/flights/$FLIGHT" > /dev/null 2>&1
            ;;
        1)
            # Historique
            curl -s "http://localhost:$FLIGHT_PORT/api/v1/flights/$FLIGHT/history?days=7" > /dev/null 2>&1
            ;;
        2)
            # Statistiques
            curl -s "http://localhost:$FLIGHT_PORT/api/v1/flights/$FLIGHT/statistics" > /dev/null 2>&1
            ;;
    esac
    ((flight_requests++))
    ((total_requests++))
}

# --- ASSISTANT ---
generate_assistant_traffic() {
    local RAND_TYPE=$((RANDOM % 4))
    local PROMPT=""

    case $RAND_TYPE in
        0)
            PROMPT="Donne-moi les infos de l'aéroport CDG"
            ;;
        1)
            PROMPT="Trouve-moi l'aéroport le plus proche de Paris"
            ;;
        2)
            local FLIGHT=${FLIGHTS_ARRAY[$RANDOM % ${#FLIGHTS_ARRAY[@]}]}
            PROMPT="Quel est le statut du vol $FLIGHT ?"
            ;;
        3)
            PROMPT="Quels vols partent de JFK ?"
            ;;
    esac

    curl -s -X POST "http://localhost:$ASSISTANT_PORT/api/v1/assistant/answer" \
      -H "Content-Type: application/json" \
      -d @- <<EOF > /dev/null 2>&1
{"prompt": "$PROMPT"}
EOF
    ((assistant_requests++))
    ((total_requests++))
}

# ============================================================================
# BOUCLE PRINCIPALE - TRAFIC MIXTE
# ============================================================================
echo -e "${BLUE}[Traffic]${NC} Génération du trafic mixte..."

for i in $(seq 1 $ITERATIONS); do
    # Progression tous les 10 iterations
    if [ $((i % 10)) -eq 0 ]; then
        echo -e "  ${BLUE}→${NC} $i/$ITERATIONS (Total: $total_requests requêtes)"
    fi

    # Mix : 20% Gateway, 25% Airport, 25% Flight, 30% Assistant
    RAND=$((RANDOM % 20))

    if [ $RAND -lt 4 ]; then
        generate_gateway_traffic
    elif [ $RAND -lt 9 ]; then
        generate_airport_traffic
    elif [ $RAND -lt 14 ]; then
        generate_flight_traffic
    else
        generate_assistant_traffic
    fi

    # Délai aléatoire (10-50ms)
    sleep 0.0$((RANDOM % 5))
done

echo -e "${GREEN}✓${NC} Trafic mixte terminé"
echo ""

# ============================================================================
# TEST DE COALESCING - Requêtes simultanées vers Gateway
# ============================================================================
echo -e "${YELLOW}🔗 Test du coalescing (10 requêtes simultanées)...${NC}"

for i in {1..10}; do
    curl -s "http://localhost:$GATEWAY_PORT/api/v1/airports?iata=$COALESCING_AIRPORT" > /dev/null 2>&1 &
done
wait
((gateway_requests+=10))
((total_requests+=10))

echo -e "${GREEN}✓${NC} Coalescing testé ($COALESCING_AIRPORT)"
echo ""

# ============================================================================
# TEST DE CACHE - Requêtes répétées
# ============================================================================
echo -e "${YELLOW}💾 Test du cache (20 requêtes répétées)...${NC}"

for i in {1..20}; do
    curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/$COALESCING_AIRPORT" > /dev/null 2>&1
    ((airport_requests++))
    ((total_requests++))
done

echo -e "${GREEN}✓${NC} Cache testé"
echo ""

# ============================================================================
# TEST DES MÉTRIQUES CUSTOM
# ============================================================================
echo -e "${YELLOW}📊 Test des métriques custom...${NC}"

# Flight statistics (déclenche les métriques de ponctualité)
echo -e "  ${BLUE}→${NC} Flight statistics..."
for FLIGHT in ${FLIGHTS_ARRAY[@]:0:3}; do
    curl -s "http://localhost:$FLIGHT_PORT/api/v1/flights/$FLIGHT/statistics" > /dev/null 2>&1
    ((flight_requests++))
    ((total_requests++))
done

# Airport geocoding (déclenche les métriques Nominatim)
echo -e "  ${BLUE}→${NC} Airport geocoding..."
curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/nearest-by-address?address=Paris&country_code=FR" > /dev/null 2>&1
((airport_requests++)); ((total_requests++))
curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/nearest-by-address?address=London&country_code=GB" > /dev/null 2>&1
((airport_requests++)); ((total_requests++))
curl -s "http://localhost:$AIRPORT_PORT/api/v1/airports/nearest-by-address?address=New%20York&country_code=US" > /dev/null 2>&1
((airport_requests++)); ((total_requests++))

# Assistant intents (déclenche les métriques LLM)
echo -e "  ${BLUE}→${NC} Assistant intents..."
INTENT_PROMPTS=(
    "Quel est le statut du vol AF123 ?"
    "Trouve-moi l'aéroport le plus proche de Lyon"
    "Quels vols partent de CDG demain ?"
)
for PROMPT in "${INTENT_PROMPTS[@]}"; do
    curl -s -X POST "http://localhost:$ASSISTANT_PORT/api/v1/assistant/answer" \
      -H "Content-Type: application/json" \
      -d "{\"prompt\": \"$PROMPT\"}" > /dev/null 2>&1
    ((assistant_requests++))
    ((total_requests++))
done

echo -e "${GREEN}✓${NC} Métriques custom testées"
echo ""

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo "=================================================="
echo -e "${GREEN}✅ Trafic généré avec succès !${NC}"
echo ""
echo "📊 Statistiques :"
echo "  ├── Gateway   : $gateway_requests requêtes"
echo "  ├── Airport   : $airport_requests requêtes"
echo "  ├── Flight    : $flight_requests requêtes"
echo "  ├── Assistant : $assistant_requests requêtes"
echo "  └── TOTAL     : $total_requests requêtes"
echo ""
echo "📈 Vérification des métriques :"
echo ""

# Attente courte pour que Prometheus scrape
echo -e "${BLUE}[Wait]${NC} Attente de 5s pour scraping Prometheus..."
sleep 5

# Vérification des métriques disponibles
echo -e "${BLUE}[Check]${NC} Métriques disponibles :"

check_metric() {
    local service=$1
    local port=$2
    local metric=$3

    if curl -s "http://localhost:$port/metrics" 2>/dev/null | grep -q "^${metric}"; then
        echo -e "  ${GREEN}✓${NC} $service: $metric"
    else
        echo -e "  ${YELLOW}○${NC} $service: $metric (pas encore de données)"
    fi
}

# Gateway metrics
check_metric "Gateway" $GATEWAY_PORT "gateway_cache_hits_total"
check_metric "Gateway" $GATEWAY_PORT "gateway_coalesced_requests_total"
check_metric "Gateway" $GATEWAY_PORT "gateway_api_calls_total"

# Airport metrics
check_metric "Airport" $AIRPORT_PORT "airport_lookups_total"
check_metric "Airport" $AIRPORT_PORT "airport_geocoding_calls_total"
check_metric "Airport" $AIRPORT_PORT "airport_flight_queries_total"

# Flight metrics
check_metric "Flight" $FLIGHT_PORT "flight_lookups_total"
check_metric "Flight" $FLIGHT_PORT "flight_mongodb_operations_total"
check_metric "Flight" $FLIGHT_PORT "flight_statistics_calculated_total"

# Assistant metrics
check_metric "Assistant" $ASSISTANT_PORT "assistant_llm_calls_total"
check_metric "Assistant" $ASSISTANT_PORT "assistant_intent_detected_total"
check_metric "Assistant" $ASSISTANT_PORT "assistant_tool_calls_total"

echo ""
echo "🌐 Interfaces :"
echo "  - Grafana   : http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "💡 Pour plus de trafic : ./scripts/generate_traffic_intensive.sh 100"
echo ""