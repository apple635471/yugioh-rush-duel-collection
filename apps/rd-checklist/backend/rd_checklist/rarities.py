"""Rarity normalization.

Some rarities appear on the blog / Konami data under several equivalent
spellings (letter-order variants). They all denote the same rarity and must be
collapsed to a single canonical code:

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


# Least rare first. Mirrors RARITIES in the frontend's constants/rarities.ts
# — used to pair up rarities deterministically, not for display.
RARITY_ORDER: tuple[str, ...] = (
    "N", "NPR", "R", "SR", "SPR", "UR", "UPR", "RUR",
    "SER", "RR", "GRR", "ORR", "ORRPBV", "FORR",
)


def rarity_rank(rarity: str) -> int:
    """Position in RARITY_ORDER; unknown rarities sort last."""
    try:
        return RARITY_ORDER.index(rarity)
    except ValueError:
        return len(RARITY_ORDER)


def normalize_rarity(rarity: str) -> str:
    """Map a single rarity token to its canonical spelling.

    Unknown / non-synonym codes are returned trimmed but otherwise unchanged.
    """
    token = rarity.strip()
    return _RARITY_SYNONYMS.get(token.upper(), token)


def normalize_rarity_string(rarity_string: str) -> str:
    """Normalize a possibly-compound rarity string (e.g. "N/PUR").

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
