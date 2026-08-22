"""One-off, idempotent migration: re-classify existing sets' product_type.

Brings rows written before the product type cleanup onto the current set:
retired types (character_pack, go_rush_character, extra_pack, vs_pack) fold
into "other", tournament_pack becomes triple_build_pack, the old "other"
bucket (7-11 tie-ins, magazine promos) becomes "promo", and "unknown"
becomes "other". Sets whose set_id now has a rule (23PR → promo,
S254 → battle_pack) pick that up too.

product_type overrides are rewritten alongside the row. They are not
hand-picked corrections here: the set-update endpoint stores every edited
field as an override, so most of them just mirror whatever the classifier
produced at the time, and leaving them behind would let the next import
restore the old value. A set_id rule therefore wins over an override; an
override pointing at a type no rule covers is preserved.

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
    overrides = {
        row.set_id: row
        for row in db.query(CardSetOverrideModel)
        .filter(CardSetOverrideModel.field_name == "product_type")
        .all()
    }

    changes: list[tuple[str, str, str]] = []
    overrides_rewritten = 0

    for card_set in db.query(CardSetModel).order_by(CardSetModel.set_id).all():
        override = overrides.get(card_set.set_id)
        current = override.value if override else card_set.product_type
        target = canonical_product_type(card_set.set_id, current)

        if card_set.product_type != target:
            changes.append((card_set.set_id, card_set.product_type, target))
            card_set.product_type = target

        if override is not None and override.value != target:
            override.value = target
            overrides_rewritten += 1

    db.commit()

    for set_id, before, after in changes:
        logger.info("%s: %s → %s", set_id, before, after)

    return {
        "sets_changed": len(changes),
        "overrides_rewritten": overrides_rewritten,
        "changes": changes,
    }
