"""Product type rules, read from the checklist backend.

The rules are **not** defined here. They live in the checklist's database
(``product_types`` + ``product_type_rules``) and are edited in its UI, so a
rule change applies to everything at once — the app's own classification and
what the scraper stamps into its JSON.

Lookup order, each step falling through on failure:

1. ``GET {RD_CHECKLIST_API}/api/product-types`` (default http://localhost:8000)
2. ``{data_dir}/product_types.json`` — the last answer we got
3. nothing, so every set is ``other``

Matching mirrors the backend: ``re.search`` against the set_id, case
insensitive, first rule wins, types in their stored order.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

API_BASE = os.getenv("RD_CHECKLIST_API", "http://localhost:8000")
CACHE_FILE = "product_types.json"
FALLBACK_CODE = "other"
_TIMEOUT = 3

# [(code, [compiled patterns])] — loaded once per process.
_rules: list[tuple[str, list[re.Pattern[str]]]] | None = None
_fallback = FALLBACK_CODE


def _compile(payload: list[dict]) -> tuple[list[tuple[str, list[re.Pattern[str]]]], str]:
    rules: list[tuple[str, list[re.Pattern[str]]]] = []
    fallback = FALLBACK_CODE
    for entry in sorted(payload, key=lambda e: e.get("sort_order", 0)):
        if entry.get("is_fallback"):
            fallback = entry.get("code", FALLBACK_CODE)
            continue
        patterns = []
        for pattern in entry.get("rules", []):
            try:
                patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                logger.warning("Skipping invalid product type rule: %r", pattern)
        if patterns:
            rules.append((entry.get("code", ""), patterns))
    return rules, fallback


def _fetch_from_api() -> list[dict] | None:
    try:
        response = requests.get(f"{API_BASE}/api/product-types", timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list) and payload:
            return payload
    except Exception as exc:  # network error, backend down, bad JSON
        logger.info("Could not read product type rules from %s: %s", API_BASE, exc)
    return None


def load_rules(data_dir: Path | None = None, refresh: bool = True) -> None:
    """Load the rules into this process (API first, then the cached copy)."""
    global _rules, _fallback

    cache_path = Path(data_dir) / CACHE_FILE if data_dir else None

    payload = _fetch_from_api() if refresh else None
    if payload is not None and cache_path is not None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("Could not cache product type rules: %s", exc)

    if payload is None and cache_path is not None and cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info("Using cached product type rules from %s", cache_path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read cached product type rules: %s", exc)

    if payload is None:
        logger.warning(
            "No product type rules available — every set will be %r. "
            "Start the checklist backend (or set RD_CHECKLIST_API) to pick them up.",
            FALLBACK_CODE,
        )
        _rules, _fallback = [], FALLBACK_CODE
        return

    _rules, _fallback = _compile(payload)


def guess_product_type(set_id: str, data_dir: Path | None = None) -> str:
    """The product type for a set_id, per the checklist's rules."""
    if _rules is None:
        load_rules(data_dir)
    for code, patterns in _rules or []:
        if any(pattern.search(set_id or "") for pattern in patterns):
            return code
    return _fallback
