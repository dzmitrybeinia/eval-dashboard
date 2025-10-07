import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Languages
LANGUAGES = [
    "english", "spanish", "polish", "french", "russian",
    "german", "portuguese", "japanese", "serbian", "arabic", "hebrew"
]

# Azure Configuration
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
AZURE_ENDPOINT = ENDPOINT_URL  # Alias for backward compatibility
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_KEY = API_KEY  # Alias for backward compatibility
API_VERSION = os.getenv("API_VERSION", "2025-01-01-preview")
AZURE_API_VERSION = API_VERSION  # Alias for backward compatibility
DEPLOYMENT_NAME = "gpt-4.1"
AZURE_DEPLOYMENT = DEPLOYMENT_NAME  # Alias for backward compatibility

# Paths
RAW_JSON_DIR = Path("raw_json_files")
MARKDOWN_DIR = Path("markdown_files")
EVAL_RESULTS_DIR = Path("eval_results")
ISSUES_DIR = Path("issues")
PROMPTS_DIR = Path("prompts")
