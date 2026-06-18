# Predictive Carbon Coach 🌱🧠

An intelligent, context-aware Carbon Footprint Awareness Platform built for PromptWars Virtual Challenge 3. It utilizes the Google Antigravity SDK to dynamically parse conversational transit entries and provide proactive emission-reducing route optimizations.

## 🛠️ Features
- **Conversational Telemetry Extraction:** Driven by a Google Antigravity parsing agent to accurately identify transport modes and journey durations from unstructured chat logs.
- **Automated Footprint Analytics:** High-performance math module calculating real-time CO2 impact using global transit emission baselines.
- **Proactive Route Shifting:** Context-aware prompts urging users to shift from high-emission individual transport modes (like cabs) into shared infrastructure.

## 📁 Repository Blueprint
- `src/main.py`: Asynchronous FastAPI backend web framework.
- `src/agents/coach_agent.py`: Google Antigravity multi-agent intent extraction framework.
- `src/services/carbon_math.py`: Hardcoded math metrics engine for footprint calculation.
- `tests/`: Structural automated suite testing parameters validated via `pytest`.
- `Dockerfile`: Production-ready container assembly layout for seamless Google Cloud Run deployment.

## 🧪 Testing Pass Pattern
Execute the internal automated quality suite locally using:
```bash
set PYTHONPATH=.&& pytest tests/
