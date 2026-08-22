"""Compare a set in the DB against its published card list on yugipedia.

The unit of comparison is a *printing* — (card_id, rarity, alternate artwork) —
because that is what the checklist tracks: the same card at two rarities is two
things to collect, and an alternate artwork is a third.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import CardModel, CardVariantModel
from ..rarities import rarity_rank
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

    remap = _pair_into_remaps(missing, extra)

    missing.sort(key=lambda m: (m["card_id"], m["rarity"], m["is_alternate_art"]))
    extra.sort(key=lambda e: (e["card_id"], e["rarity"], e["is_alternate_art"]))
    remap.sort(key=lambda r: (r["card_id"], r["from_rarity"], r["to_rarity"]))

    logger.info(
        "%s vs %s: %d missing, %d extra, %d remap",
        set_id, result.list_page, len(missing), len(extra), len(remap),
    )
    return {
        "list_page": result.list_page,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": missing,
        "extra": extra,
        "remap": remap,
        "unknown_rarities": result.unknown_rarities,
    }


def _pair_into_remaps(missing: list[dict], extra: list[dict]) -> list[dict]:
    """Turn "we have X, the list says Y" into a rarity correction.

    A card the scraper read at the wrong rarity shows up as both a missing and
    an extra printing. Deleting and recreating would work, but the variant row
    carries the owned count and the uploaded image — renaming it keeps both, so
    pairs are proposed as remaps and removed from the two lists.

    Pairing is by card and artwork flag, least-rare first on each side, so the
    result does not depend on dict ordering. Anything left over stays a plain
    create or delete.
    """
    remaps: list[dict] = []

    def pair(match_artwork: bool) -> None:
        """Pair what is left, card by card. With match_artwork the two sides
        must agree on the artwork flag; without it, a normal printing can be
        corrected into an alternate one (or back)."""
        cards = {m["card_id"] for m in missing} & {e["card_id"] for e in extra}
        for card_id in sorted(cards):
            for is_alt in ((False, True) if match_artwork else (None,)):
                want = sorted(
                    (
                        m for m in missing
                        if m["card_id"] == card_id
                        and (is_alt is None or m["is_alternate_art"] == is_alt)
                    ),
                    key=lambda m: rarity_rank(m["rarity"]),
                )
                have = sorted(
                    (
                        e for e in extra
                        if e["card_id"] == card_id
                        and (is_alt is None or e["is_alternate_art"] == is_alt)
                    ),
                    key=lambda e: rarity_rank(e["rarity"]),
                )
                for target, source in zip(want, have):
                    remaps.append(
                        {
                            "card_id": card_id,
                            "from_rarity": source["rarity"],
                            "to_rarity": target["rarity"],
                            "from_is_alternate_art": source["is_alternate_art"],
                            "to_is_alternate_art": target["is_alternate_art"],
                            "name_jp": source["name_jp"] or target["name_jp"],
                            "name_zh": source["name_zh"],
                            "owned_count": source["owned_count"],
                        }
                    )
                    missing.remove(target)
                    extra.remove(source)

    # Same artwork flag first — those are plain rarity corrections. Only then
    # pair across the flag, which is the "we filed the alternate artwork as a
    # normal printing" case.
    pair(match_artwork=True)
    pair(match_artwork=False)

    return remaps
