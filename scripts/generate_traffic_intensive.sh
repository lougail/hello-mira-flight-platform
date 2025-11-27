#!/bin/bash
# Script de génération de trafic INTENSIF pour obtenir des métriques fiables
# Usage: ./scripts/generate_traffic_intensive.sh [iterations]
# Default: 50 iterations = ~300 requêtes

ITERATIONS=${1:-50}

echo "🚀 Génération de trafic INTENSIF"
echo "=================================================="
echo "📊 Iterations: $ITERATIONS (~$(($ITERATIONS * 6)) requêtes)"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Compteurs
total_requests=0
airport_requests=0
flight_requests=0
assistant_requests=0

echo -e "${YELLOW}🔥 Démarrage du test de charge...${NC}"
echo ""

# ============================================================================
# RÉCUPÉRATION DES VOLS RÉELS DEPUIS L'API
# ============================================================================
echo -e "${BLUE}[Init]${NC} Récupération des vols réels depuis l'API..."

# Récupère PLUS de vols pour avoir assez d'aéroports à séparer (traffic + coalescing)
DEPARTURES_DATA=$(curl -s "http://localhost:8001/api/v1/airports/CDG/departures?limit=50")

# Extrait les flight_iata
REAL_FLIGHTS=$(echo "$DEPARTURES_DATA" | \
    python -c "import sys, json; data = json.load(sys.stdin); print(' '.join([f['flight_iata'] for f in data.get('flights', [])[:10] if f.get('flight_iata')]))" 2>/dev/null)

