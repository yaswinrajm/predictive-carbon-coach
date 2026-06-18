# src/agents/coach_agent.py
import json
from pydantic import BaseModel, Field
from google.antigravity import Agent, LocalAgentConfig
from src.config import ANTIGRAVITY_API_KEY

class TransitExtraction(BaseModel):
    transit_mode: str = Field(description="Must be exactly one of: walk, bicycle, metro, bus, cab")
    duration_minutes: int = Field(description="The duration of travel extracted as an integer in minutes")

SYSTEM_INSTRUCTION = """
You are the telemetry extraction engine for the Predictive Carbon Coach.
Your sole job is to analyze user transit descriptions, extract the mode and duration, and output a valid JSON structure matching the schema.
"""

async def parse_transit_text(user_input: str) -> dict:
    """Parses raw user string inputs into validated structural metrics via Antigravity."""
    
    # 💡 LOCAL MOCK FALLBACK: Allows flawless end-to-end testing without an API key
    if not ANTIGRAVITY_API_KEY or ANTIGRAVITY_API_KEY == "your_mock_or_real_dev_key":
        text = user_input.lower()
        mode = "bus"  # Default fallback
        if "cab" in text or "auto" in text or "taxi" in text:
            mode = "cab"
        elif "metro" in text or "train" in text:
            mode = "metro"
        elif "walk" in text:
            mode = "walk"
        elif "cycle" in text or "bicycle" in text:
            mode = "bicycle"
            
        # Try to guess a number from common test phrases like "20 minute"
        duration = 20
        for word in text.split():
            if word.isdigit():
                duration = int(word)
                break
                
        return {"transit_mode": mode, "duration_minutes": duration}

    # Standard Live Google Antigravity SDK Pathway
    config = LocalAgentConfig(
        system_instructions=SYSTEM_INSTRUCTION,
        api_key=ANTIGRAVITY_API_KEY
    )
    try:
        async with Agent(config) as agent:
            prompt = f"Extract transit metrics from: '{user_input}'"
            response = await agent.chat(prompt)
            structured_data = response.structured_output(TransitExtraction)
            return structured_data.model_dump()
    except Exception as e:
        return {"error": f"Failed to parse transit criteria safely: {str(e)}"}