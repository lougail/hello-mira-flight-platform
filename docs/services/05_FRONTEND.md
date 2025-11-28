# 🖥️ Frontend Streamlit - Documentation Technique

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Authentification Supabase](#authentification-supabase)
4. [Pages et Navigation](#pages-et-navigation)
5. [Composants UI](#composants-ui)
6. [Communication avec le Backend](#communication-avec-le-backend)
7. [Configuration](#configuration)
8. [Déploiement](#déploiement)

---

## Vue d'Ensemble

Le frontend est une application **Streamlit** qui fournit :

- 💬 **Chat conversationnel** avec l'Assistant IA
- 🏢 **Recherche d'aéroports** par code IATA ou nom
- ✈️ **Consultation des vols** (départs, arrivées, statut)
- 🔐 **Authentification** via Supabase

### Caractéristiques

| Aspect | Détail |
|--------|--------|
| **Framework** | Streamlit 1.28+ |
| **Port** | 8501 |
| **Auth** | Supabase + st_login_form |
| **Thème** | Mode sombre supporté |
| **Multi-langue** | FR (interface) |

---

## Architecture

### Structure des Fichiers

```text
frontend/
├── app.py                    # Application principale (477 lignes)
├── Dockerfile                # Image Docker
├── requirements.txt          # Dépendances Python
└── .streamlit/
    ├── config.toml           # Configuration Streamlit
    ├── secrets.toml          # Credentials Supabase (git ignored)
    └── secrets.toml.example  # Template des secrets
```

### Diagramme de Composants

```text
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (main)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 AUTHENTIFICATION                         │   │
│  │               init_supabase_auth()                       │   │
│  │  • Vérifie session_state.authenticated                   │   │
│  │  • Affiche login_form() ou mode démo                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SIDEBAR                               │   │
│  │  • Logo Hello Mira                                       │   │
│  │  • Navigation (Radio buttons)                            │   │
│  │  • Info utilisateur                                      │   │
│  │  • Bouton déconnexion                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│      ┌────────────────────┼────────────────────┐               │
│      ▼                    ▼                    ▼               │
│ ┌──────────┐       ┌──────────────┐     ┌───────────┐        │
│ │page_chat │       │page_airports │     │page_flights│        │
│ │          │       │              │     │           │        │
│ │• Historique│     │• Recherche   │     │• Départs  │        │
│ │• Chat input│     │• Résultats   │     │• Arrivées │        │
│ │• Réponses │      │• Boutons nav │     │• Statut   │        │
│ └──────────┘       └──────────────┘     └───────────┘        │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentification Supabase

### Flux d'Authentification

```python
def init_supabase_auth():
    """
    1. Vérifie si déjà authentifié (session_state)
    2. Vérifie si Supabase est configuré (secrets.toml)
    3. Affiche login_form() ou mode démo
    """
```

### Configuration Secrets

**Fichier** : `frontend/.streamlit/secrets.toml`

```toml
[connections.supabase]
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Mode Démo

Si Supabase n'est pas configuré, un **mode démo** est disponible :

```python
if st.button("🚀 Continuer en mode démo"):
    st.session_state["authenticated"] = True
    st.session_state["username"] = "demo_user"
    st.rerun()
```

### États de Session

| Clé | Type | Description |
|-----|------|-------------|
| `authenticated` | bool | Utilisateur connecté |
| `username` | str | Nom d'utilisateur |
| `chat_history` | list | Historique des conversations |
| `selected_airport` | str | IATA sélectionné |
| `view_mode` | str | Mode de vue (departures/arrivals) |

---

## Pages et Navigation

### Navigation Sidebar

```python
page = st.radio(
    "Navigation",
    ["💬 Assistant", "🏢 Aéroports", "✈️ Vols"],
    label_visibility="collapsed"
)
```

### Page 1 : Assistant (page_chat)

**Fonctionnalités** :

- Historique conversationnel persisté en session
- Input chat avec placeholder
- Affichage des réponses avec données JSON expandables
- Bouton effacer l'historique

**Code clé** :

```python
def page_chat():
    # Initialise l'historique
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Affiche l'historique
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("data"):
                with st.expander("📊 Données"):
                    st.json(message["data"])

    # Input utilisateur
    if prompt := st.chat_input("Que voulez-vous savoir ?"):
        # ... traitement
```

### Page 2 : Aéroports (page_airports)

**Fonctionnalités** :

- Recherche par IATA (3 lettres) ou nom de ville
- Affichage des résultats en cartes
- Boutons pour voir départs/arrivées
- Drapeaux pays via emoji Unicode

**Code clé** :

```python
def search_airport(query: str) -> dict:
    # Détection automatique IATA vs nom
    if len(query) == 3 and query.isalpha():
        # Recherche par IATA
        response = requests.get(f"{AIRPORT_URL}/api/v1/airports/{query.upper()}")
    else:
        # Recherche par nom
        response = requests.get(
            f"{AIRPORT_URL}/api/v1/airports/search",
            params={"query": query}
        )
```

### Page 3 : Vols (page_flights)

**Fonctionnalités** :

- 3 onglets : Départs, Arrivées, Statut Vol
- Paramètre limite (5-50)
- Cartes de vol avec statut coloré
- Détails JSON expandables

**Onglets** :

```python
tab1, tab2, tab3 = st.tabs(["🛫 Départs", "🛬 Arrivées", "🔍 Statut Vol"])
```

---

## Composants UI

### Carte de Vol (render_flight_card)

Affiche les informations d'un vol en colonnes :

```python
def render_flight_card(flight: dict):
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:  # Numéro de vol + Route
        st.markdown(f"### ✈️ {flight_num}")
        st.markdown(f"**{dep_airport}** → **{arr_airport}**")
        # Pays de destination
        if arr.get("country"):
            st.caption(f"🌍 Destination: {arr.get('country')}")

    with col2:  # Statut + Retard
        status_colors = {
            "scheduled": "🟡",
            "active": "🟢",
            "landed": "🔵",
            "cancelled": "🔴",
            "diverted": "🟠"
        }
        st.markdown(f"{status_colors.get(status, '⚪')} **{status.upper()}**")

    with col3:  # Horaires
        st.markdown(f"🛫 {departure_time}")
        st.markdown(f"🛬 {arrival_time}")
```

### Drapeau Pays (get_country_flag)

Convertit un code ISO en emoji drapeau :

```python
def get_country_flag(country_code: str) -> str:
    """Retourne l'emoji drapeau pour un code pays ISO."""
    if not country_code or len(country_code) != 2:
        return "🌍"
    # Algorithme Unicode : A -> 🇦 (U+1F1E6), B -> 🇧 (U+1F1E7), etc.
    return "".join(chr(ord(c) + 127397) for c in country_code.upper())
```

**Exemples** :

- `FR` → 🇫🇷
- `US` → 🇺🇸
- `JP` → 🇯🇵

---

## Communication avec le Backend

### URLs des Services

```python
# Configuration des URLs (via variables d'environnement Docker)
ASSISTANT_URL = os.getenv("ASSISTANT_URL", "http://localhost:8003")
AIRPORT_URL = os.getenv("AIRPORT_URL", "http://localhost:8001")
FLIGHT_URL = os.getenv("FLIGHT_URL", "http://localhost:8002")
```

### Fonctions API

| Fonction | Service | Endpoint | Timeout |
|----------|---------|----------|---------|
| `call_assistant(prompt)` | Assistant | POST /api/v1/assistant/answer | 30s |
| `search_airport(query)` | Airport | GET /api/v1/airports/{iata} ou /search | 10s |
| `get_departures(iata, limit)` | Airport | GET /api/v1/airports/{iata}/departures | 15s |
| `get_arrivals(iata, limit)` | Airport | GET /api/v1/airports/{iata}/arrivals | 15s |
| `get_flight_status(flight_iata)` | Flight | GET /api/v1/flights/{flight_iata} | 10s |

### Gestion d'Erreurs

```python
def call_assistant(prompt: str) -> dict:
    try:
        response = requests.post(
            f"{ASSISTANT_URL}/api/v1/assistant/answer",
            json={"prompt": prompt},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "answer": f"Erreur de connexion: {e}"}
```

---

## Configuration

### Config Streamlit

**Fichier** : `frontend/.streamlit/config.toml`

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[server]
headless = true
enableCORS = false
```

### Requirements

**Fichier** : `frontend/requirements.txt`

```text
streamlit>=1.28.0
requests>=2.31.0
st-login-form>=0.2.0
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Déploiement

### Docker Compose (Extrait)

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: hello-mira-frontend
  depends_on:
    assistant:
      condition: service_healthy
  environment:
    ASSISTANT_URL: http://assistant:8003
    AIRPORT_URL: http://airport:8001
    FLIGHT_URL: http://flight:8002
  volumes:
    - ./frontend/.streamlit:/app/.streamlit:ro
  ports:
    - "8501:8501"
```

### Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `ASSISTANT_URL` | <http://localhost:8003> | URL du service Assistant |
| `AIRPORT_URL` | <http://localhost:8001> | URL du service Airport |
| `FLIGHT_URL` | <http://localhost:8002> | URL du service Flight |

### Health Check

```bash
curl -f http://localhost:8501/_stcore/health
```

---

## Captures d'Écran

### Page Assistant

```text
┌─────────────────────────────────────────────────────────┐
│ ✈️ Hello Mira    │  💬 Assistant de Vol                 │
│ Flight Platform  │                                      │
│ ─────────────── │  Posez vos questions en langage      │
│ 💬 Assistant    │  naturel (FR/EN/ES)                  │
│ 🏢 Aéroports    │  ─────────────────────────────────── │
│ ✈️ Vols         │  👤 Quels vols partent de CDG ?      │
│ ─────────────── │                                      │
│ 👤 demo_user    │  🤖 Voici les vols au départ de      │
│ 🚪 Déconnexion  │  l'aéroport Charles de Gaulle...     │
│                 │                                      │
│                 │  ▼ 📊 Données                        │
│                 │  ─────────────────────────────────── │
│                 │  [Que voulez-vous savoir ?]          │
└─────────────────────────────────────────────────────────┘
```

### Page Vols

```text
┌─────────────────────────────────────────────────────────┐
│ ✈️ Vols                                                  │
├─────────────────────────────────────────────────────────┤
│  [🛫 Départs]  [🛬 Arrivées]  [🔍 Statut Vol]           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Code IATA: [CDG     ]  Nombre: [10]  [Voir les départs]│
│                                                         │
│  ✅ 10 vols trouvés                                     │
│  ───────────────────────────────────────────────────── │
│  ### ✈️ AF1234                                          │
│  **CDG** → **JFK**          🟢 **ACTIVE**    🛫 14:30  │
│  🌍 Destination: United States   ⏱️ Retard: 15 min     │
│  ───────────────────────────────────────────────────── │
│  ### ✈️ BA456                                           │
│  **CDG** → **LHR**          🟡 **SCHEDULED** 🛫 15:45  │
│  🌍 Destination: United Kingdom                        │
└─────────────────────────────────────────────────────────┘
```

---

## Améliorations Futures

### UX/UI

- [ ] Mode sombre complet
- [ ] Animations de chargement améliorées
- [ ] Notifications push pour changements de statut
- [ ] Carte interactive des aéroports

### Fonctionnalités

- [ ] Historique des recherches persisté
- [ ] Favoris (aéroports, vols)
- [ ] Export des données (CSV, PDF)
- [ ] Multi-langue interface (EN, ES)

### Performance

- [ ] Mise en cache côté client
- [ ] Streaming des réponses Assistant
- [ ] Lazy loading des listes longues
