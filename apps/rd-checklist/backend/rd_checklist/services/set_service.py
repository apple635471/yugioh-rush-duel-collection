"""Card set maintenance operations that don't belong to the import flow."""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from ..models import (
    CardEditModel,
    CardModel,
    CardOverrideModel,
    CardSetModel,
    CardSetOverrideModel,
    CardVariantModel,
    CardVariantOverrideModel,
)

logger = logging.getLogger(__name__)

# "RD/B252-JP001" → "B252". Mirrors SET_ID_RE in the scraper's parser.py.
_SET_CODE_RE = re.compile(r"RD/(\w+)-JP")

# Battle packs ship as a B-half and an S-half sharing one number (B251/S251);
# both live under the B id. Mirrors _split_group_id() in the scraper.
_BATTLE_PACK_S_HALF_RE = re.compile(r"^S(\d{3})$")


def set_id_from_card_id(card_id: str) -> str | None:
    """Set a card belongs to, judged by its own card number."""
    m = _SET_CODE_RE.search(card_id)
    if not m:
        return None
    code = m.group(1)
    half = _BATTLE_PACK_S_HALF_RE.match(code)
    return f"B{half.group(1)}" if half else code


def resplit_set(db: Session, set_id: str, delete_when_empty: bool = True) -> dict:
    """Move a set's cards to the sets their own card numbers point at.

    For posts that used to be scraped as one set and are now split into
    several (see MULTI_DECK_URLS in the scraper). Cards are moved rather than
    re-imported so that everything keyed by card_id — overrides, edits,
    uploaded images, owned_count — comes along untouched.

    Target sets must already exist; import the new scraper data first.
    """
    card_set = db.get(CardSetModel, set_id)
    if card_set is None:
        raise LookupError(f"Card set not found: {set_id}")

    moved: list[tuple[str, str]] = []
    missing_targets: dict[str, int] = {}
    stayed = 0

    for card in db.query(CardModel).filter(CardModel.set_id == set_id).all():
        target = set_id_from_card_id(card.card_id)
        if target is None or target == set_id:
            stayed += 1
            continue
        if db.get(CardSetModel, target) is None:
            missing_targets[target] = missing_targets.get(target, 0) + 1
            continue
        card.set_id = target
        moved.append((card.card_id, target))

    db.commit()

    remaining = db.query(CardModel).filter(CardModel.set_id == set_id).count()
    deleted = False
    if remaining == 0 and delete_when_empty:
        delete_card_set(db, set_id)
        deleted = True

    for card_id, target in moved:
        logger.info("%s: %s → %s", card_id, set_id, target)

    return {
        "set_id": set_id,
        "moved": len(moved),
        "by_target": {t: sum(1 for _, x in moved if x == t) for t in sorted({t for _, t in moved})},
        "stayed": stayed,
        "missing_targets": missing_targets,
        "source_deleted": deleted,
    }


def delete_card_set(db: Session, set_id: str) -> dict:
    """Delete a card set and everything hanging off it.

    For sets that no longer exist upstream — e.g. a post that used to be
    scraped as one set and is now split into several. Nothing cascades in
    the schema, so rows are removed explicitly, children first.

    User-uploaded images are left on disk; the return value reports how many
    variants referenced one so the caller can decide what to do about them.
    """
    card_set = db.get(CardSetModel, set_id)
    if card_set is None:
        raise LookupError(f"Card set not found: {set_id}")

    card_ids = [row[0] for row in db.query(CardModel.card_id).filter(CardModel.set_id == set_id).all()]

    user_uploads = 0
    owned = 0
    if card_ids:
        variants = db.query(CardVariantModel).filter(CardVariantModel.card_id.in_(card_ids)).all()
        user_uploads = sum(1 for v in variants if v.image_source == "user_upload")
        owned = sum(v.owned_count for v in variants)

    stats = {
        "set_id": set_id,
        "cards": len(card_ids),
        "variants": 0,
        "owned_count": owned,
        "user_uploaded_images": user_uploads,
    }

    if card_ids:
        stats["variants"] = (
            db.query(CardVariantModel)
            .filter(CardVariantModel.card_id.in_(card_ids))
            .delete(synchronize_session=False)
        )
        for model in (CardVariantOverrideModel, CardOverrideModel, CardEditModel):
            db.query(model).filter(model.card_id.in_(card_ids)).delete(synchronize_session=False)
        db.query(CardModel).filter(CardModel.set_id == set_id).delete(synchronize_session=False)

    db.query(CardSetOverrideModel).filter(CardSetOverrideModel.set_id == set_id).delete(
        synchronize_session=False
    )
    db.delete(card_set)
    db.commit()

    logger.info("Deleted set %s (%d cards, %d variants)", set_id, stats["cards"], stats["variants"])
    return stats
