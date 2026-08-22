"""Product type classification and labels.

Single source of truth for the backend: which product type a set belongs to
(derived from its set_id), what it is called in the UI, and how retired types
map onto current ones.

The scraper has a mirror of the derivation rules in
``tools/rd-card-scraper/rd_card_scraper/parser.py`` (``PRODUCT_TYPE_MAP`` /
``guess_product_type``). Keep the two in sync — the scraper stamps a
product_type into its JSON, and the import re-derives it here anyway, so this
module is what actually decides.
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
}

# Jump Festa giveaways: 23PR, 24PR, 25PR, 26PR, … (two digits + PR)
_YEAR_PROMO_RE = re.compile(r"^\d{2}PR$", re.IGNORECASE)

# Retired product types → what they are now. Sets that used to get their own
# sidebar entry for a single release are folded into "other"; the old
# tournament_pack was simply a wrong name for the Triple Build Pack.
LEGACY_PRODUCT_TYPE_ALIASES: dict[str, str] = {
    "unknown": "other",
    "character_pack": "other",
    "go_rush_character": "other",
    "extra_pack": "other",
    "vs_pack": "other",
    "tournament_pack": "triple_build_pack",
}

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


def canonical_product_type(set_id: str, scraper_value: str | None = None) -> str:
    """Resolve a set to a current product type.

    A set_id rule wins when there is one — those are the cases we are sure
    about. Otherwise the scraper's own value is used, with retired types
    mapped forward; anything unrecognised becomes "other".
    """
    derived = derive_product_type(set_id)
    if derived:
        return derived

    value = LEGACY_PRODUCT_TYPE_ALIASES.get(scraper_value or "", scraper_value)
    if value in PRODUCT_TYPE_LABELS:
        return value
    return FALLBACK_PRODUCT_TYPE


def label_for(product_type: str) -> tuple[str, str | None]:
    """(English, Chinese) label pair; unknown types fall back to their key."""
    return PRODUCT_TYPE_LABELS.get(product_type, (product_type, None))
