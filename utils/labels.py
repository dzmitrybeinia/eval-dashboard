"""Helpers for working with evaluation labels safely."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class LabelInfo:
    """Normalized representation of a label value."""

    original: str  # User-provided label
    key: str  # Filesystem-safe version


def sanitize_label(label: str) -> str:
    """Return a filesystem-safe label identifier."""
    sanitized = _SANITIZE_PATTERN.sub("_", label.strip())
    sanitized = sanitized.strip("_")
    return sanitized or "default"


def normalize_label(label: str) -> LabelInfo:
    """Normalize user-supplied labels for consistent downstream usage."""
    original = label.strip()
    if not original:
        raise ValueError("Label cannot be empty.")

    key = sanitize_label(original.lower())
    return LabelInfo(original=original, key=key)


def ensure_label(label: LabelInfo | str) -> LabelInfo:
    """Return normalized label info regardless of input type."""
    if isinstance(label, LabelInfo):
        return label
    return normalize_label(label)
