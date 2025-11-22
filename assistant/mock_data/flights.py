"""
Données mockées pour les vols.

Contient des vols fictifs cohérents pour la démonstration.
"""

from datetime import datetime, timedelta

# Date/heure actuelle pour des données réalistes
NOW = datetime.utcnow()
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)

# =============================================================================
# VOLS MOCKES (pour l'exemple "Je suis sur le vol AV15")
# =============================================================================

MOCK_FLIGHTS = {
    "AV15": {
        "flight_date": TODAY.strftime("%Y-%m-%d"),
        "flight_status": "active",
        "departure": {
            "airport": "El Dorado International Airport",
            "timezone": "America/Bogota",
            "iata": "BOG",
            "icao": "SKBO",
            "terminal": "1",
            "gate": "A12",
            "delay": None,
            "scheduled": (NOW - timedelta(hours=2, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "estimated": (NOW - timedelta(hours=2, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "actual": (NOW - timedelta(hours=2, minutes=48)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        },
        "arrival": {
            "airport": "Charles de Gaulle Airport",
            "timezone": "Europe/Paris",
            "iata": "CDG",
            "icao": "LFPG",
            "terminal": "2E",
            "gate": "L24",
            "baggage": "7",
            "delay": 18,
            "scheduled": (NOW + timedelta(hours=8, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "estimated": (NOW + timedelta(hours=8, minutes=48)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "actual": None,
        },
        "airline": {
            "name": "Avianca",
            "iata": "AV",
            "icao": "AVA",
        },
        "flight": {
            "number": "15",
            "iata": "AV15",
            "icao": "AVA15",
            "codeshared": None,
        },
        "aircraft": {
            "registration": "N787AV",
            "iata": "B788",
            "icao": "B788",
            "icao24": "A12345",
        },
        "live": {
            "updated": NOW.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "latitude": 48.5,
            "longitude": 5.2,
            "altitude": 11000.0,
            "direction": 45.0,
            "speed_horizontal": 850.0,
            "speed_vertical": 0.0,
            "is_ground": False,
        },
    },
    "AF282": {
        "flight_date": TODAY.strftime("%Y-%m-%d"),
        "flight_status": "scheduled",
        "departure": {
            "airport": "Charles de Gaulle Airport",
            "timezone": "Europe/Paris",
            "iata": "CDG",
            "icao": "LFPG",
            "terminal": "2F",
            "gate": "K42",
            "delay": None,
            "scheduled": (NOW + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "estimated": (NOW + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "actual": None,
        },
        "arrival": {
            "airport": "Tokyo Narita International Airport",
            "timezone": "Asia/Tokyo",
            "iata": "NRT",
            "icao": "RJAA",
            "terminal": "1",
            "gate": None,
            "baggage": None,
            "delay": None,
            "scheduled": (NOW + timedelta(hours=16)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "estimated": (NOW + timedelta(hours=16)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "actual": None,
        },
        "airline": {
            "name": "Air France",
            "iata": "AF",
            "icao": "AFR",
        },
        "flight": {
            "number": "282",
            "iata": "AF282",
            "icao": "AFR282",
            "codeshared": None,
        },
        "aircraft": None,
        "live": None,
    },
}

# =============================================================================
# STATISTIQUES DE VOLS MOCKES
# =============================================================================

MOCK_FLIGHT_STATISTICS = {
    "AV15": {
        "flight_iata": "AV15",
        "total_flights": 156,
        "on_time": 124,
        "delayed": 28,
        "cancelled": 4,
        "on_time_percentage": 79.5,
        "average_delay_minutes": 12.3,
        "median_delay_minutes": 8.0,
        "max_delay_minutes": 145,
        "period_start": (TODAY - timedelta(days=180)).strftime("%Y-%m-%d"),
        "period_end": TODAY.strftime("%Y-%m-%d"),
    },
    "AF282": {
        "flight_iata": "AF282",
        "total_flights": 210,
        "on_time": 189,
        "delayed": 18,
        "cancelled": 3,
        "on_time_percentage": 90.0,
        "average_delay_minutes": 6.8,
        "median_delay_minutes": 5.0,
        "max_delay_minutes": 89,
        "period_start": (TODAY - timedelta(days=180)).strftime("%Y-%m-%d"),
        "period_end": TODAY.strftime("%Y-%m-%d"),
    },
}