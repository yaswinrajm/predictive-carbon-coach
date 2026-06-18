# src/config.py
import os
from dotenv import load_dotenv

# Load during local development; automatically overridden or handled by Cloud Run in production
load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "predictive-carbon-coach")
ANTIGRAVITY_API_KEY = os.getenv("ANTIGRAVITY_API_KEY")

# Fail early locally if the environment configuration is completely missing
if not ANTIGRAVITY_API_KEY:
    print("WARNING: ANTIGRAVITY_API_KEY is not set in environment variables. Agent calls will fail.")
    