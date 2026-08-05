"""Rarity normalization for scraped card data.

Some rarities appear on the blog under several equivalent spellings
(letter-order variants). They all denote the same rarity and are collapsed to a
single canonical code so downstream (DB / frontend) only ever sees:

    SPR ← SPR, SRP, PSR   (亮鑽)
    NPR ← NPR, NRP, PNR   (普鑽)
    UPR ← UPR, URP, PUR   (金亮鑽)

Every other rarity code is left untouched.
"""

from __future__ import annotations

# synonym (upper-cased) → canonical
_RARITY_SYNONYMS: dict[str, str] = {
    "SPR": "SPR", "SRP": "SPR", "PSR": "SPR",
    "NPR": "NPR", "NRP": "NPR", "PNR": "NPR",
    "UPR": "UPR", "URP": "UPR", "PUR": "UPR",
}


def normalize_rarity(rarity: str) -> str:
    """Map a single rarity token to its canonical spelling."""
    token = rarity.strip()
    return _RARITY_SYNONYMS.get(token.upper(), token)


def normalize_rarity_string(rarity_string: str) -> str:
    """Normalize a possibly-compound rarity string (e.g. "SR/PUR" → "SR/UPR").

    Each ``/``-separated token is canonicalized; duplicates that collapse to the
    same canonical code are removed while preserving first-seen order.
    """
    seen: set[str] = set()
    out: list[str] = []
    for raw in rarity_string.split("/"):
        token = normalize_rarity(raw)
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return "/".join(out)
