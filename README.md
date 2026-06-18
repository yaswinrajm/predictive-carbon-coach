# Leafline — The Predictive Carbon Coach

Leafline is a lightweight, AI-powered carbon coaching application that helps individuals **understand**, **track**, and **reduce** their carbon footprint through **simple actions** and **personalized insights**.

## The Problem

Traditional carbon calculators force users to fill out long forms and look up utility bills. This friction causes immediate drop-off. People need a zero-friction, conversational tool that fits into their daily routine.

## Our Solution

Leafline replaces complex forms with natural conversation. A user simply describes their commute — "I took a 20-minute cab to the station" — and the system instantly parses, calculates, and coaches.

### Understand

Every trip is translated into plain-language context: kilograms of CO₂, equivalent tree-absorption days, and weekly pattern analysis. Users see their top emission source and how their mode mix compares over time.

### Track

Trips are logged persistently with weekly snapshots, cumulative totals, and a personal carbon budget goal. The dashboard visualizes progress with a goal tracker, greener-share percentage, and full journey history.

### Reduce

Leafline proactively suggests realistic lower-carbon swaps based on each user's actual travel patterns. It identifies the single biggest reduction opportunity each week and coaches users toward repeatable, sustainable habits — not one-off perfect days.

## Personalized Insights

- **Weekly Goal Tracking**: Set a personal weekly carbon budget and see real-time progress
- **Best Next Action**: Leafline identifies the single repeated trip creating the most emissions and suggests what to try instead
- **Contextual Coaching**: Advice adapts based on whether the user favors greener modes or relies heavily on solo car trips
- **Impact Levels**: Each trip is classified into soft impact bands (low, light, moderate, high) for quick understanding

## Simple Actions

- Log trips by texting naturally: "rode the bus for 30 minutes"
- Tap suggestion chips for one-click logging
- Set and adjust a weekly carbon goal with a single input
- Clear history and start fresh with one button

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Semantic HTML5, CSS3, Vanilla JavaScript |
| AI Parsing | Google Antigravity SDK with local regex fallback |
| Deployment | Docker, Google Cloud Run |
| Testing | pytest, httpx, FastAPI TestClient |

## Project Structure

```
src/
├── main.py                  # FastAPI app, routing, security middleware, rate limiting
├── config.py                # Environment configuration with safety diagnostics
├── agents/
│   └── coach_agent.py       # NLP parsing via Antigravity SDK + local fallback
├── services/
│   └── carbon_math.py       # Emissions engine, distance, impact, swap recommendations
└── static/
    └── index.html           # Accessible responsive dashboard UI
tests/
├── test_carbon_math.py      # Unit tests for emissions calculations
├── test_coach_agent.py      # Unit tests for NLP parsing logic
└── test_api.py              # Integration tests for API endpoints
```

## Local Setup

1. Create and activate a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your environment variables
4. Run the app:

```powershell
uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Testing

```powershell
python -m pytest tests/ -v
```

## Security

- Input validation with Pydantic field validators and length limits
- Rate limiting on chat endpoints (30 requests/minute per client)
- Security headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- Non-root Docker container execution
- Environment variables for sensitive configuration (never committed)

## Accessibility

- WCAG 2.1 AA compliant color contrast ratios
- Skip navigation link for keyboard users
- Proper ARIA landmarks, roles, and live regions
- Semantic HTML5 structure with correct heading hierarchy
- Visible focus indicators on all interactive elements
- Screen reader announcements for dynamic content updates
