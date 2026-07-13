import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-specdec")

try:
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
except ValueError:
    TEMPERATURE = 0.0

try:
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
except ValueError:
    MAX_RETRIES = 3

MAX_REWRITES = 1
