# tests/test_coach_agent.py
import pytest
from src.agents.coach_agent import parse_transit_text


# ── Existing tests (preserved) ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_parse_transit_text_walk():
    result = await parse_transit_text("I walked for 10 minutes yesterday")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "walk"
    assert result["duration_minutes"] == 10


@pytest.mark.anyio
async def test_parse_transit_text_cab():
    result = await parse_transit_text("took a cab to the office, took about 45 mins")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "cab"
    assert result["duration_minutes"] == 45


@pytest.mark.anyio
async def test_parse_transit_text_conversation_greeting():
    result = await parse_transit_text("hello there carbon coach!")
    assert result["intent"] == "conversation"
    assert result["conversational_reply"] is not None
    assert result["transit_mode"] is None


@pytest.mark.anyio
async def test_parse_transit_text_conversation_advice():
    result = await parse_transit_text("what should i do to reduce my footprint?")
    assert result["intent"] == "conversation"
    assert result["conversational_reply"] is not None
    assert result["transit_mode"] is None


# ── NEW: Mode synonym tests ─────────────────────────────────────────────────


@pytest.mark.anyio
async def test_synonym_taxi_maps_to_cab():
    result = await parse_transit_text("I took a taxi for 20 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "cab"
    assert result["duration_minutes"] == 20


@pytest.mark.anyio
async def test_synonym_uber_maps_to_cab():
    result = await parse_transit_text("uber ride for 15 minutes to the mall")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "cab"
    assert result["duration_minutes"] == 15


@pytest.mark.anyio
async def test_synonym_subway_maps_to_metro():
    result = await parse_transit_text("I rode the subway for 25 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "metro"
    assert result["duration_minutes"] == 25


@pytest.mark.anyio
async def test_synonym_train_maps_to_metro():
    result = await parse_transit_text("took the train for 30 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "metro"
    assert result["duration_minutes"] == 30


@pytest.mark.anyio
async def test_synonym_bike_maps_to_bicycle():
    result = await parse_transit_text("I biked for 12 minutes to the store")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "bicycle"
    assert result["duration_minutes"] == 12


@pytest.mark.anyio
async def test_synonym_cycle_maps_to_bicycle():
    result = await parse_transit_text("cycled to work today, 18 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "bicycle"
    assert result["duration_minutes"] == 18


@pytest.mark.anyio
async def test_synonym_shuttle_maps_to_bus():
    result = await parse_transit_text("took the shuttle for 22 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "bus"
    assert result["duration_minutes"] == 22


# ── NEW: Duration extraction from various formats ───────────────────────────


@pytest.mark.anyio
async def test_duration_extraction_min_format():
    result = await parse_transit_text("bus ride 20 min to the office")
    assert result["intent"] == "log_transit"
    assert result["duration_minutes"] == 20


@pytest.mark.anyio
async def test_duration_extraction_minutes_format():
    result = await parse_transit_text("took 45 minutes by cab")
    assert result["intent"] == "log_transit"
    assert result["duration_minutes"] == 45


@pytest.mark.anyio
async def test_duration_extraction_mins_format():
    result = await parse_transit_text("metro ride was 30 mins long")
    assert result["intent"] == "log_transit"
    assert result["duration_minutes"] == 30


# ── NEW: Conversation intent variants ────────────────────────────────────────


@pytest.mark.anyio
async def test_what_should_triggers_conversation():
    result = await parse_transit_text("what should I change about my commute?")
    assert result["intent"] == "conversation"
    assert result["conversational_reply"] is not None
    assert result["transit_mode"] is None


@pytest.mark.anyio
async def test_how_are_you_triggers_conversation():
    result = await parse_transit_text("how are you today?")
    assert result["intent"] == "conversation"
    assert result["conversational_reply"] is not None
    assert result["transit_mode"] is None


@pytest.mark.anyio
async def test_hey_triggers_conversation():
    result = await parse_transit_text("hey")
    assert result["intent"] == "conversation"
    assert result["conversational_reply"] is not None
    assert result["transit_mode"] is None


# ── NEW: Direct mode extraction ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_metro_direct_extraction():
    result = await parse_transit_text("I commuted by metro for 25 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "metro"
    assert result["duration_minutes"] == 25


@pytest.mark.anyio
async def test_bus_direct_extraction():
    result = await parse_transit_text("took the bus to work, 40 minutes")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "bus"
    assert result["duration_minutes"] == 40


@pytest.mark.anyio
async def test_walk_direct_extraction():
    result = await parse_transit_text("walked 5 minutes to the store")
    assert result["intent"] == "log_transit"
    assert result["transit_mode"] == "walk"
    assert result["duration_minutes"] == 5


# ── NEW: Response structure validation ───────────────────────────────────────


@pytest.mark.anyio
async def test_log_transit_has_null_conversational_reply():
    result = await parse_transit_text("I took a cab for 10 minutes")
    assert result["intent"] == "log_transit"
    assert result["conversational_reply"] is None


@pytest.mark.anyio
async def test_conversation_has_null_duration():
    result = await parse_transit_text("hello!")
    assert result["intent"] == "conversation"
    assert result["duration_minutes"] is None
