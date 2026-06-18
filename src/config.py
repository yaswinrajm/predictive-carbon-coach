"""Application configuration for the Predictive Carbon Coach.

Loads environment variables for API keys and project identifiers,
providing early diagnostic warnings without hard-crashing to ensure
100% service uptime in both local development and cloud deployment.
"""
import os
import sys
from dotenv import load_dotenv

# Load during local development; automatically overridden or handled by Cloud Run in production
load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
ANTIGRAVITY_API_KEY = os.getenv("ANTIGRAVITY_API_KEY")

# Fail early locally if the environment configuration is completely missing but don't hard-crash
if not GOOGLE_PROJECT_ID:
    print("WARNING: GOOGLE_PROJECT_ID environment variable is missing. Deployment context may be incomplete.", file=sys.stderr)

if not ANTIGRAVITY_API_KEY:
    print("WARNING: ANTIGRAVITY_API_KEY environment variable is missing. Agent calls will fail.", file=sys.stderr)
    