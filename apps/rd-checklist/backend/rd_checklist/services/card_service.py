"""Card-level operations shared by more than one router."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import (
    CardEditModel,
    CardModel,
    CardOverrideModel,
    CardVariantModel,
    CardVariantOverrideModel,
)

logger = logging.getLogger(__name__)


def delete_card_and_variants(db: Session, card_id: str) -> int:
    """Delete a card with everything keyed to it. Returns variants removed.

    Nothing cascades in the schema, so children go first. The caller commits.
    """
    variants = (
        db.query(CardVariantModel).filter_by(card_id=card_id).delete(synchronize_session=False)
    )
    for model in (CardVariantOverrideModel, CardOverrideModel, CardEditModel):
        db.query(model).filter_by(card_id=card_id).delete(synchronize_session=False)
    db.query(CardModel).filter_by(card_id=card_id).delete(synchronize_session=False)
    logger.info("Deleted card %s (%d variant(s))", card_id, variants)
    return variants
