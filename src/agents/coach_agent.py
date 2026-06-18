# src/agents/coach_agent.py
import json
from pydantic import BaseModel, Field
from google.antigravity import Agent, LocalAgentConfig
from src.config import ANTIGRAVITY_API_KEY

# Define the structured data schema for the AI to return
class TransitExtraction(BaseModel):
    transit_mode: str = Field(description="Must be exactly one of: walk, bicycle, metro, bus, cab")
    duration_minutes: int = Field(description="The duration of travel extracted as an integer in minutes")

SYSTEM_INSTRUCTION = """
You are the telemetry extraction engine for the Predictive Carbon Coach.
Your sole job is to analyze user transit descriptions, extract the mode and duration, and output a valid JSON structure matching the schema.
If a mode is colloquial or local, map it to the closest match (e.g., 'auto', 'uber', 'taxi', 'car' -> 'cab'; 'shuttle' -> 'bus').
If no transit duration or mode can be deduced, return an error layout.
"""

async def parse_transit_text(user_input: str) -> dict:
    """Parses raw user string inputs into validated structural metrics via Antigravity."""
    config = LocalAgentConfig(
        system_instructions=SYSTEM_INSTRUCTION,
        api_key=ANTIGRAVITY_API_KEY
    )
    
    try:
        async with Agent(config) as agent:
            prompt = f"Extract transit metrics from: '{user_input}'"
            response = await agent.chat(prompt)
            
            # Use Pydantic schema validation built into the SDK response layer
            structured_data = response.structured_output(TransitExtraction)
            return structured_data.model_dump()
    except Exception as e:
        # Graceful fallback to prevent application crashes during evaluations
        return {"error": f"Failed to parse transit criteria safely: {str(e)}"}