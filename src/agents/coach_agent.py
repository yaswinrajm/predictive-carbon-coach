"""Natural language parsing agent for the Predictive Carbon Coach.

Extracts structured transit telemetry from conversational user input to
help individuals track their carbon footprint through simple, natural
language actions. Uses Google Antigravity SDK for AI-powered parsing
with a robust local regex fallback for offline operation.
"""
import re
import sys
import inspect
from pydantic import BaseModel, Field
from src.config import ANTIGRAVITY_API_KEY

class AgentResponse(BaseModel):
    intent: str = Field(
        description="The intent of the user message. Must be 'log_transit' if the user is logging a trip or commute, or 'conversation' if the user is asking a question, making general chat, or seeking carbon reduction advice."
    )
    transit_mode: str | None = Field(
        default=None,
        description="The mode of transportation. Must fall directly into: ['walk', 'bicycle', 'metro', 'bus', 'cab']. Set to null if intent is 'conversation'."
    )
    duration_minutes: int | None = Field(
        default=None,
        description="The duration of the travel journey in minutes. Must be a non-negative integer. Set to null if intent is 'conversation'."
    )
    conversational_reply: str | None = Field(
        default=None,
        description="Write a direct, friendly, and helpful response to the user's message if the intent is 'conversation' (e.g. answer their question or chat with them). Set to null if intent is 'log_transit'."
    )

SYSTEM_INSTRUCTION = """
You are the telemetry extraction and conversational engine for Leafline.
Analyze the user's message:
1. If the user is describing a travel journey or commute (e.g. "I commuted by metro for 30 minutes"), classify intent as 'log_transit', extract the mode and duration, and set conversational_reply to null.
2. If the user is asking a question, greeting you, or requesting advice (e.g. "how do I reduce my footprint"), classify intent as 'conversation', write a helpful conversational response inside conversational_reply, and set transit_mode and duration_minutes to null.
"""

def _parse_transit_text_local(user_input: str) -> dict:
    """Fallback local regex and string parsing logic with intent classification."""
    text = user_input.lower()
    
    is_greeting = any(word in text for word in ["hello", "hi", "hey", "greet", "how are you"])
    is_advice = any(word in text for word in ["reduce", "footprint", "save", "help", "do to", "coaching", "advice", "what should"])
    
    # Check if they specify a transit mode
    mode = None
    if "walk" in text:
        mode = "walk"
    elif "bicycle" in text or "cycle" in text or "bike" in text:
        mode = "bicycle"
    elif "metro" in text or "train" in text or "subway" in text:
        mode = "metro"
    elif "bus" in text or "shuttle" in text:
        mode = "bus"
    elif "cab" in text or "taxi" in text or "uber" in text or "lyft" in text:
        mode = "cab"
        
    # Check if they specify a duration
    numbers = re.findall(r'\d+', text)
    
    # If it's a greeting, asking for footprint advice, or doesn't have mode/numbers, treat as conversation
    if is_greeting or is_advice or not (mode or numbers):
        reply = "I'm here as Leafline. Tell me how you traveled and for how long, like 'I took a 20-minute bus ride', and I can help you log it and spot a simpler lower-carbon swap."
        if is_greeting:
            reply = "Hello! I'm Leafline. Tell me about a commute and I'll help you track it, understand its impact, and find one gentle way to improve it over time."
        elif "reduce" in text or "footprint" in text:
            reply = "The easiest way to reduce your footprint is to start with the trips you repeat most often. Try swapping solo cab rides for metro or bus, walking short trips, or combining errands into one journey."
            
        return {
            "intent": "conversation",
            "transit_mode": None,
            "duration_minutes": None,
            "conversational_reply": reply
        }
    
    # Otherwise, treat as log_transit
    if not mode:
        mode = "bus"  # Fallback mode
    if numbers:
        duration = int(numbers[0])
    else:
        duration = 15  # Fallback duration
        
    return {
        "intent": "log_transit",
        "transit_mode": mode,
        "duration_minutes": duration,
        "conversational_reply": None
    }

async def parse_transit_text(user_input: str) -> dict:
    """Parses raw user string inputs into validated structural metrics via google-antigravity 
    or a local regex fallback if no API key is set or the API call fails.
    """
    is_missing_key = not ANTIGRAVITY_API_KEY or ANTIGRAVITY_API_KEY in [
        "", 
        "your_mock_or_real_dev_key", 
        "YOUR_ANTIGRAVITY_API_KEY",
        "placeholder"
    ]
    
    if is_missing_key:
        return _parse_transit_text_local(user_input)

    # Standard google-antigravity SDK Pathway
    try:
        from google.antigravity import Agent, LocalAgentConfig
    except Exception as e:
        print(f"Warning: SDK import failed ({e}). Falling back to local parser.", file=sys.stderr)
        return _parse_transit_text_local(user_input)

    config = LocalAgentConfig(
        system_instructions=SYSTEM_INSTRUCTION,
        api_key=ANTIGRAVITY_API_KEY,
        response_schema=AgentResponse
    )
    try:
        async with Agent(config) as agent:
            prompt = f"Analyze and parse: '{user_input}'"
            response = await agent.chat(prompt)
            
            try:
                # Try passing schema as parameter as requested by user
                structured_data = response.structured_output(AgentResponse)
                if inspect.iscoroutine(structured_data):
                    structured_data = await structured_data
            except TypeError:
                # Fallback to no-argument call
                structured_data = response.structured_output()
                if inspect.iscoroutine(structured_data):
                    structured_data = await structured_data

            if hasattr(structured_data, "model_dump"):
                return structured_data.model_dump()
            if structured_data and isinstance(structured_data, dict):
                return structured_data
            return _parse_transit_text_local(user_input)
    except Exception as e:
        print(f"Warning: SDK extraction failed ({e}). Falling back to local parser.", file=sys.stderr)
        return _parse_transit_text_local(user_input)
