# tests/test_api.py
from fastapi.testclient import TestClient

import src.main as main_module


# ── Existing tests (preserved) ──────────────────────────────────────────────


def test_health_endpoint_sets_security_headers(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "leafline"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_chat_endpoint_returns_trip_metadata(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    async def fake_parse_transit_text(_message: str):
        return {
            "intent": "log_transit",
            "transit_mode": "cab",
            "duration_minutes": 30,
            "conversational_reply": None,
        }

    monkeypatch.setattr(main_module, "parse_transit_text", fake_parse_transit_text)

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"message": "I took a cab for 30 minutes"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["mode"] == "cab"
    assert payload["data"]["duration"] == 30
    assert payload["data"]["carbon_kg"] == 3.15
    assert payload["data"]["distance_km"] == 17.5
    assert payload["data"]["suggested_mode"] == "bicycle"
    assert payload["data"]["potential_savings_kg"] == 3.15
    assert payload["data"]["impact_level"] == "high"
    assert "save about 3.15 kg CO2e" in payload["reply"]


def test_chat_endpoint_rejects_empty_and_too_long_messages(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        empty_response = client.post("/api/chat", json={"message": "   "})
        long_response = client.post("/api/chat", json={"message": "x" * 281})

    assert empty_response.status_code == 422
    assert long_response.status_code == 422


# ── NEW: Conversation intent returns data: None ──────────────────────────────


def test_chat_conversation_intent_returns_no_trip_data(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    async def fake_parse_conversation(_message: str):
        return {
            "intent": "conversation",
            "transit_mode": None,
            "duration_minutes": None,
            "conversational_reply": "Hello! I'm here to help you track your carbon footprint.",
        }

    monkeypatch.setattr(main_module, "parse_transit_text", fake_parse_conversation)

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"message": "hello there!"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"] is None
    assert payload["reply"] is not None
    assert len(payload["reply"]) > 0


# ── NEW: Root endpoint serves HTML ───────────────────────────────────────────


def test_root_endpoint_returns_html(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ── NEW: Metro trip returns correct fields ───────────────────────────────────


def test_chat_metro_trip_returns_correct_fields(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    async def fake_parse_metro(_message: str):
        return {
            "intent": "log_transit",
            "transit_mode": "metro",
            "duration_minutes": 30,
            "conversational_reply": None,
        }

    monkeypatch.setattr(main_module, "parse_transit_text", fake_parse_metro)

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"message": "metro for 30 minutes"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["mode"] == "metro"
    assert payload["data"]["carbon_kg"] == 0.67
    assert payload["data"]["distance_km"] == 22.5
    assert payload["data"]["impact_level"] == "light"


# ── NEW: Invalid JSON body returns 422 ───────────────────────────────────────


def test_chat_invalid_json_body_returns_422(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/chat",
            content="this is not json",
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 422


# ── NEW: Missing message field returns 422 ───────────────────────────────────


def test_chat_missing_message_field_returns_422(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"text": "wrong field name"})

    assert response.status_code == 422


# ── NEW: Health endpoint returns correct schema ──────────────────────────────


def test_health_endpoint_returns_correct_schema(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    with TestClient(main_module.app) as client:
        response = client.get("/api/health")

    payload = response.json()
    assert "status" in payload
    assert "service" in payload
    assert payload["status"] == "healthy"
    assert payload["service"] == "leafline"


# ── NEW: Security headers present on all responses ──────────────────────────


def test_security_headers_on_chat_endpoint(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    async def fake_parse(_message: str):
        return {
            "intent": "conversation",
            "transit_mode": None,
            "duration_minutes": None,
            "conversational_reply": "Hello!",
        }

    monkeypatch.setattr(main_module, "parse_transit_text", fake_parse)

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"message": "hi"})

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "same-origin"
    assert response.headers["cache-control"] == "no-store"


# ── NEW: Walk trip returns zero emissions ────────────────────────────────────


def test_chat_walk_trip_returns_zero_emissions(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_API_KEY", "")
    main_module.REQUEST_LOG.clear()

    async def fake_parse_walk(_message: str):
        return {
            "intent": "log_transit",
            "transit_mode": "walk",
            "duration_minutes": 20,
            "conversational_reply": None,
        }

    monkeypatch.setattr(main_module, "parse_transit_text", fake_parse_walk)

    with TestClient(main_module.app) as client:
        response = client.post("/api/chat", json={"message": "walked for 20 mins"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["carbon_kg"] == 0.0
    assert payload["data"]["impact_level"] == "low"
