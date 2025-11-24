"""
Données mockées pour les aéroports.

Contient des aéroports et vols au départ/arrivée fictifs.
"""

from datetime import datetime, timedelta

# Date/heure actuelle
NOW = datetime.utcnow()
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)

# =============================================================================
# AEROPORTS MOCKES
# =============================================================================

MOCK_AIRPORTS = {
    # Pour l'exemple "Trouve-moi l'aéroport le plus proche de Lille"
    "nearest_lille": {
        "airport_name": "Lille Airport",
        "iata_code": "LIL",
        "icao_code": "LFQQ",
        "latitude": 50.563332,
        "longitude": 3.086886,
        "geoname_id": "3007896",
        "timezone": "Europe/Paris",
        "gmt": "1",
        "phone_number": "+33 3 20 49 68 68",
        "country_name": "France",
        "country_iso2": "FR",
        "city_iata_code": "LIL",
        "distance_km": 8.5,
    },
    "CDG": {
        "airport_name": "Charles de Gaulle Airport",
        "iata_code": "CDG",
        "icao_code": "LFPG",
        "latitude": 49.012779,
        "longitude": 2.55,
        "geoname_id": "6269554",
        "timezone": "Europe/Paris",
        "gmt": "1",
        "phone_number": "+33 1 70 36 39 50",
        "country_name": "France",
        "country_iso2": "FR",
        "city_iata_code": "PAR",
    },
    "BOG": {
        "airport_name": "El Dorado International Airport",
        "iata_code": "BOG",
        "icao_code": "SKBO",
        "latitude": 4.701594,
        "longitude": -74.146947,
        "geoname_id": "3688689",
        "timezone": "America/Bogota",
        "gmt": "-5",
        "phone_number": "+57 1 266 2000",
        "country_name": "Colombia",
        "country_iso2": "CO",
        "city_iata_code": "BOG",
    },
}

# =============================================================================
# VOLS AU DEPART DE CDG (pour l'exemple "Quels vols partent de CDG")
# =============================================================================

MOCK_DEPARTURES = {
    "CDG": [
        {
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
                "scheduled": (NOW + timedelta(hours=1, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=1, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "arrival": {
                "airport": "John F Kennedy International Airport",
                "timezone": "America/New_York",
                "iata": "JFK",
                "icao": "KJFK",
                "terminal": "1",
                "gate": None,
                "baggage": None,
                "delay": None,
                "scheduled": (NOW + timedelta(hours=9, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=9, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "airline": {
                "name": "Air France",
                "iata": "AF",
                "icao": "AFR",
            },
            "flight": {
                "number": "007",
                "iata": "AF007",
                "icao": "AFR007",
                "codeshared": None,
            },
        },
        {
            "flight_date": TODAY.strftime("%Y-%m-%d"),
            "flight_status": "scheduled",
            "departure": {
                "airport": "Charles de Gaulle Airport",
                "timezone": "Europe/Paris",
                "iata": "CDG",
                "icao": "LFPG",
                "terminal": "2E",
                "gate": "L12",
                "delay": None,
                "scheduled": (NOW + timedelta(hours=2, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=2, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "arrival": {
                "airport": "Dubai International Airport",
                "timezone": "Asia/Dubai",
                "iata": "DXB",
                "icao": "OMDB",
                "terminal": "3",
                "gate": None,
                "baggage": None,
                "delay": None,
                "scheduled": (NOW + timedelta(hours=8, minutes=45)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=8, minutes=45)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "airline": {
                "name": "Emirates",
                "iata": "EK",
                "icao": "UAE",
            },
            "flight": {
                "number": "073",
                "iata": "EK073",
                "icao": "UAE073",
                "codeshared": None,
            },
        },
        {
            "flight_date": TODAY.strftime("%Y-%m-%d"),
            "flight_status": "active",
            "departure": {
                "airport": "Charles de Gaulle Airport",
                "timezone": "Europe/Paris",
                "iata": "CDG",
                "icao": "LFPG",
                "terminal": "2G",
                "gate": "M03",
                "delay": 15,
                "scheduled": (NOW - timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW - timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": (NOW - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            },
            "arrival": {
                "airport": "Barcelona-El Prat Airport",
                "timezone": "Europe/Madrid",
                "iata": "BCN",
                "icao": "LEBL",
                "terminal": "1",
                "gate": None,
                "baggage": None,
                "delay": 15,
                "scheduled": (NOW + timedelta(hours=1, minutes=40)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=1, minutes=55)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "airline": {
                "name": "Vueling",
                "iata": "VY",
                "icao": "VLG",
            },
            "flight": {
                "number": "8004",
                "iata": "VY8004",
                "icao": "VLG8004",
                "codeshared": None,
            },
        },
        {
            "flight_date": TODAY.strftime("%Y-%m-%d"),
            "flight_status": "scheduled",
            "departure": {
                "airport": "Charles de Gaulle Airport",
                "timezone": "Europe/Paris",
                "iata": "CDG",
                "icao": "LFPG",
                "terminal": "2F",
                "gate": "K18",
                "delay": None,
                "scheduled": (NOW + timedelta(hours=3, minutes=45)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=3, minutes=45)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "arrival": {
                "airport": "Heathrow Airport",
                "timezone": "Europe/London",
                "iata": "LHR",
                "icao": "EGLL",
                "terminal": "5",
                "gate": None,
                "baggage": None,
                "delay": None,
                "scheduled": (NOW + timedelta(hours=5, minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=5, minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "actual": None,
            },
            "airline": {
                "name": "British Airways",
                "iata": "BA",
                "icao": "BAW",
            },
            "flight": {
                "number": "314",
                "iata": "BA314",
                "icao": "BAW314",
                "codeshared": None,
            },
        },
        {
            "flight_date": TODAY.strftime("%Y-%m-%d"),
            "flight_status": "scheduled",
            "departure": {
                "airport": "Charles de Gaulle Airport",
                "timezone": "Europe/Paris",
                "iata": "CDG",
                "icao": "LFPG",
                "terminal": "2F",
                "gate": "K55",
                "delay": None,
                "scheduled": (NOW + timedelta(hours=4, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=4, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
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
                "scheduled": (NOW + timedelta(hours=16, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "estimated": (NOW + timedelta(hours=16, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
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
        },
    ]
}

# =============================================================================
# VOLS A L'ARRIVEE (vide pour l'instant, peut être ajouté si nécessaire)
# =============================================================================

MOCK_ARRIVALS = {}