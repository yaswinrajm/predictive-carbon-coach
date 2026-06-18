"""Carbon emissions calculation engine for the Predictive Carbon Coach.

Provides functions to help individuals understand their carbon footprint
through personalized transport metrics. Calculates CO2 emissions, travel
distances, impact classifications, and actionable mode-swap recommendations
to reduce environmental impact through simple, repeatable actions.
"""
from typing import Tuple, Optional

# Constants to eliminate magic numbers and improve memory tracking
MINUTES_IN_HOUR = 60.0
LOW_IMPACT_THRESHOLD = 0.75
MODERATE_IMPACT_THRESHOLD = 2.0
WALK_SUGGESTION_LIMIT_MINS = 20
BIKE_SUGGESTION_LIMIT_MINS = 35

TRANSIT_METRICS = {
    "walk": {"speed": 5, "ef": 0.00, "label": "Walk"},
    "bicycle": {"speed": 15, "ef": 0.00, "label": "Bicycle"},
    "metro": {"speed": 45, "ef": 0.03, "label": "Metro"},
    "bus": {"speed": 25, "ef": 0.08, "label": "Bus"},
    "cab": {"speed": 35, "ef": 0.18, "label": "Cab"},
}


def _normalize_inputs(duration_minutes: int, transit_mode: str) -> Tuple[int, str]:
    if not isinstance(duration_minutes, int) or isinstance(duration_minutes, bool):
        raise ValueError("duration_minutes must be a valid integer.")
    if not isinstance(transit_mode, str):
        raise ValueError("transit_mode must be a string.")
    if duration_minutes < 0:
        raise ValueError("duration_minutes cannot be negative.")

    mode = transit_mode.lower().strip()
    if mode not in TRANSIT_METRICS:
        raise ValueError(f"Unsupported transit mode: {transit_mode}")

    return duration_minutes, mode


def calculate_transport_emissions(duration_minutes: int, transit_mode: str) -> float:
    """Calculates transport emissions in kg CO2 equivalent."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, transit_mode)
    metrics = TRANSIT_METRICS[mode]
    distance_km = (duration_minutes / MINUTES_IN_HOUR) * metrics["speed"]
    return round(distance_km * metrics["ef"], 2)


def calculate_distance_km(duration_minutes: int, transit_mode: str) -> float:
    """Estimates distance from mode-specific average speeds."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, transit_mode)
    speed = TRANSIT_METRICS[mode]["speed"]
    return round((duration_minutes / MINUTES_IN_HOUR) * speed, 1)


def recommend_lower_carbon_mode(duration_minutes: int, transit_mode: str) -> Optional[str]:
    """Suggests a realistic lower-carbon swap for the given trip."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, transit_mode)

    if mode in {"walk", "bicycle"}:
        return None
    if duration_minutes <= WALK_SUGGESTION_LIMIT_MINS:
        return "walk"
    if duration_minutes <= BIKE_SUGGESTION_LIMIT_MINS:
        return "bicycle"
    if mode in {"cab", "bus"}:
        return "metro"
    return "bicycle"


def estimate_savings_for_mode_swap(
    duration_minutes: int, current_mode: str, suggested_mode: Optional[str]
) -> float:
    """Calculates avoided emissions if the rider took the suggested mode instead."""
    if not suggested_mode:
        return 0.0

    duration_minutes, mode = _normalize_inputs(duration_minutes, current_mode)
    current_emissions = calculate_transport_emissions(duration_minutes, mode)
    suggested_emissions = calculate_transport_emissions(duration_minutes, suggested_mode)
    return round(max(current_emissions - suggested_emissions, 0.0), 2)


def classify_trip_impact(carbon_kg: float) -> str:
    """Buckets a trip into a soft impact band for UI messaging."""
    if carbon_kg <= 0.0:
        return "low"
    if carbon_kg < LOW_IMPACT_THRESHOLD:
        return "light"
    if carbon_kg < MODERATE_IMPACT_THRESHOLD:
        return "moderate"
    return "high"
