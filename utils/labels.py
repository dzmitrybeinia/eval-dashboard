import re

_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")

def sanitize_label(label: str) -> str:
    if not label.strip():
        raise ValueError("Label cannot be empty.")
    sanitized = _SANITIZE_PATTERN.sub("_", label.strip().lower())
    sanitized = sanitized.strip("_")
    return sanitized or "default"
