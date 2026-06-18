# tests/test_carbon_math.py
import pytest
from src.services.carbon_math import (
    calculate_distance_km,
    calculate_transport_emissions,
    classify_trip_impact,
    estimate_savings_for_mode_swap,
    recommend_lower_carbon_mode,
)

# ── Existing tests (preserved) ──────────────────────────────────────────────


def test_bus_emission_calculation():
    # 30 mins bus @ 25 km/h = 12.5 km * 0.08 kg/km = 1.0 kg CO2
    assert calculate_transport_emissions(30, "bus") == 1.0


def test_zero_emission_modes():
    assert calculate_transport_emissions(60, "walk") == 0.0
    assert calculate_transport_emissions(15, "bicycle") == 0.0


def test_distance_and_recommendation_helpers():
    assert calculate_distance_km(30, "bus") == 12.5
    assert recommend_lower_carbon_mode(15, "cab") == "walk"
    assert recommend_lower_carbon_mode(30, "bus") == "bicycle"
    assert recommend_lower_carbon_mode(50, "cab") == "metro"
    assert recommend_lower_carbon_mode(25, "walk") is None


def test_swap_savings_and_impact_bands():
    assert estimate_savings_for_mode_swap(30, "cab", "bicycle") == 3.15
    assert estimate_savings_for_mode_swap(20, "walk", None) == 0.0
    assert classify_trip_impact(0.0) == "low"
    assert classify_trip_impact(0.5) == "light"
    assert classify_trip_impact(1.2) == "moderate"
    assert classify_trip_impact(2.5) == "high"


def test_invalid_inputs():
    # Unsupported mode
    with pytest.raises(ValueError):
        calculate_transport_emissions(20, "rocket")
    # Negative duration
    with pytest.raises(ValueError):
        calculate_transport_emissions(-10, "bus")
    # Invalid duration types
    with pytest.raises(ValueError):
        calculate_transport_emissions("30", "bus")
    with pytest.raises(ValueError):
        calculate_transport_emissions(30.5, "bus")
    with pytest.raises(ValueError):
        calculate_transport_emissions(True, "bus")
    with pytest.raises(ValueError):
        calculate_transport_emissions(None, "bus")
    # Invalid mode types
    with pytest.raises(ValueError):
        calculate_transport_emissions(30, 123)
    with pytest.raises(ValueError):
        calculate_transport_emissions(30, None)


# ── NEW: Parametrized test covering ALL 5 transit modes ─────────────────────


@pytest.mark.parametrize(
    "mode, duration, expected_kg",
    [
        ("walk", 60, 0.0),        # speed=5, ef=0 → 0.0 kg
        ("bicycle", 60, 0.0),     # speed=15, ef=0 → 0.0 kg
        ("metro", 30, 0.67),      # 0.5h * 45 * 0.03 = 0.675 → round(0.675, 2) = 0.67
        ("bus", 30, 1.0),         # 0.5h * 25 * 0.08 = 1.0
        ("cab", 30, 3.15),        # 0.5h * 35 * 0.18 = 3.15
    ],
)
def test_all_modes_exact_emissions(mode, duration, expected_kg):
    assert calculate_transport_emissions(duration, mode) == expected_kg


# ── NEW: Zero duration returns zero ─────────────────────────────────────────


def test_zero_duration_returns_zero():
    assert calculate_transport_emissions(0, "bus") == 0.0


# ── NEW: Case insensitivity & whitespace handling ────────────────────────────


def test_case_insensitivity_upper():
    assert calculate_transport_emissions(30, "BUS") == 1.0


def test_case_insensitivity_mixed_with_whitespace():
    assert calculate_transport_emissions(30, " Bus ") == 1.0


# ── NEW: classify_trip_impact boundary tests ─────────────────────────────────
# Source: <=0 → low, <0.75 → light, <2 → moderate, >=2 → high


def test_classify_boundary_at_0_75():
    # 0.75 is NOT < 0.75, so it falls to the next band: "moderate"
    assert classify_trip_impact(0.75) == "moderate"


