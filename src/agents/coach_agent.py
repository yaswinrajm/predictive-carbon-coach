"""Natural language parsing agent for the Predictive Carbon Coach.

Extracts structured transit telemetry from conversational user input to
help individuals track their carbon footprint through simple, natural
language actions. Uses Google Antigravity SDK for AI-powered parsing
with a robust local regex fallback for offline operation.
"""
import re
import sys
import inspect
from typing import Any, Dict, Optional, cast
from pydantic import BaseModel, Field

from src.config import ANTIGRAVITY_API_KEY

# Compile regex and store constants globally for efficiency (O(1) memory lookup vs repeatedly declaring sets)
DURATION_REGEX = re.compile(r'\d+')

GREETING_KEYWORDS = ("hello", "hi", "hey", "greet", "how are you")
ADVICE_KEYWORDS = ("reduce", "footprint", "save", "help", "do to", "coaching", "advice", "what should")

MODE_MAPPING = {
    "walk": "walk",
    "bicycle": "bicycle", "cycle": "bicycle", "bike": "bicycle",
    "metro": "metro", "train": "metro", "subway": "metro",
    "bus": "bus", "shuttle": "bus",
    "cab": "cab", "taxi": "cab", "uber": "cab", "lyft": "cab"
}

class AgentResponse(BaseModel):
    intent: str = Field(
        description="The intent of the user message. Must be 'log_transit' if the user is logging a trip or commute, or 'conversation' if the user is asking a question, making general chat, or seeking carbon reduction advice."
    )
    transit_mode: Optional[str] = Field(
        default=None,
        description="The mode of transportation. Must fall directly into: ['walk', 'bicycle', 'metro', 'bus', 'cab']. Set to null if intent is 'conversation'."
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="The duration of the travel journey in minutes. Must be a non-negative integer. Set to null if intent is 'conversation'."
    )
    conversational_reply: Optional[str] = Field(
        default=None,
        description="Write a direct, friendly, and helpful response to the user's message if the intent is 'conversation' (e.g. answer their question or chat with them). Set to null if intent is 'log_transit'."
    )

SYSTEM_INSTRUCTION = """
You are the telemetry extraction and conversational engine for Leafline.
Analyze the user's message:
1. If the user is describing a travel journey or commute (e.g. "I commuted by metro for 30 minutes"), classify intent as 'log_transit', extract the mode and duration, and set conversational_reply to null.
2. If the user is asking a question, greeting you, or requesting advice (e.g. "how do I reduce my footprint"), classify intent as 'conversation', write a helpful conversational response inside conversational_reply, and set transit_mode and duration_minutes to null.
"""

def _parse_transit_text_local(user_input: str) -> Dict[str, Any]:
    """Fallback local string parsing logic with intent classification. O(N) efficient string checks."""
    text = user_input.lower()
    
    is_greeting = any(word in text for word in GREETING_KEYWORDS)
    is_advice = any(word in text for word in ADVICE_KEYWORDS)
    
    # O(N) mapping lookup vs repeated large if-else blocks
    mode = next((val for key, val in MODE_MAPPING.items() if key in text), None)
    
    numbers = DURATION_REGEX.findall(text)
    
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
    
    duration = int(numbers[0]) if numbers else 15
    return {
        "intent": "log_transit",
        "transit_mode": mode or "bus",
        "duration_minutes": duration,
        "conversational_reply": None
    }

async def parse_transit_text(user_input: str) -> Dict[str, Any]:
    """Parses raw user string inputs into validated structural metrics."""
    if not ANTIGRAVITY_API_KEY or ANTIGRAVITY_API_KEY in {"", "your_mock_or_real_dev_key", "YOUR_ANTIGRAVITY_API_KEY", "placeholder"}:
        return _parse_transit_text_local(user_input)

    try:
        from google.antigravity import Agent, LocalAgentConfig
    except ImportError as e:
        print(f"Warning: SDK import failed ({e}). Falling back to local parser.", file=sys.stderr)
        return _parse_transit_text_local(user_input)

    config = LocalAgentConfig(
        system_instructions=SYSTEM_INSTRUCTION,
        api_key=ANTIGRAVITY_API_KEY,
        response_schema=AgentResponse
    )
    try:
        async with Agent(config) as agent:
            response = await agent.chat(f"Analyze and parse: '{user_input}'")
            try:
                structured_data = response.structured_output(AgentResponse)
                if inspect.iscoroutine(structured_data):
                    structured_data = await structured_data
            except TypeError:
                structured_data = response.structured_output()
                if inspect.iscoroutine(structured_data):
                    structured_data = await structured_data

            if hasattr(structured_data, "model_dump"):
                return cast(Dict[str, Any], structured_data.model_dump())
            if isinstance(structured_data, dict):
                return structured_data
            return _parse_transit_text_local(user_input)
    except Exception as e:
        print(f"Warning: SDK extraction failed ({e}). Falling back to local parser.", file=sys.stderr)
        return _parse_transit_text_local(user_input)
