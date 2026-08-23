"""Card set maintenance operations that don't belong to the import flow."""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from ..product_types import canonical_product_type
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



def set_id_from_card_id(card_id: str) -> str | None:
    """Set a card belongs to, judged by its own card number.

    Card numbers are RD/{set_id}-{number}, and the set id in the number is
    taken at face value: a different code means a different set, full stop.
    Battle packs' B-half and S-half (B251/S251) are therefore separate sets,
    as are series that get sprinkled across several posts (S23P).
    """
    m = _SET_CODE_RE.search(card_id)
    return m.group(1) if m else None


# Card numbers that never get a set of their own, and where they live instead.
# For one-off oddities — a single promo numbered RD/21CC-* is not a product
# line, it is one card in the Promo pile. resplit_set() keeps these out of
# their own set and files them under the home named here.
#
# This is a rule about the number, so it also catches cards imported later.
# For a one-time decision about one specific card, use merge-set, which
# records a pin in card_overrides instead.
SET_ID_HOMES: dict[str, str] = {
    "21CC": "PROMO",
}

PINNED_FIELD = "set_id"


def pinned_card_ids(db: Session) -> set[str]:
    """Cards deliberately filed under a set their number doesn't name.

    Recorded as a card_overrides row on "set_id" — the same mechanism that
    protects hand-edited fields from being overwritten by an import. Used to
    keep a merge from being undone by the next resplit sweep.
    """
    return {
        row[0]
        for row in db.query(CardOverrideModel.card_id)
        .filter(CardOverrideModel.field_name == PINNED_FIELD)
        .all()
    }


def merge_set(db: Session, source_id: str, target_id: str) -> dict:
    """Move every card of one set into another and pin them there.

    For set ids that should not exist on their own — a one-card oddity like
    21CC that belongs in the Promo pile. The cards keep their numbers; a pin
    records that their home was chosen by hand, so `resplit_set` leaves them
    alone. The emptied source set is deleted unless it was created by hand.
    """
    if source_id == target_id:
        raise ValueError("Source and target are the same set")

    source = db.get(CardSetModel, source_id)
    if source is None:
        raise LookupError(f"Card set not found: {source_id}")
    if db.get(CardSetModel, target_id) is None:
        raise LookupError(f"Target card set not found: {target_id}")

    moved = 0
    for card in db.query(CardModel).filter(CardModel.set_id == source_id).all():
        card.set_id = target_id
        override = (
            db.query(CardOverrideModel)
            .filter_by(card_id=card.card_id, field_name=PINNED_FIELD)
            .first()
        )
        if override is None:
            db.add(
                CardOverrideModel(
                    card_id=card.card_id, field_name=PINNED_FIELD, value=target_id
                )
            )
        else:
            override.value = target_id
        moved += 1

    db.commit()

    deleted = False
    if moved and not source.is_manual:
        delete_card_set(db, source_id)
        deleted = True

    logger.info("Merged %s into %s (%d cards)", source_id, target_id, moved)
    return {
        "source_id": source_id,
        "target_id": target_id,
        "moved": moved,
        "source_deleted": deleted,
    }


def resplit_set(db: Session, set_id: str, delete_when_empty: bool = True) -> dict:
    """Move a set's cards to the sets their own card numbers point at.

    Card numbers are RD/{set_id}-{number}: a card whose number names another
    set belongs to that set. This happens when one blog post covers several
    products — a whole year of event packs, or a promo series sprinkled one
    card at a time across a season's posts.

    Cards are moved rather than deleted and re-imported, so everything keyed
    by card_id — overrides, edits, uploaded images, owned_count — comes along
    untouched. Missing target sets are created, copying the source's name,
    release date and post URL (the products do share a post, after all);
    product_type is derived from the new set id.

    A source set that ends up empty is deleted, unless it was created by hand.
    """
    card_set = db.get(CardSetModel, set_id)
    if card_set is None:
        raise LookupError(f"Card set not found: {set_id}")

    moved: list[tuple[str, str]] = []
    created: list[str] = []
    stayed = 0
    pinned = pinned_card_ids(db)
    kept_pinned = 0

    for card in db.query(CardModel).filter(CardModel.set_id == set_id).all():
        target = set_id_from_card_id(card.card_id)
        if target is None or target == set_id:
            stayed += 1
            continue
        if card.card_id in pinned:
            kept_pinned += 1
            continue

        home = SET_ID_HOMES.get(target)
        if home is not None:
            # Never gets its own set; belongs in `home` when that set exists.
            if card.set_id == home or db.get(CardSetModel, home) is None:
                kept_pinned += 1
                continue
            target = home

        if db.get(CardSetModel, target) is None:
            db.add(
                CardSetModel(
                    set_id=target,
                    set_name_jp=card_set.set_name_jp,
                    set_name_zh=card_set.set_name_zh,
                    product_type=canonical_product_type(target),
                    release_date=card_set.release_date,
                    post_url=card_set.post_url,
                    total_cards=0,
                    # Derived from scraped cards, so not hand-made even when
                    # the set they came out of was.
                    is_manual=False,
                )
            )
            db.flush()
            created.append(target)

        card.set_id = target
        moved.append((card.card_id, target))

    db.commit()

    # Newly created sets have no scraped card count of their own; use what
    # actually landed in them. Existing sets keep the count from their post.
    for target in created:
        new_set = db.get(CardSetModel, target)
        new_set.total_cards = db.query(CardModel).filter(CardModel.set_id == target).count()
    if created:
        db.commit()

    remaining = db.query(CardModel).filter(CardModel.set_id == set_id).count()
    deleted = False
    if remaining == 0 and delete_when_empty and not card_set.is_manual:
        delete_card_set(db, set_id)
        deleted = True

    for card_id, target in moved:
        logger.info("%s: %s → %s", card_id, set_id, target)

    return {
        "set_id": set_id,
        "moved": len(moved),
        "by_target": {t: sum(1 for _, x in moved if x == t) for t in sorted({t for _, t in moved})},
        "created": created,
        "stayed": stayed,
        "kept_pinned": kept_pinned,
        "source_deleted": deleted,
        "source_empty_kept": remaining == 0 and not deleted,
    }


def find_split_candidates(db: Session) -> dict[str, dict[str, int]]:
    """Sets holding cards whose numbers name a different set."""
    pinned = pinned_card_ids(db)
    out: dict[str, dict[str, int]] = {}
    for (set_id,) in db.query(CardSetModel.set_id).order_by(CardSetModel.set_id).all():
        counts: dict[str, int] = {}
        for (card_id,) in db.query(CardModel.card_id).filter(CardModel.set_id == set_id).all():
            if card_id in pinned:
                continue
            target = set_id_from_card_id(card_id)
            if target is None:
                continue
            target = SET_ID_HOMES.get(target, target)
            if target != set_id:
                counts[target] = counts.get(target, 0) + 1
        if counts:
            out[set_id] = counts
    return out


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
