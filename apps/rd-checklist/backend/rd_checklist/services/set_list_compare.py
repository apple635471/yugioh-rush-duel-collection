"""Compare a set in the DB against its published card list on yugipedia.

The unit of comparison is a *printing* — (card_id, rarity, alternate artwork) —
because that is what the checklist tracks: the same card at two rarities is two
things to collect, and an alternate artwork is a third.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import CardModel, CardVariantModel
from .yugipedia import ExpectedVariant, fetch_set_list

logger = logging.getLogger(__name__)

Key = tuple[str, str, bool]


def _key(card_id: str, rarity: str, is_alt: bool) -> Key:
    return (card_id, rarity, is_alt)


def compare_with_yugipedia(db: Session, set_id: str, url: str) -> dict:
    """What the list has that we don't, and what we have that it doesn't."""
    result = fetch_set_list(url)

    expected: dict[Key, ExpectedVariant] = {}
    for v in result.variants:
        expected.setdefault(_key(v.card_id, v.rarity, v.is_alternate_art), v)

    rows = (
        db.query(CardVariantModel, CardModel)
        .join(CardModel, CardModel.card_id == CardVariantModel.card_id)
        .filter(CardModel.set_id == set_id)
        .all()
    )
    actual: dict[Key, tuple[CardVariantModel, CardModel]] = {
        _key(v.card_id, v.rarity, bool(v.is_alternate_art)): (v, c) for v, c in rows
    }

    missing = [
        {
            "card_id": v.card_id,
            "rarity": v.rarity,
            "is_alternate_art": v.is_alternate_art,
            "name_en": v.name_en,
            "name_jp": v.name_jp,
            # A card we hold at another rarity only needs the extra printing.
            "card_exists": db.query(CardModel).filter_by(card_id=v.card_id).first() is not None,
        }
        for key, v in expected.items()
        if key not in actual
    ]

    extra = [
        {
            "card_id": variant.card_id,
            "rarity": variant.rarity,
            "is_alternate_art": bool(variant.is_alternate_art),
            "name_jp": card.name_jp,
            "name_zh": card.name_zh,
            "owned_count": variant.owned_count,
            # Deleting the last printing means deleting the card itself.
            "is_only_variant": db.query(CardVariantModel)
            .filter_by(card_id=variant.card_id)
            .count()
            <= 1,
        }
        for key, (variant, card) in actual.items()
        if key not in expected
    ]

    missing.sort(key=lambda m: (m["card_id"], m["rarity"], m["is_alternate_art"]))
    extra.sort(key=lambda e: (e["card_id"], e["rarity"], e["is_alternate_art"]))

    logger.info(
        "%s vs %s: %d missing, %d extra",
        set_id, result.list_page, len(missing), len(extra),
    )
    return {
        "list_page": result.list_page,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": missing,
        "extra": extra,
        "unknown_rarities": result.unknown_rarities,
    }
