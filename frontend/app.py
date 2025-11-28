"""
Hello Mira Flight Platform - Frontend Streamlit
Interface conversationnelle avec authentification Supabase
"""

import streamlit as st
import requests
import os
from datetime import datetime

# Configuration des URLs des APIs backend
ASSISTANT_URL = os.getenv("ASSISTANT_URL", "http://localhost:8003")
AIRPORT_URL = os.getenv("AIRPORT_URL", "http://localhost:8001")
FLIGHT_URL = os.getenv("FLIGHT_URL", "http://localhost:8002")

# Configuration de la page
st.set_page_config(
    page_title="Hello Mira - Flight Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# AUTHENTIFICATION SUPABASE
# =============================================================================

def init_supabase_auth():
    """Initialise l'authentification Supabase avec st_login_form."""
    # Vérifie si déjà authentifié
    if st.session_state.get("authenticated", False):
        return True

    # Vérifie si Supabase est configuré dans les secrets
    supabase_configured = False
    try:
        if "connections" in st.secrets and "supabase" in st.secrets["connections"]:
            supabase_configured = True
    except Exception:
        pass

    if not supabase_configured:
        st.warning("⚠️ Supabase non configuré - Mode démo activé")
        st.caption("Pour configurer: créez .streamlit/secrets.toml avec vos credentials Supabase")
        if st.button("🚀 Continuer en mode démo"):
            st.session_state["authenticated"] = True
            st.session_state["username"] = "demo_user"
            st.rerun()
        st.stop()

    # Import et affichage du formulaire de login
    try:
        from st_login_form import login_form

        # login_form utilise automatiquement st.connection("supabase")
        # Les credentials sont lus depuis secrets.toml
        client = login_form(
            title="✈️ Hello Mira Flight Platform",
            user_tablename="users",
            create_title="Créer un compte",
            login_title="Se connecter",
            allow_guest=True,
            guest_title="Continuer en tant qu'invité"
        )

        if st.session_state.get("authenticated"):
            return True
        else:
            st.stop()

    except ImportError as e:
        st.error(f"Module st_login_form non installé: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Erreur authentification: {e}")
        if st.button("🚀 Continuer en mode démo"):
            st.session_state["authenticated"] = True
            st.session_state["username"] = "demo_user"
            st.rerun()
        st.stop()

# =============================================================================
# FONCTIONS API
# =============================================================================

def call_assistant(prompt: str) -> dict:
    """Appelle l'API Assistant pour une réponse en langage naturel."""
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

def search_airport(query: str) -> dict:
    """Recherche un aéroport par code IATA ou nom."""
    try:
        # Essaie d'abord par IATA (3 lettres)
        if len(query) == 3 and query.isalpha():
            response = requests.get(
                f"{AIRPORT_URL}/api/v1/airports/{query.upper()}",
                timeout=10
            )
        else:
            response = requests.get(
                f"{AIRPORT_URL}/api/v1/airports/search",
                params={"query": query},
                timeout=10
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_departures(iata: str, limit: int = 10) -> dict:
    """Récupère les vols au départ d'un aéroport."""
    try:
        response = requests.get(
            f"{AIRPORT_URL}/api/v1/airports/{iata}/departures",
            params={"limit": limit},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_arrivals(iata: str, limit: int = 10) -> dict:
    """Récupère les vols à l'arrivée d'un aéroport."""
    try:
        response = requests.get(
            f"{AIRPORT_URL}/api/v1/airports/{iata}/arrivals",
            params={"limit": limit},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_flight_status(flight_iata: str) -> dict:
    """Récupère le statut d'un vol."""
    try:
        response = requests.get(
            f"{FLIGHT_URL}/api/v1/flights/{flight_iata.upper()}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# =============================================================================
# COMPOSANTS UI
# =============================================================================

def render_flight_card(flight: dict):
    """Affiche une carte de vol avec les infos clés."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        flight_num = flight.get("flight_iata") or flight.get("flight", {}).get("iata", "N/A")
        st.markdown(f"### ✈️ {flight_num}")

        dep = flight.get("departure", {})
        arr = flight.get("arrival", {})

        dep_airport = dep.get("iata", "???")
        arr_airport = arr.get("iata", "???")

        st.markdown(f"**{dep_airport}** → **{arr_airport}**")

        # Pays de destination si disponible
        if arr.get("country"):
            st.caption(f"🌍 Destination: {arr.get('country')}")

    with col2:
        status = flight.get("flight_status", "unknown")
        status_colors = {
            "scheduled": "🟡",
            "active": "🟢",
            "landed": "🔵",
            "cancelled": "🔴",
            "diverted": "🟠"
        }
        st.markdown(f"{status_colors.get(status, '⚪')} **{status.upper()}**")

        # Retard
        delay = dep.get("delay")
        if delay and delay > 0:
            st.markdown(f"⏱️ Retard: **{delay} min**")

    with col3:
        dep_time = dep.get("scheduled", dep.get("estimated", ""))
        if dep_time:
            try:
                dt = datetime.fromisoformat(dep_time.replace("Z", "+00:00"))
                st.markdown(f"🛫 {dt.strftime('%H:%M')}")
            except:
                st.markdown(f"🛫 {dep_time[:16]}")

        arr_time = arr.get("scheduled", arr.get("estimated", ""))
        if arr_time:
            try:
                dt = datetime.fromisoformat(arr_time.replace("Z", "+00:00"))
                st.markdown(f"🛬 {dt.strftime('%H:%M')}")
            except:
                st.markdown(f"🛬 {arr_time[:16]}")

def get_country_flag(country_code: str) -> str:
    """Retourne l'emoji drapeau pour un code pays ISO."""
    if not country_code or len(country_code) != 2:
        return "🌍"
    return "".join(chr(ord(c) + 127397) for c in country_code.upper())

# =============================================================================
# PAGES
# =============================================================================

def page_chat():
    """Page principale - Chat avec l'Assistant IA."""
    st.header("💬 Assistant de Vol")
    st.caption("Posez vos questions en langage naturel (FR/EN/ES)")

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
    if prompt := st.chat_input("Que voulez-vous savoir ? Ex: 'À quelle heure arrive le vol AF282 ?'"):
        # Affiche message utilisateur
        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Appelle l'assistant
        with st.chat_message("assistant"):
            with st.spinner("Recherche en cours..."):
                result = call_assistant(prompt)

            answer = result.get("answer", result.get("error", "Erreur inconnue"))
            st.write(answer)

            # Affiche données structurées si présentes
            data = result.get("data")
            if data and not result.get("error"):
                with st.expander("📊 Données détaillées"):
                    st.json(data)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "data": data
        })

    # Bouton pour effacer l'historique
    if st.session_state.chat_history:
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.chat_history = []
            st.rerun()

def page_airports():
    """Page de recherche d'aéroports."""
    st.header("🏢 Recherche d'Aéroports")

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Code IATA ou nom de ville",
            placeholder="Ex: CDG, Paris, JFK...",
            key="airport_search"
        )

    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Rechercher", type="primary")

    if search_btn and query:
        with st.spinner("Recherche..."):
            result = search_airport(query)

        if "error" in result:
            st.error(f"Erreur: {result['error']}")
        else:
            # Affiche résultat
            airports = result if isinstance(result, list) else [result]

            for airport in airports:
                if not airport:
                    continue

                country_code = airport.get("country_iso2", "")
                flag = get_country_flag(country_code)

                with st.container():
                    st.markdown(f"""
                    ### {flag} {airport.get('airport_name', 'N/A')} ({airport.get('iata_code', 'N/A')})

                    | Info | Valeur |
                    |------|--------|
                    | **Ville** | {airport.get('city', 'N/A')} |
                    | **Pays** | {airport.get('country_name', 'N/A')} |
                    | **Timezone** | {airport.get('timezone', 'N/A')} |
                    | **Coordonnées** | {airport.get('latitude', 'N/A')}, {airport.get('longitude', 'N/A')} |
                    """)

                    # Boutons pour voir départs/arrivées
                    col1, col2 = st.columns(2)
                    iata = airport.get('iata_code')

                    if iata:
                        with col1:
                            if st.button(f"🛫 Départs de {iata}", key=f"dep_{iata}"):
                                st.session_state["selected_airport"] = iata
                                st.session_state["view_mode"] = "departures"
                        with col2:
                            if st.button(f"🛬 Arrivées à {iata}", key=f"arr_{iata}"):
                                st.session_state["selected_airport"] = iata
                                st.session_state["view_mode"] = "arrivals"

                    st.divider()

def page_flights():
    """Page de consultation des vols."""
    st.header("✈️ Vols")

    # Tabs pour départs/arrivées/statut
    tab1, tab2, tab3 = st.tabs(["🛫 Départs", "🛬 Arrivées", "🔍 Statut Vol"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            dep_iata = st.text_input(
                "Code IATA aéroport",
                value=st.session_state.get("selected_airport", "CDG"),
                key="dep_iata"
            )
        with col2:
            dep_limit = st.number_input("Nombre de vols", 5, 50, 10, key="dep_limit")

        if st.button("Voir les départs", type="primary", key="btn_departures"):
            with st.spinner("Chargement..."):
                result = get_departures(dep_iata.upper(), dep_limit)

            if "error" in result:
                st.error(f"Erreur: {result['error']}")
            else:
                flights = result.get("departures", result.get("data", []))
                if isinstance(result, list):
                    flights = result

                st.success(f"✅ {len(flights)} vols trouvés")

                for flight in flights:
                    with st.container():
                        render_flight_card(flight)
                        st.divider()

    with tab2:
        col1, col2 = st.columns([2, 1])
        with col1:
            arr_iata = st.text_input(
                "Code IATA aéroport",
                value=st.session_state.get("selected_airport", "CDG"),
                key="arr_iata"
            )
        with col2:
            arr_limit = st.number_input("Nombre de vols", 5, 50, 10, key="arr_limit")

        if st.button("Voir les arrivées", type="primary", key="btn_arrivals"):
            with st.spinner("Chargement..."):
                result = get_arrivals(arr_iata.upper(), arr_limit)

            if "error" in result:
                st.error(f"Erreur: {result['error']}")
            else:
                flights = result.get("arrivals", result.get("data", []))
                if isinstance(result, list):
                    flights = result

                st.success(f"✅ {len(flights)} vols trouvés")

                for flight in flights:
                    with st.container():
                        render_flight_card(flight)
                        st.divider()

    with tab3:
        flight_num = st.text_input(
            "Numéro de vol",
            placeholder="Ex: AF282, BA117...",
            key="flight_status_input"
        )

        if st.button("🔍 Voir le statut", type="primary", key="btn_status"):
            if flight_num:
                with st.spinner("Recherche..."):
                    result = get_flight_status(flight_num)

                if "error" in result:
                    st.error(f"Erreur: {result['error']}")
                else:
                    render_flight_card(result)

                    # Détails supplémentaires
                    with st.expander("📋 Détails complets"):
                        st.json(result)
            else:
                st.warning("Veuillez entrer un numéro de vol")

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal de l'application."""

    # Authentification
    init_supabase_auth()

    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/lougail/hello-mira-flight-platform/main/docs/logo.png", width=150)
        st.title("✈️ Hello Mira")
        st.caption("Flight Platform")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            ["💬 Assistant", "🏢 Aéroports", "✈️ Vols"],
            label_visibility="collapsed"
        )

        st.divider()

        # Info utilisateur
        username = st.session_state.get("username", "Invité")
        st.caption(f"👤 Connecté: {username}")

        if st.button("🚪 Déconnexion"):
            # Nettoie tous les états de session (y compris st_login_form)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Vide aussi le cache
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.caption("v1.0.0 | Nov 2025")

    # Contenu principal
    if page == "💬 Assistant":
        page_chat()
    elif page == "🏢 Aéroports":
        page_airports()
    elif page == "✈️ Vols":
        page_flights()

if __name__ == "__main__":
    main()
