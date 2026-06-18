# src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agents.coach_agent import parse_transit_text
from src.services.carbon_math import calculate_transport_emissions

app = FastAPI(title="Predictive Carbon Coach Backend")

# Strict request body validation matching standard production APIs
class ChatPayload(BaseModel):
    message: str

@app.post("/api/chat")
async def handle_coach_chat(payload: ChatPayload):
    """Processes natural language travel inputs, computes carbon outputs, 
    and returns localized reduction recommendations.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message payload cannot be empty.")
        
    # 1. Parse text inputs into structural tokens via Antigravity Agent Engine
    parsed_metrics = await parse_transit_text(payload.message)
    
    if "error" in parsed_metrics:
        return {
            "reply": "I couldn't quite catch your transit details. Could you specify the transport mode (like cab, bus, metro) and how long it took?",
            "data": None
        }
        
    # 2. Compute carbon baseline data using your verified mathematical formulas
    try:
        co2_footprint = calculate_transport_emissions(
            duration_minutes=parsed_metrics["duration_minutes"],
            transit_mode=parsed_metrics["transit_mode"]
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
        
    # 3. Formulate analytical coaching response and proactive routing advice
    mode = parsed_metrics["transit_mode"]
    reply_msg = f"Logged your {parsed_metrics['duration_minutes']}-minute {mode} journey. This generated roughly {co2_footprint} kg of CO2 equivalent."
    
    # Proactive route optimization check (Hybrid Concept 2 feature)
    if mode == "cab":
        reply_msg += " Pro tip: Swapping your next routine cab trip for the campus shuttle or metro cuts your journey footprint by over 80%!"
    elif mode == "bus" or mode == "metro":
        reply_msg += " Great job choosing shared public transit! You are helping bend the emission curve downward."
        
    return {
        "reply": reply_msg,
        "data": {
            "mode": mode,
            "duration": parsed_metrics["duration_minutes"],
            "carbon_kg": co2_footprint
        }
    }

@app.get("/api/health")
def health_check():
    """Automated monitoring route for Google Cloud Run health probes."""
    return {"status": "healthy", "service": "carbon-coach"}