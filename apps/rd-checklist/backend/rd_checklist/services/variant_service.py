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
