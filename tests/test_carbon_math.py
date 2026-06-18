# tests/test_carbon_math.py
import pytest
from src.services.carbon_math import calculate_transport_emissions

def test_bus_emission_calculation():
    # 30 mins bus @ 25 km/h = 12.5 km * 0.08 kg/km = 1.0 kg CO2
    assert calculate_transport_emissions(30, "bus") == 1.0

def test_zero_emission_modes():
    assert calculate_transport_emissions(60, "walk") == 0.0
    assert calculate_transport_emissions(15, "bicycle") == 0.0

def test_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_transport_emissions(20, "rocket")
    with pytest.raises(ValueError):
        calculate_transport_emissions(-10, "bus")