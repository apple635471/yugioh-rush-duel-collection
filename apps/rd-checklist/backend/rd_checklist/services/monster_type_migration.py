"""One-off, idempotent migration: normalize monster races in existing rows.

Collapses the blog's inconsistent spellings (三種 omega 寫法) and fills in
missing 族 suffixes, so the 種族 filter offers one entry per race. Safe to run
repeatedly — once everything is canonical it becomes a no-op.

Card-level overrides on monster_type are normalized as well: leaving them
behind would let the next import restore the old spelling.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import CardModel, CardOverrideModel
from ..monster_types import normalize_monster_type

logger = logging.getLogger(__name__)


def migrate_monster_types(db: Session) -> dict:
    """Run the migration. Returns stats plus what changed, by race."""
    changed: dict[str, dict[str, int]] = {}

    for card in db.query(CardModel).filter(CardModel.monster_type.isnot(None)).all():
        target = normalize_monster_type(card.monster_type)
        if target != card.monster_type:
            changed.setdefault(card.monster_type, {}).setdefault(target, 0)
            changed[card.monster_type][target] += 1
            logger.info("%s: %s → %s", card.card_id, card.monster_type, target)
            card.monster_type = target

    overrides_updated = 0
    for override in (
        db.query(CardOverrideModel)
        .filter(CardOverrideModel.field_name == "monster_type")
        .all()
    ):
        target = normalize_monster_type(override.value)
        if target != override.value:
            override.value = target
            overrides_updated += 1

    db.commit()

    return {
        "cards_changed": sum(sum(v.values()) for v in changed.values()),
        "overrides_updated": overrides_updated,
        "changes": {
            before: after for before, after in changed.items()
        },
    }
