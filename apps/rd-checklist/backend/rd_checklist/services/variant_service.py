"""Variant deletion, shared by the single-variant endpoint and bulk apply.

Deleting a printing is more than dropping a row: unless a deletion override is
recorded, the next import recreates it from the scraper data — which is how a
wrong rarity would keep coming back after the user corrects it.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import CardModel, CardVariantModel, CardVariantOverrideModel

logger = logging.getLogger(__name__)


def remap_variant(
    db: Session,
    card_id: str,
    from_rarity: str,
    to_rarity: str,
    from_alternate_art: bool = False,
    to_alternate_art: bool | None = None,
) -> bool:
    """Correct a printing in place — its rarity, its artwork flag, or both.

    Preferred over delete-then-create when the scraper simply read the printing
    wrong: the variant row carries owned_count and the uploaded image, so
    editing it keeps both.

    What the import then does with it depends on the direction:

    * to a normal variant — a `remap` override points the scraper's rarity at
      the corrected one, so the next import updates this row instead of
      recreating the old rarity beside it.
    * to an alternate artwork — the import only ever touches normal variants,
      so the row is safe once there; a `delete` override stops the scraper's
      rarity from reappearing as a normal variant next to it.

    Returns False when the source is missing or the target already exists.
    The caller commits.
    """
    if to_alternate_art is None:
        to_alternate_art = from_alternate_art
    if from_rarity == to_rarity and from_alternate_art == to_alternate_art:
        return False

    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=from_rarity, is_alternate_art=from_alternate_art)
        .first()
    )
    if variant is None:
        return False

    clash = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=to_rarity, is_alternate_art=to_alternate_art)
        .first()
    )
    if clash is not None:
        return False

    now = datetime.now(timezone.utc).isoformat()

    def _override_for(rarity: str) -> CardVariantOverrideModel | None:
        chained = (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, action="remap")
            .filter(CardVariantOverrideModel.target_rarity == rarity)
            .first()
        )
        return chained or (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, scraper_rarity=rarity)
            .first()
        )

    # The scraper only ever produced this row if it started as a normal
    # variant; only then is there something for an override to redirect.
    if not from_alternate_art:
        existing = _override_for(from_rarity)
        action = "delete" if to_alternate_art else "remap"
        target = None if to_alternate_art else to_rarity
        if existing:
            existing.action = action
            existing.target_rarity = target
            existing.updated_at = now
        else:
            db.add(
                CardVariantOverrideModel(
                    card_id=card_id,
                    scraper_rarity=from_rarity,
                    action=action,
                    target_rarity=target,
                )
            )
    elif not to_alternate_art:
        # Becoming a normal variant: a leftover deletion override for that
        # rarity would have the import skip it.
        existing = _override_for(to_rarity)
        if existing is not None and existing.action == "delete":
            db.delete(existing)

    variant.rarity = to_rarity
    variant.is_alternate_art = to_alternate_art

    # original_rarity_string tracks what the scraper said, so it only moves
    # when a normal variant is renamed to another normal variant.
    if not from_alternate_art and not to_alternate_art:
        card = db.query(CardModel).filter_by(card_id=card_id).first()
        if card is not None:
            rarities = [
                r.strip() for r in card.original_rarity_string.split("/") if r.strip()
            ]
            if from_rarity in rarities:
                rarities[rarities.index(from_rarity)] = to_rarity
                card.original_rarity_string = "/".join(rarities)

    logger.info(
        "Remapped variant %s: %s%s → %s%s",
        card_id,
        from_rarity, " alt" if from_alternate_art else "",
        to_rarity, " alt" if to_alternate_art else "",
    )
    return True


def delete_variant(
    db: Session, card_id: str, rarity: str, is_alternate_art: bool
) -> bool:
    """Delete one printing and stop the import recreating it.

    Returns False when there was nothing to delete. The caller commits.

    Overrides are only kept for non-alternate variants: alternate artworks are
    not produced by the scraper, so there is nothing to suppress.
    """
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity, is_alternate_art=is_alternate_art)
        .first()
    )
    if variant is None:
        return False

    now = datetime.now(timezone.utc).isoformat()

    if not is_alternate_art:
        # A variant the user had already remapped becomes a deletion instead.
        chained = (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, action="remap")
            .filter(CardVariantOverrideModel.target_rarity == rarity)
            .first()
        )
        existing = chained or (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, scraper_rarity=rarity)
            .first()
        )
        if existing:
            existing.action = "delete"
            existing.target_rarity = None
            existing.updated_at = now
        else:
            db.add(
                CardVariantOverrideModel(
                    card_id=card_id,
                    scraper_rarity=rarity,
                    action="delete",
                    target_rarity=None,
                )
            )

    db.delete(variant)

    # Keep the card's rarity string in step (scraper-side rarities only).
    if not is_alternate_art:
        card = db.query(CardModel).filter_by(card_id=card_id).first()
        if card is not None:
            remaining = [
                r.strip()
                for r in card.original_rarity_string.split("/")
                if r.strip() and r.strip() != rarity
            ]
            card.original_rarity_string = "/".join(remaining)

    logger.info("Deleted variant %s (%s%s)", card_id, rarity, " alt" if is_alternate_art else "")
    return True
