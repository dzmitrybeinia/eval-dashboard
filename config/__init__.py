"""Configuration modules."""
from pathlib import Path

from .azure import API_KEY, API_VERSION, DEPLOYMENT_NAME, ENDPOINT_URL
from .languages import SUPPORTED_LANGUAGES as LANGUAGES
from .paths import DEFAULT_EVAL_RESULTS_DIR, DEFAULT_MARKDOWN_DIR, DEFAULT_RAW_JSON_DIR

# Backward compatibility alias
SUPPORTED_LANGUAGES = LANGUAGES

# Path aliases for unified config interface
EVAL_RESULTS_DIR = Path("eval_results")
MARKDOWN_DIR = Path("markdown_files")
RAW_JSON_DIR = Path("raw_json_files")
ISSUES_DIR = Path("issues")
PROMPTS_DIR = Path("prompts")
