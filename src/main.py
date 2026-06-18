# src/main.py
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from fastapi.staticfiles import StaticFiles
from src.agents.coach_agent import parse_transit_text
from src.services.carbon_math import (
    calculate_distance_km,
    calculate_transport_emissions,
    classify_trip_impact,
    estimate_savings_for_mode_swap,
    recommend_lower_carbon_mode,
)

MAX_CHAT_MESSAGE_LENGTH = 280
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
REQUEST_LOG: dict[str, deque[float]] = defaultdict(deque)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation diagnostic check
    api_key = os.getenv("ANTIGRAVITY_API_KEY")
    print("\n" + "="*80)
    if not api_key:
        print("WARNING: ANTIGRAVITY_API_KEY env variable is missing.")
        print("Using local mock/regex fallback parser. Live Gemini tracking is inactive.")
    else:
        print("INFO: Detecting ANTIGRAVITY_API_KEY in environment variables.")
        print("Verifying connection to Gemini API...")
        try:
            from google.antigravity import Agent, LocalAgentConfig
            # Run a fast async diagnostic chat
            config = LocalAgentConfig(
                system_instructions="Verify connectivity.",
                api_key=api_key
            )
            async with Agent(config) as agent:
                await agent.chat("ping")
            print("SUCCESS: Gemini API connection verified successfully! Live telemetry parsing is active.")
        except Exception as e:
            print(f"WARNING: Gemini API connectivity diagnostic failed ({e}).")
            print("Falling back to local mock/regex parser to maintain 100% service uptime.")
    print("="*80 + "\n")
    yield

app = FastAPI(
    title="Leafline — The Predictive Carbon Coach",
    description="Helps individuals understand, track, and reduce their carbon footprint through simple actions and personalized insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# Static directory structure matching project initialization guidelines
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC_FILE_PATH = os.path.join(STATIC_DIR, "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Strict request body validation matching standard production APIs
class ChatPayload(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message payload cannot be empty.")
        return cleaned


def _build_trip_insight(mode: str, duration: int, carbon_kg: float) -> tuple[str, str | None, float]:
    suggested_mode = recommend_lower_carbon_mode(duration, mode)
    savings_kg = estimate_savings_for_mode_swap(duration, mode, suggested_mode)

    if mode == "cab":
        insight = (
            f"Cab rides tend to carry the highest commute impact. "
            f"Switching one similar trip to {suggested_mode} could save about {savings_kg:.2f} kg CO2e."
        )
    elif mode == "bus":
        insight = (
            "Buses are already a shared option. If this route has a metro leg or a short walk at either end, "
            f"you could trim about {savings_kg:.2f} kg CO2e from a similar trip."
            if suggested_mode and savings_kg > 0
            else "Buses are already a strong lower-carbon choice compared with driving alone."
        )
    elif mode == "metro":
        insight = "Metro travel is already one of the steadier low-carbon commute choices, especially for repeated city trips."
    else:
        insight = "This is a near-zero carbon trip. Repeating choices like this is one of the strongest habits you can build over time."

    return insight, suggested_mode, savings_kg


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.middleware("http")
async def add_security_headers_and_rate_limit(request: Request, call_next):
    client_key = _client_key(request)
    now = time.monotonic()
    request_times = REQUEST_LOG[client_key]

    while request_times and now - request_times[0] > RATE_LIMIT_WINDOW_SECONDS:
        request_times.popleft()

    if request.url.path == "/api/chat" and len(request_times) >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many chat requests. Please wait a moment and try again."},
        )

    request_times.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    return response

@app.get("/")
async def read_index():
    """Serves the main dashboard user interface."""
    if not os.path.exists(STATIC_FILE_PATH):
        raise HTTPException(status_code=404, detail="Frontend index.html was not found.")
    return FileResponse(STATIC_FILE_PATH)

@app.post("/api/chat")
async def handle_coach_chat(payload: ChatPayload):
    """Processes natural language travel inputs or conversational advice requests."""
    # 1. Parse text inputs via Antigravity Agent Engine (or local fallback)
    parsed_metrics = await parse_transit_text(payload.message)
    
    if "error" in parsed_metrics:
        return {
            "reply": "I encountered an issue parsing that request. Could you describe your commute again?",
            "data": None
        }
        
    intent = parsed_metrics.get("intent", "log_transit")
    
    # Mode A: Conversational reply (general questions, greetings)
    if intent == "conversation":
        reply = parsed_metrics.get("conversational_reply")
        if not reply:
            reply = "I'm here to help you optimize your carbon footprint! Tell me about your commute."
        return {
            "reply": reply,
            "data": None  # No trip logged in dashboard
        }
        
    # Mode B: Transit Logging
    mode = parsed_metrics.get("transit_mode")
    duration = parsed_metrics.get("duration_minutes")
    
    if not mode or duration is None:
        return {
            "reply": "I couldn't quite catch your transit details. Could you specify the transport mode (like cab, bus, metro, bicycle, walk) and how long it took in minutes?",
            "data": None
        }
        
    # Compute carbon baseline
    try:
        co2_footprint = calculate_transport_emissions(
            duration_minutes=duration,
            transit_mode=mode
        )
        distance_km = calculate_distance_km(
            duration_minutes=duration,
            transit_mode=mode
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    impact_level = classify_trip_impact(co2_footprint)
    trip_insight, suggested_mode, savings_kg = _build_trip_insight(mode, duration, co2_footprint)

    reply_parts = [
        f"I logged your {duration}-minute {mode} trip at about {co2_footprint:.2f} kg CO2e.",
        f"That works out to roughly {distance_km:.1f} km of travel.",
        trip_insight,
    ]
    reply_msg = "\n\n".join(reply_parts)

    return {
        "reply": reply_msg,
        "data": {
            "mode": mode,
            "duration": duration,
            "carbon_kg": co2_footprint,
            "distance_km": distance_km,
            "impact_level": impact_level,
            "insight": trip_insight,
            "suggested_mode": suggested_mode,
            "potential_savings_kg": savings_kg,
        }
    }

@app.get("/api/health")
def health_check():
    """Automated monitoring route for Google Cloud Run health probes."""
    return {"status": "healthy", "service": "leafline"}
