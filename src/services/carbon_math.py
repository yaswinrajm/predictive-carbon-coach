"""Carbon emissions calculation engine for the Predictive Carbon Coach.

Provides functions to help individuals understand their carbon footprint
through personalized transport metrics. Calculates CO2 emissions, travel
distances, impact classifications, and actionable mode-swap recommendations
to reduce environmental impact through simple, repeatable actions.
"""

TRANSIT_METRICS = {
    "walk": {"speed": 5, "ef": 0.00, "label": "Walk"},
    "bicycle": {"speed": 15, "ef": 0.00, "label": "Bicycle"},
    "metro": {"speed": 45, "ef": 0.03, "label": "Metro"},
    "bus": {"speed": 25, "ef": 0.08, "label": "Bus"},
    "cab": {"speed": 35, "ef": 0.18, "label": "Cab"},
}


def _normalize_inputs(duration_minutes: int, transit_mode: str) -> tuple[int, str]:
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
    hours = duration_minutes / 60.0
    distance_km = hours * metrics["speed"]
    co2_kg = distance_km * metrics["ef"]

    return round(co2_kg, 2)


def calculate_distance_km(duration_minutes: int, transit_mode: str) -> float:
    """Estimates distance from mode-specific average speeds."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, transit_mode)
    metrics = TRANSIT_METRICS[mode]
    hours = duration_minutes / 60.0
    return round(hours * metrics["speed"], 1)


def recommend_lower_carbon_mode(duration_minutes: int, transit_mode: str) -> str | None:
    """Suggests a realistic lower-carbon swap for the given trip."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, transit_mode)

    if mode in {"walk", "bicycle"}:
        return None
    if duration_minutes <= 20:
        return "walk"
    if duration_minutes <= 35:
        return "bicycle"
    if mode == "cab":
        return "metro"
    if mode == "bus":
        return "metro"
    return "bicycle"


def estimate_savings_for_mode_swap(duration_minutes: int, current_mode: str, suggested_mode: str | None) -> float:
    """Calculates avoided emissions if the rider took the suggested mode instead."""
    duration_minutes, mode = _normalize_inputs(duration_minutes, current_mode)

    if not suggested_mode:
        return 0.0

    current_emissions = calculate_transport_emissions(duration_minutes, mode)
    suggested_emissions = calculate_transport_emissions(duration_minutes, suggested_mode)
    return round(max(current_emissions - suggested_emissions, 0.0), 2)


def classify_trip_impact(carbon_kg: float) -> str:
    """Buckets a trip into a soft impact band for UI messaging."""
    if carbon_kg <= 0:
        return "low"
    if carbon_kg < 0.75:
        return "light"
    if carbon_kg < 2:
        return "moderate"
    return "high"
