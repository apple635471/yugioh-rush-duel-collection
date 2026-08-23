"""Timeline view data for the set list page.

One request instead of a per-set fan-out: the timeline needs each set's
ownership progress, its rarity distribution and a few of its rarest card
images, and doing that one set at a time would be ~4 requests × 90 sets.

Sets without a release date are left out — they have no place on a time axis.
"""

from __future__ import annotations

from sqlalchemy import case as sa_case, func
from sqlalchemy.orm import Session

from ..models import (
    CardModel,
    CardSetImageModel,
    CardSetModel,
    CardVariantModel,
)
from ..rarities import RARITY_ORDER, rarity_rank

def _rank(rarity: str) -> int:
    """Like rarity_rank, but unknown codes sort as *least* rare, not rarest."""
    rank = rarity_rank(rarity)
    return -1 if rank >= len(RARITY_ORDER) else rank


def _date_key(release_date: str | None) -> tuple[int, int, int]:
    """Sortable key from a "YYYY/M/D" string; unparsable parts count as 0."""
    parts = (release_date or "").split("/")[:3]
    nums = []
    for part in parts:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    nums += [0] * (3 - len(nums))
    return nums[0], nums[1], nums[2]


def build_timeline(
    db: Session,
    product_type: str | None = None,
    top_cards: int = 4,
) -> list[dict]:
    """Newest first. Each entry is one box on the timeline."""
    q = db.query(CardSetModel).filter(
        CardSetModel.release_date.isnot(None),
        CardSetModel.release_date != "",
    )
    if product_type:
        q = q.filter(CardSetModel.product_type == product_type)
    sets = q.all()
    if not sets:
        return []

    # Stable two-pass sort: set_id ascending within the same release date.
    sets.sort(key=lambda s: s.set_id)
    sets.sort(key=lambda s: _date_key(s.release_date), reverse=True)

    set_ids = [s.set_id for s in sets]
    rarities = _rarity_counts(db, set_ids)
    picks = _top_cards(db, set_ids, top_cards)
    images = _first_images(db, set_ids)

    out = []
    for s in sets:
        dist = rarities.get(s.set_id, [])
        out.append(
            {
                "set_id": s.set_id,
                "set_name_jp": s.set_name_jp,
                "set_name_zh": s.set_name_zh,
                "product_type": s.product_type,
                "release_date": s.release_date,
                "total_cards": s.total_cards,
                "total_variants": sum(d["count"] for d in dist),
                "owned_variants": sum(d["owned"] for d in dist),
                "rarity_distribution": dist,
                "top_cards": picks.get(s.set_id, []),
                "image_id": images.get(s.set_id),
            }
        )
    return out


def _rarity_counts(db: Session, set_ids: list[str]) -> dict[str, list[dict]]:
    """Per set: [{rarity, count, owned}], rarest first."""
    rows = (
        db.query(
            CardModel.set_id,
            CardVariantModel.rarity,
            func.count(CardVariantModel.id).label("total"),
            func.sum(sa_case((CardVariantModel.owned_count > 0, 1), else_=0)).label("owned"),
        )
        .join(CardVariantModel, CardVariantModel.card_id == CardModel.card_id)
        .filter(CardModel.set_id.in_(set_ids))
        .group_by(CardModel.set_id, CardVariantModel.rarity)
        .all()
    )
    out: dict[str, list[dict]] = {}
    for row in rows:
        out.setdefault(row.set_id, []).append(
            {"rarity": row.rarity, "count": row.total, "owned": int(row.owned or 0)}
        )
    for entries in out.values():
        entries.sort(key=lambda e: (-_rank(e["rarity"]), e["rarity"]))
    return out


def _top_cards(db: Session, set_ids: list[str], limit: int) -> dict[str, list[dict]]:
    """Per set: the `limit` rarest cards that actually have an image.

    One card contributes once — its rarest printing — so a card printed in
    N/SR/SER does not eat three slots.
    """
    if limit <= 0:
        return {}
    rows = (
        db.query(
            CardModel.set_id,
            CardModel.card_id,
            CardModel.name_zh,
            CardModel.name_jp,
            CardVariantModel.rarity,
            CardVariantModel.is_alternate_art,
        )
        .join(CardVariantModel, CardVariantModel.card_id == CardModel.card_id)
        .filter(CardModel.set_id.in_(set_ids))
        .filter(CardVariantModel.image_path.isnot(None), CardVariantModel.image_path != "")
        .all()
    )

    # card_id → best printing so far
    best: dict[str, dict] = {}
    for row in rows:
        entry = {
            "set_id": row.set_id,
            "card_id": row.card_id,
            "name_zh": row.name_zh,
            "name_jp": row.name_jp,
            "rarity": row.rarity,
            "is_alternate_art": bool(row.is_alternate_art),
        }
        current = best.get(row.card_id)
        if current is None or _printing_key(entry) > _printing_key(current):
            best[row.card_id] = entry

    by_set: dict[str, list[dict]] = {}
    for entry in best.values():
        by_set.setdefault(entry["set_id"], []).append(entry)
    for set_id, entries in by_set.items():
        entries.sort(key=lambda e: (-_rank(e["rarity"]), e["card_id"]))
        by_set[set_id] = [
            {k: v for k, v in e.items() if k != "set_id"} for e in entries[:limit]
        ]
    return by_set


def _printing_key(entry: dict) -> tuple[int, int]:
    """Rarer wins; at the same rarity the normal artwork wins over the alt."""
    return _rank(entry["rarity"]), 0 if entry["is_alternate_art"] else 1


def _first_images(db: Session, set_ids: list[str]) -> dict[str, int]:
    """Per set: the id of its first gallery image (the pack shot), if any."""
    rows = (
        db.query(CardSetImageModel.set_id, CardSetImageModel.id)
        .filter(CardSetImageModel.set_id.in_(set_ids))
        .order_by(
            CardSetImageModel.set_id,
            CardSetImageModel.sort_order,
            CardSetImageModel.id,
        )
        .all()
    )
    out: dict[str, int] = {}
    for set_id, image_id in rows:
        out.setdefault(set_id, image_id)
    return out
