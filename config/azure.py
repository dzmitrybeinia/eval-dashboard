"""Azure OpenAI configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

ENDPOINT_URL = os.getenv("ENDPOINT_URL")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_VERSION = os.getenv("API_VERSION", "2025-01-01-preview")
DEPLOYMENT_NAME = "gpt-4.1"
