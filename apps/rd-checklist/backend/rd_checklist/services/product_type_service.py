"""Classification: which product line a set belongs to.

The rules live in the database (``product_types`` + ``product_type_rules``),
not in code, so editing them in the UI immediately re-files every set — there
is no stored ``product_type`` to migrate. The scraper reads the same rules
through ``GET /api/product-types``.

Matching: each rule is a Python regular expression applied to the set_id with
``re.search`` and ``re.IGNORECASE``. An unanchored pattern therefore means
"contains" (``JMP`` → SJMP / VJMP / WJMP) and an anchored one pins the shape
(``^\\d{2}PR$`` → 23PR, 24PR, …). Rules are tried in product-type order, then
rule order; the first hit wins. The fallback type carries no rules and takes
whatever is left.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import ProductTypeModel, ProductTypeRuleModel

logger = logging.getLogger(__name__)

# Used before the table is seeded, and when every rule fails.
FALLBACK_CODE = "other"


@dataclass(frozen=True)
class _CompiledType:
    code: str
    patterns: tuple[re.Pattern[str], ...]


# Compiled rules, ordered. None means "not loaded yet".
_cache: tuple[_CompiledType, ...] | None = None
_fallback: str = FALLBACK_CODE


def invalidate() -> None:
    """Drop the cached rules; the next classification reloads them.

    Called after any edit to the product types or their rules.
    """
    global _cache
    _cache = None


def load(db: Session) -> None:
    """Compile the rules from the DB into the cache."""
    global _cache, _fallback

    types = (
        db.query(ProductTypeModel)
        .order_by(ProductTypeModel.sort_order, ProductTypeModel.code)
        .all()
    )
    compiled: list[_CompiledType] = []
    fallback = FALLBACK_CODE
    for pt in types:
        if pt.is_fallback:
            fallback = pt.code
            continue
        patterns = []
        for rule in sorted(pt.rules, key=lambda r: (r.sort_order, r.id)):
            try:
                patterns.append(re.compile(rule.pattern, re.IGNORECASE))
            except re.error:
                # A bad pattern cannot reach the DB through the API, but a
                # hand-edited row should not take the whole app down.
                logger.warning(
                    "product type %s: skipping invalid pattern %r", pt.code, rule.pattern
                )
        if patterns:
            compiled.append(_CompiledType(code=pt.code, patterns=tuple(patterns)))

    _cache = tuple(compiled)
    _fallback = fallback


def _ensure_loaded() -> tuple[_CompiledType, ...]:
    global _cache
    if _cache is None:
        # Reached from CardSetModel.product_type, which has no session of its
        # own; open a short-lived one rather than threading one through.
        from ..database import SessionLocal

        db = SessionLocal()
        try:
            load(db)
        finally:
            db.close()
    return _cache or ()


def classify_set(set_id: str) -> str:
    """The product type code for a set_id — the first rule that matches."""
    for entry in _ensure_loaded():
        for pattern in entry.patterns:
            if pattern.search(set_id or ""):
                return entry.code
    return _fallback


def matching_set_ids(patterns: list[str], set_ids: list[str]) -> list[str]:
    """Which of `set_ids` these patterns would claim (editor preview).

    Ignores every other product type — it answers "what does this rule catch",
    not "what would end up here", because an earlier type may claim some of
    them first.
    """
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error:
            continue
    return [s for s in set_ids if any(p.search(s) for p in compiled)]


def fallback_code(db: Session) -> str:
    """The code of the fallback type, or the default when there isn't one."""
    row = db.query(ProductTypeModel).filter_by(is_fallback=True).first()
    return row.code if row else FALLBACK_CODE


