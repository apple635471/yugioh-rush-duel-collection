"""Monster race (種族) normalization.

The blog spells a few races inconsistently, and occasionally drops the 族
suffix. Normalizing keeps one race from showing up as several entries in the
種族 filter.

Mirrors rd_card_scraper/monster_types.py in the scraper — keep the two maps in
sync. Applied again on import so older scraper JSON heals itself without a
re-scrape, and by the normalize-monster-types CLI for rows already in the DB.
"""

from __future__ import annotations

MONSTER_TYPE_ALIASES: dict[str, str] = {
    # Three transliterations of the same race
    "歐米茄超能族": "omega 超能族",
    "奧米茄超能族": "omega 超能族",
    "奧米加超能族": "omega 超能族",
    # Missing or wrong 族 suffix
    "炎": "炎族",
    "爬蟲族": "爬蟲類族",
    "魔法族": "魔法使族",
}


def normalize_monster_type(value: str | None) -> str | None:
    """Canonical race name; unknown values pass through unchanged."""
    if not value:
        return value
    stripped = value.strip()
    return MONSTER_TYPE_ALIASES.get(stripped, stripped)
