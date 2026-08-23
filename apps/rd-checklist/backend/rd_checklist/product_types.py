"""Product type classification and labels.

Single source of truth for the backend: which product type a set belongs to
(derived from its set_id) and what it is called in the UI.

**Classification is rule-only.** The set_id decides, and nothing else: no
manual editing (the UI shows the type read-only), no overrides, and the
scraper's own guess is ignored on import. A set_id no rule covers lands in
"other" — which is a fine place to sit until someone adds a rule here.

Two mirrors to keep in sync:

* ``tools/rd-card-scraper/rd_card_scraper/parser.py`` — ``PRODUCT_TYPE_MAP`` /
  ``guess_product_type``. Same rules, so the scraper's JSON agrees with what
  the import computes.
* ``frontend/src/constants/productTypes.ts`` — ``PRODUCT_TYPES``, the display
  side (labels + timeline colours).
"""

from __future__ import annotations

import re

# ── Derivation from set_id ────────────────────────────────────────────────
# Prefix → product type. Only listed where we are confident; anything that
# matches nothing falls through to "other" rather than getting its own
# sidebar entry. Longer prefixes are checked first (SBD before SD).
SET_PREFIX_TO_PRODUCT_TYPE: dict[str, str] = {
    "KP": "booster",
    "AP": "advanced_pack",
    "MAX": "maximum_pack",
    "ORP": "over_rush_pack",
    "LGP": "legend_pack",
    "TB": "triple_build_pack",
    "SBD": "structure_deck",
    "SD": "structure_deck",
    "ST": "structure_deck",
    "GRD": "structure_deck",
    "B0": "battle_pack",
    "B2": "battle_pack",
    # Battle packs ship as a B-half and an S-half (B241/S241); some posts are
    # filed under the S-side set id, e.g. S254 carries the RD/B252 cards.
    "S2": "battle_pack",
    # Promos: convenience-store tie-ins, magazine inserts, gum, starter boosts
    "711": "promo",
    "ECG": "promo",
    "SJMP": "promo",
    "VJMP": "promo",
    "WJMP": "promo",
    "PROMO": "promo",
    "P0": "promo",
    # Game tie-in bonus cards, e.g. G001 (Switch「最強バトルロイヤル!!」特典)
    "G0": "promo",
}

# Jump Festa giveaways: 23PR, 24PR, 25PR, 26PR, … (two digits + PR)
_YEAR_PROMO_RE = re.compile(r"^\d{2}PR$", re.IGNORECASE)

# ── Labels ────────────────────────────────────────────────────────────────
# product type → (English name, Chinese name or None when there isn't a
# meaningful one). The UI renders the Chinese part on its own line.
PRODUCT_TYPE_LABELS: dict[str, tuple[str, str | None]] = {
    "booster":           ("Booster Pack", "補充包"),
    "advanced_pack":     ("Advanced Pack", "上級包"),
    "maximum_pack":      ("Maximum Pack", "巨極包"),
    "over_rush_pack":    ("Over Rush Pack", "超越超速包"),
    "legend_pack":       ("Legend Pack", "傳說包"),
    "triple_build_pack": ("Triple Build Pack", "三重構築包"),
    "structure_deck":    ("Structure Deck", "預組"),
    "battle_pack":       ("Battle Pack", "戰鬥包"),
    "promo":             ("Promo", None),
    "other":             ("Other", None),
}

FALLBACK_PRODUCT_TYPE = "other"


def derive_product_type(set_id: str) -> str | None:
    """Product type implied by the set_id, or None when no rule matches."""
    if _YEAR_PROMO_RE.match(set_id):
        return "promo"
    for prefix in sorted(SET_PREFIX_TO_PRODUCT_TYPE, key=len, reverse=True):
        if set_id.startswith(prefix):
            return SET_PREFIX_TO_PRODUCT_TYPE[prefix]
    return None


def canonical_product_type(set_id: str) -> str:
    """The product type a set belongs to: its set_id rule, or "other"."""
    return derive_product_type(set_id) or FALLBACK_PRODUCT_TYPE


def label_for(product_type: str) -> tuple[str, str | None]:
    """(English, Chinese) label pair; unknown types fall back to their key."""
    return PRODUCT_TYPE_LABELS.get(product_type, (product_type, None))
