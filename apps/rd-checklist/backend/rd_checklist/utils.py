"""Shared utilities for the Checklist API."""

from __future__ import annotations

# Suffix appended to a rarity value to form the URL-safe "rarity key" for
# alternate-art variants.  e.g. "SR" → "SR-alt"
_ALT_SUFFIX = "-alt"


def parse_rarity_key(key: str) -> tuple[str, bool]:
    """Parse a URL rarity key into (rarity, is_alternate_art).

    "SR"     → ("SR", False)
    "SR-alt" → ("SR", True)
    """
    if key.endswith(_ALT_SUFFIX):
        return key[: -len(_ALT_SUFFIX)], True
    return key, False


def make_rarity_key(rarity: str, is_alternate_art: bool) -> str:
    """Build a URL rarity key from a rarity value and alternate-art flag.

    ("SR", False) → "SR"
    ("SR", True)  → "SR-alt"
    """
    return f"{rarity}{_ALT_SUFFIX}" if is_alternate_art else rarity