def test_classify_boundary_at_2_0():
    # 2.0 is NOT < 2, so it falls to the last band: "high"
    assert classify_trip_impact(2.0) == "high"


def test_classify_boundary_just_below_0_75():
    assert classify_trip_impact(0.74) == "light"


def test_classify_boundary_just_below_2():
    assert classify_trip_impact(1.99) == "moderate"


def test_classify_negative_value():
    assert classify_trip_impact(-1.0) == "low"


# ── NEW: estimate_savings with same mode ─────────────────────────────────────


def test_swap_savings_same_mode():
    assert estimate_savings_for_mode_swap(30, "bus", "bus") == 0.0


# ── NEW: recommend_lower_carbon_mode for bicycle returns None ────────────────


def test_recommend_for_bicycle_returns_none():
    assert recommend_lower_carbon_mode(30, "bicycle") is None


def test_recommend_for_walk_returns_none():
    assert recommend_lower_carbon_mode(60, "walk") is None


# ── NEW: recommend_lower_carbon_mode for metro ──────────────────────────────


def test_recommend_for_metro():
    # metro is not walk/bicycle and duration > 35, falls to final return "bicycle"
    assert recommend_lower_carbon_mode(50, "metro") == "bicycle"


def test_recommend_for_short_metro():
    # duration <= 20 → walk
    assert recommend_lower_carbon_mode(15, "metro") == "walk"


def test_recommend_for_medium_bus():
    # duration > 20 and <= 35 → bicycle
    assert recommend_lower_carbon_mode(25, "bus") == "bicycle"


# ── NEW: calculate_distance_km for ALL 5 modes ──────────────────────────────


@pytest.mark.parametrize(
    "mode, duration, expected_km",
    [
        ("walk", 60, 5.0),        # 1h * 5 km/h
        ("bicycle", 60, 15.0),    # 1h * 15 km/h
        ("metro", 30, 22.5),      # 0.5h * 45 km/h
        ("bus", 30, 12.5),        # 0.5h * 25 km/h
        ("cab", 30, 17.5),        # 0.5h * 35 km/h
    ],
)
def test_distance_km_all_modes(mode, duration, expected_km):
    assert calculate_distance_km(duration, mode) == expected_km


# ── NEW: Individual ValueError tests (separate functions) ───────────────────


def test_error_unsupported_mode():
    with pytest.raises(ValueError, match="Unsupported transit mode"):
        calculate_transport_emissions(20, "rocket")


def test_error_negative_duration():
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_transport_emissions(-10, "bus")


def test_error_string_duration():
    with pytest.raises(ValueError, match="must be a valid integer"):
        calculate_transport_emissions("30", "bus")


def test_error_float_duration():
    with pytest.raises(ValueError, match="must be a valid integer"):
        calculate_transport_emissions(30.5, "bus")


def test_error_bool_duration():
    with pytest.raises(ValueError, match="must be a valid integer"):
        calculate_transport_emissions(True, "bus")


def test_error_none_duration():
    with pytest.raises(ValueError, match="must be a valid integer"):
        calculate_transport_emissions(None, "bus")


def test_error_int_mode():
    with pytest.raises(ValueError, match="must be a string"):
        calculate_transport_emissions(30, 123)


def test_error_none_mode():
    with pytest.raises(ValueError, match="must be a string"):
        calculate_transport_emissions(30, None)


# ── NEW: ValueError tests for other functions ────────────────────────────────


def test_distance_error_unsupported_mode():
    with pytest.raises(ValueError):
        calculate_distance_km(30, "spaceship")


def test_recommend_error_unsupported_mode():
    with pytest.raises(ValueError):
        recommend_lower_carbon_mode(30, "helicopter")


def test_savings_error_unsupported_mode():
    with pytest.raises(ValueError):
        estimate_savings_for_mode_swap(30, "airplane", "bus")


def test_savings_with_none_suggested():
    assert estimate_savings_for_mode_swap(30, "cab", None) == 0.0
