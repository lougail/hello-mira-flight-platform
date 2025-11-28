"""Module de monitoring pour le service Flight."""

from .metrics import (
    flight_lookups,
    flight_lookup_latency,
    mongodb_operations,
    flights_stored,
    history_flights_count,
    statistics_calculated,
    statistics_flights_analyzed,
    last_on_time_rate,
    last_delay_rate,
    last_average_delay,
)

__all__ = [
    "flight_lookups",
    "flight_lookup_latency",
    "mongodb_operations",
    "flights_stored",
    "history_flights_count",
    "statistics_calculated",
    "statistics_flights_analyzed",
    "last_on_time_rate",
    "last_delay_rate",
    "last_average_delay",
]