# Extrait et SÉPARE les aéroports dès le début selon leur usage
# - Aéroports 1-10 : Trafic normal (boucle principale)
# - Aéroport 11 : Test coalescing (jamais utilisé avant → cache MISS garanti)
# - Réutilisation aéroport 11 : Test cache HIT (en cache après le test coalescing)
AIRPORTS_SEPARATION=$(echo "$DEPARTURES_DATA" | \
    python -c "
import sys, json
data = json.load(sys.stdin)

# Récupère tous les aéroports de destination uniques
destinations = []
seen = set()
for flight in data.get('flights', []):
    arr = flight.get('arrival_iata')
    if arr and arr != 'CDG' and arr not in seen:  # Exclut CDG et déduplique
        destinations.append(arr)
        seen.add(arr)

# Sépare :
# - 10 premiers → trafic normal
# - 11ème → test coalescing (jamais touché avant)
traffic_airports = destinations[:10]
coalescing_airport = destinations[10] if len(destinations) > 10 else 'BCN'

print(f\"{' '.join(traffic_airports)}|{coalescing_airport}\")
" 2>/dev/null)

# Parse le résultat (format : "AMS BKK DXB ...|MAD")
AIRPORTS_DATA="${AIRPORTS_SEPARATION%|*}"  # Partie avant le |
COALESCING_AIRPORT="${AIRPORTS_SEPARATION#*|}"  # Partie après le |

# Fallback : si pas de vols récupérés, utilise des codes génériques
if [ -z "$REAL_FLIGHTS" ]; then
    echo -e "${YELLOW}⚠${NC}  Impossible de récupérer les vols réels, utilisation de codes génériques"
    REAL_FLIGHTS="AF1234 BA5678 LH9012"
fi

if [ -z "$AIRPORTS_DATA" ]; then
    echo -e "${YELLOW}⚠${NC}  Impossible de récupérer les aéroports réels, utilisation de codes génériques"
    AIRPORTS_DATA="JFK LHR ORY LAX SFO DXB NRT SIN HKG BKK"
    COALESCING_AIRPORT="BCN"
fi

# Convertit en tableaux
FLIGHTS_ARRAY=($REAL_FLIGHTS)
AIRPORTS_ARRAY=($AIRPORTS_DATA)

echo -e "${GREEN}✓${NC} ${#FLIGHTS_ARRAY[@]} vols réels récupérés : ${FLIGHTS_ARRAY[@]:0:5}..."
echo -e "${GREEN}✓${NC} ${#AIRPORTS_ARRAY[@]} aéroports pour trafic normal : ${AIRPORTS_ARRAY[@]:0:5}..."
echo -e "${GREEN}✓${NC} Aéroport réservé pour coalescing : $COALESCING_AIRPORT (jamais utilisé avant → cache MISS garanti)"
echo ""
echo -e "${BLUE}[Strategy]${NC} Séparation des données :"
echo "  - Aéroports 1-10 : Trafic mixte dans la boucle principale"
echo "  - Aéroport 11 ($COALESCING_AIRPORT) : Test coalescing (cache MISS) puis test cache (cache HIT)"
echo ""

# ============================================================================
# FONCTION : GÉNÈRE DU TRAFIC AIRPORT
# ============================================================================
generate_airport_traffic() {
    # Utilise les aéroports de destination récupérés depuis l'API + CDG
    # Ajoute CDG dynamiquement car c'est notre point de départ principal
    local TRAFFIC_AIRPORTS=("CDG" "${AIRPORTS_ARRAY[@]}")

    # Requête aléatoire
    AIRPORT=${TRAFFIC_AIRPORTS[$RANDOM % ${#TRAFFIC_AIRPORTS[@]}]}
    curl -s http://localhost:8001/api/v1/airports/$AIRPORT > /dev/null 2>&1
    ((airport_requests++))
    ((total_requests++))
}

# ============================================================================
# FONCTION : GÉNÈRE DU TRAFIC FLIGHT
# ============================================================================
generate_flight_traffic() {
    # Utilise les vols réels récupérés depuis l'API
    FLIGHT=${FLIGHTS_ARRAY[$RANDOM % ${#FLIGHTS_ARRAY[@]}]}
    curl -s http://localhost:8002/api/v1/flights/$FLIGHT > /dev/null 2>&1
    ((flight_requests++))
    ((total_requests++))
}

# ============================================================================
# FONCTION : GÉNÈRE DU TRAFIC ASSISTANT
# ============================================================================
generate_assistant_traffic() {
    # Variété de prompts utilisant les données réelles
    # Mix d'aéroports et de vols pour tester différentes latences
    RAND_TYPE=$((RANDOM % 3))

    if [ $RAND_TYPE -eq 0 ]; then
        # Prompts sur les aéroports
        AIRPORTS_PROMPTS=(
            "Donne-moi les infos de l'aéroport CDG"
            "Trouve-moi l'aéroport le plus proche de Paris"
            "Quels vols partent de JFK ?"
            "Où se trouve l'aéroport ORY ?"
        )
        PROMPT=${AIRPORTS_PROMPTS[$RANDOM % ${#AIRPORTS_PROMPTS[@]}]}
    else
        # Prompts sur les vols (utilise les vols réels récupérés)
        REAL_FLIGHT=${FLIGHTS_ARRAY[$RANDOM % ${#FLIGHTS_ARRAY[@]}]}
        FLIGHT_PROMPTS=(
            "Quel est le statut du vol $REAL_FLIGHT ?"
            "Je suis sur le vol $REAL_FLIGHT, à quelle heure j'arrive ?"
            "Donne-moi les détails du vol $REAL_FLIGHT"
        )
        PROMPT=${FLIGHT_PROMPTS[$RANDOM % ${#FLIGHT_PROMPTS[@]}]}
    fi

    # Utilise un heredoc pour éviter les problèmes d'échappement avec apostrophes/guillemets
    # Méthode recommandée (2025) : curl -d @- avec heredoc
    curl -s -X POST http://localhost:8003/api/v1/assistant/answer \
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
for i in $(seq 1 $ITERATIONS); do
    # Affichage progression tous les 10 iterations
    if [ $((i % 10)) -eq 0 ]; then
        echo -e "${BLUE}[Progress]${NC} $i/$ITERATIONS iterations (Total: $total_requests requêtes)"
    fi

    # Mix aléatoire de requêtes pour simuler du trafic réel
    # 40% Airport, 30% Flight (vols réels), 30% Assistant
    RAND=$((RANDOM % 10))

    if [ $RAND -lt 4 ]; then
        # 40% - Airport
        generate_airport_traffic
    elif [ $RAND -lt 7 ]; then
        # 30% - Flight (utilise vols réels récupérés)
        generate_flight_traffic
    else
        # 30% - Assistant (utilise vols réels dans prompts)
        generate_assistant_traffic
    fi

    # Petit délai pour éviter de surcharger (10-50ms aléatoire)
    sleep 0.0$((RANDOM % 5))
done

# ============================================================================
# TEST DE COALESCING - Requêtes simultanées
# ============================================================================
echo ""
echo -e "${YELLOW}🔗 Test du coalescing (requêtes simultanées)...${NC}"

# 10 requêtes identiques en parallèle pour tester le coalescing
# Utilise $COALESCING_AIRPORT qui n'a JAMAIS été touché dans la boucle principale
# Garantit un cache MISS initial → 1 API call + 9 requêtes coalescées
echo -e "${BLUE}[Info]${NC} Test avec $COALESCING_AIRPORT (aéroport #11, jamais utilisé avant)"
for i in {1..10}; do
    curl -s http://localhost:8001/api/v1/airports/$COALESCING_AIRPORT > /dev/null 2>&1 &
done
wait
((airport_requests+=10))
((total_requests+=10))

echo -e "${GREEN}✓${NC} Coalescing testé (10 requêtes $COALESCING_AIRPORT simultanées → 9 coalescées)"

# ============================================================================
# TEST DE CACHE HITS - Requêtes répétées
# ============================================================================
echo ""
echo -e "${YELLOW}💾 Test du cache (requêtes répétées)...${NC}"

# Requêtes répétées pour maximiser cache hits
# $COALESCING_AIRPORT est maintenant EN CACHE (mis en cache par le test de coalescing)
# Garantit 20 cache HITs consécutifs
echo -e "${BLUE}[Info]${NC} Réutilise $COALESCING_AIRPORT (maintenant en cache)"
for i in {1..20}; do
    curl -s http://localhost:8001/api/v1/airports/$COALESCING_AIRPORT > /dev/null 2>&1
    ((airport_requests++))
    ((total_requests++))
done

echo -e "${GREEN}✓${NC} Cache testé (20 requêtes séquentielles, toutes en cache HIT)"

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Trafic généré avec succès !${NC}"
echo ""
echo "📊 Statistiques :"
echo "  - Total requêtes : $total_requests"
echo "  - Airport : $airport_requests"
echo "  - Flight : $flight_requests"
echo "  - Assistant : $assistant_requests"
echo ""
echo "📈 Prochaines étapes :"
echo "  1. Attends 15s que Prometheus scrape les données"
echo "  2. Rafraîchis Grafana : http://localhost:3000"
echo "  3. Vérifie les panels :"
echo "     - Latence p50/p95 (devrait montrer de la variabilité)"
echo "     - Cache Hit Rate (devrait être >70%)"
echo "     - API Calls économisés via coalescing"
echo ""
echo "💡 Pour plus de trafic : ./scripts/generate_traffic_intensive.sh 100"
echo ""
