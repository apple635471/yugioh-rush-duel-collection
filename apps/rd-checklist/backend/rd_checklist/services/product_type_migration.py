"""Idempotent migration: put every set on the product type its set_id implies.

Classification is rule-only (see ``product_types``), so this recomputes each
row from ``canonical_product_type`` and **deletes every product_type
override**. Those overrides were never hand-picked corrections — the
set-update endpoint used to store any edited field as an override, so most of
them just mirror whatever the classifier produced at the time — and nothing
can create them any more: the field is not editable and the import ignores
them. Leaving them behind would only confuse the next person reading the
override table.

Safe to run repeatedly — once everything is canonical it becomes a no-op.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import CardSetModel, CardSetOverrideModel
from ..product_types import canonical_product_type

logger = logging.getLogger(__name__)


def migrate_product_types(db: Session) -> dict:
    """Run the migration. Returns stats plus the list of changes made."""
    changes: list[tuple[str, str, str]] = []

    for card_set in db.query(CardSetModel).order_by(CardSetModel.set_id).all():
        target = canonical_product_type(card_set.set_id)
        if card_set.product_type != target:
            changes.append((card_set.set_id, card_set.product_type, target))
            card_set.product_type = target

    overrides_dropped = (
        db.query(CardSetOverrideModel)
        .filter(CardSetOverrideModel.field_name == "product_type")
        .delete(synchronize_session=False)
    )

    db.commit()

    for set_id, before, after in changes:
        logger.info("%s: %s → %s", set_id, before, after)

    return {
        "sets_changed": len(changes),
        "overrides_dropped": overrides_dropped,
        "changes": changes,
    }