# ── Seeding ───────────────────────────────────────────────────────────────
# The rules the app shipped with, used to fill an empty table (a fresh
# install, or the migration off the old hard-coded map). Everything here is
# editable afterwards — this is a starting point, not a source of truth.
DEFAULT_PRODUCT_TYPES: list[dict] = [
    {
        "code": "booster", "name_en": "Booster Pack", "name_zh": "補充包",
        "group_label": "補充包系列", "color": "#C9A84C", "rules": [r"^KP\d"],
    },
    {
        "code": "advanced_pack", "name_en": "Advanced Pack", "name_zh": "上級包",
        "group_label": "補充包系列", "color": "#E0776B", "rules": [r"^AP\d"],
    },
    {
        "code": "maximum_pack", "name_en": "Maximum Pack", "name_zh": "巨極包",
        "group_label": "補充包系列", "color": "#6FBF9B", "rules": [r"^MAX\d"],
    },
    {
        "code": "over_rush_pack", "name_en": "Over Rush Pack", "name_zh": "超越超速包",
        "group_label": "補充包系列", "color": "#A78BFA", "rules": [r"^ORP\d"],
    },
    {
        "code": "legend_pack", "name_en": "Legend Pack", "name_zh": "傳說包",
        "group_label": "補充包系列", "color": "#7DB8E8", "rules": [r"^LGP\d"],
    },
    {
        "code": "triple_build_pack", "name_en": "Triple Build Pack", "name_zh": "三重構築包",
        "group_label": "補充包系列", "color": "#E8A0C8", "rules": [r"^TB\d"],
    },
    {
        "code": "structure_deck", "name_en": "Structure Deck", "name_zh": "預組",
        "group_label": "預組", "color": "#5FB3A1",
        "rules": [r"^SBD", r"^SD", r"^ST\d", r"^GRD"],
    },
    {
        # Battle packs ship as a B-half and an S-half (B251/S251); the S side
        # is its own set, so it needs its own rule.
        "code": "battle_pack", "name_en": "Battle Pack", "name_zh": "戰鬥包",
        "group_label": "其他", "color": "#E0A458",
        "rules": [r"^B0\d", r"^B2\d", r"^S2"],
    },
    {
        # Convenience-store tie-ins, magazine inserts, Jump Festa giveaways,
        # gum, game bonus cards.
        "code": "promo", "name_en": "Promo", "name_zh": None,
        "group_label": "其他", "color": "#B9A3D6",
        "rules": [r"^711", r"^\d{2}PR$", r"JMP", r"^P\d", r"^G\d", r"^PROMO", r"^ECG\d"],
    },
    {
        "code": "other", "name_en": "Other", "name_zh": None,
        "group_label": "其他", "color": "#8C90A3", "rules": [], "is_fallback": True,
    },
]


def seed_defaults(db: Session, force: bool = False) -> int:
    """Fill an empty product_types table with the defaults.

    Returns the number of types created. Does nothing when the table already
    has rows (the user's edits win) unless `force` is set.
    """
    if db.query(ProductTypeModel).count() and not force:
        return 0

    created = 0
    for order, spec in enumerate(DEFAULT_PRODUCT_TYPES):
        if db.query(ProductTypeModel).filter_by(code=spec["code"]).first():
            continue
        db.add(
            ProductTypeModel(
                code=spec["code"],
                name_en=spec["name_en"],
                name_zh=spec["name_zh"],
                group_label=spec["group_label"],
                color=spec["color"],
                sort_order=order,
                is_fallback=spec.get("is_fallback", False),
            )
        )
        for rule_order, pattern in enumerate(spec["rules"]):
            db.add(
                ProductTypeRuleModel(
                    product_type_code=spec["code"],
                    pattern=pattern,
                    sort_order=rule_order,
                )
            )
        created += 1

    db.commit()
    invalidate()
    return created


def migrate_to_db_rules(db: Session, reseed: bool = False) -> dict:
    """Move classification into the DB. Idempotent.

    Seeds the rules, reports every set whose type changes as a result, drops
    the legacy ``card_sets.product_type`` column and any leftover
    ``product_type`` overrides. Reading the old column first is what makes the
    before/after report possible — after this runs there is nothing to compare.
    """
    from sqlalchemy import text

    from ..database import engine, init_db
    from ..models import CardSetOverrideModel

    legacy: dict[str, str] = {}
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='card_sets'")
        ).fetchone()
        had_column = bool(row) and "product_type" in row[0]
        if had_column:
            legacy = {
                set_id: product_type
                for set_id, product_type in conn.execute(
                    text("SELECT set_id, product_type FROM card_sets")
                )
            }

    types_seeded = seed_defaults(db, force=reseed)

    # Creates the new tables, seeds when empty, drops the legacy column.
    init_db()
    invalidate()

    changes = [
        (set_id, before, classify_set(set_id))
        for set_id, before in sorted(legacy.items())
        if classify_set(set_id) != before
    ]

    overrides_dropped = (
        db.query(CardSetOverrideModel)
        .filter(CardSetOverrideModel.field_name == "product_type")
        .delete(synchronize_session=False)
    )
    db.commit()

    return {
        "types_seeded": types_seeded,
        "legacy_column": "dropped" if had_column else "already gone",
        "overrides_dropped": overrides_dropped,
        "changes": changes,
    }
