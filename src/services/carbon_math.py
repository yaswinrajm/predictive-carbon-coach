# src/services/carbon_math.py

# Transit constants: Speed (km/h) and Emission Factors (kg CO2 per km)
TRANSIT_METRICS = {
    "walk": {"speed": 5, "ef": 0.00},
    "bicycle": {"speed": 15, "ef": 0.00},
    "metro": {"speed": 45, "ef": 0.03},
    "bus": {"speed": 25, "ef": 0.08},
    "cab": {"speed": 35, "ef": 0.18}
}

def calculate_transport_emissions(duration_minutes: int, transit_mode: str) -> float:
    """Calculates transport emissions in kg CO2 equivalent."""
    mode = transit_mode.lower().strip()
    if mode not in TRANSIT_METRICS:
        raise ValueError(f"Unsupported transit mode: {transit_mode}")
        
    if duration_minutes < 0:
        raise ValueError("Duration cannot be negative.")
        
    metrics = TRANSIT_METRICS[mode]
    hours = duration_minutes / 60.0
    distance_km = hours * metrics["speed"]
    co2_kg = distance_km * metrics["ef"]
    
    return round(co2_kg, 2)