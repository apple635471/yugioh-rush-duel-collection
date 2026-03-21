"""Import scraped card data (JSON) into the SQLite database."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import CardModel, CardOverrideModel, CardSetModel, CardSetOverrideModel, CardVariantModel, CardVariantOverrideModel

logger = logging.getLogger(__name__)

# Mirrors PRODUCT_TYPE_MAP in the scraper's parser.py.
# Used to re-derive product_type when legacy JSON files contain "unknown".
# Longer prefixes (SBD) must appear before shorter ones (SD) would,
# but since startswith() is used and "SBD".startswith("SD") is False,
# insertion order doesn't affect correctness — it's kept for readability.
_SET_PREFIX_TO_PRODUCT_TYPE: dict[str, str] = {
    "KP": "booster",
    "SD": "structure_deck",
    "SBD": "structure_deck",
    "ST": "structure_deck",
    "GRD": "structure_deck",
    "CP": "character_pack",
    "GRC": "go_rush_character",
    "B0": "battle_pack",
    "B2": "battle_pack",
    "MAX": "maximum_pack",
    "EXT": "extra_pack",
    "LGP": "legend_pack",
    "VSP": "vs_pack",
    "TB": "tournament_pack",
    "AP": "advanced_pack",
    "ORP": "over_rush_pack",
}


def _derive_product_type(set_id: str) -> str:
    """Derive product type from set_id prefix.

    Fallback for legacy scraper data where product_type was stored as
    'unknown' because the prefix was not yet mapped at scrape time.
    Returns 'unknown' when no prefix matches.
    """
    for prefix, ptype in _SET_PREFIX_TO_PRODUCT_TYPE.items():
        if set_id.startswith(prefix):
            return ptype
    return "unknown"


def import_scraper_data(
    db: Session,
    scraper_data_dir: Path,
    force: bool = False,
) -> dict:
    """Import all card sets from scraper JSON files into the database.

    Args:
        db: SQLAlchemy session.
        scraper_data_dir: Path to the scraper's data/ directory.
        force: If True, overwrite all card/set fields (but never owned_count).

    Returns:
        Summary dict with counts.
    """
    stats = {"sets_imported": 0, "cards_imported": 0, "variants_created": 0}

    json_files = sorted(scraper_data_dir.glob("*/cards.json"))
    if not json_files:
        logger.warning(f"No cards.json files found in {scraper_data_dir}")
        return stats

    logger.info(f"Found {len(json_files)} card set JSON files")

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            _import_one_set(db, data, force)
            stats["sets_imported"] += 1
            stats["cards_imported"] += len(data.get("cards", []))
        except Exception as e:
            logger.error(f"Error importing {json_file}: {e}")
            continue

    db.commit()

    # Count total variants
    stats["variants_created"] = db.query(CardVariantModel).count()
    logger.info(
        f"Import complete: {stats['sets_imported']} sets, "
        f"{stats['cards_imported']} cards, {stats['variants_created']} variants"
    )
    return stats


def _import_one_set(db: Session, data: dict, force: bool) -> None:
    """Import a single card set from parsed JSON data.

    Fields that have user overrides (in card_set_overrides) will NOT be
    overwritten by scraper data — the override value is applied instead.
    """
    set_id = data["set_id"]

    # Skip manually created sets — they are managed by the user, not the scraper
    existing = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if existing and existing.is_manual:
        logger.debug(f"Skipping manually created set: {set_id}")
        return

    # Upsert card_set
    card_set = existing
    if card_set is None:
        card_set = CardSetModel(set_id=set_id)
        db.add(card_set)

    # Load user overrides for this set
    overrides: dict[str, str | None] = {}
    for ov in (
        db.query(CardSetOverrideModel)
        .filter_by(set_id=set_id)
        .all()
    ):
        overrides[ov.field_name] = ov.value

    # Helper: use override value if present, otherwise use scraper value
    def _val(field: str, scraper_val):  # noqa: ANN001
        if field in overrides:
            return overrides[field]
        return scraper_val

    card_set.set_name_jp = _val("set_name_jp", data.get("set_name_jp", ""))
    card_set.set_name_zh = _val("set_name_zh", data.get("set_name_zh", ""))
    scraper_product_type = data.get("product_type", "unknown")
    # Re-derive from set_id prefix when legacy JSON has "unknown", so that
    # re-importing old scraper files automatically corrects the DB.
    if scraper_product_type == "unknown":
        scraper_product_type = _derive_product_type(set_id)
    card_set.product_type = _val("product_type", scraper_product_type)
    card_set.release_date = _val("release_date", data.get("release_date"))
    card_set.post_url = data.get("post_url", "")  # post_url 不需要 override
    if "total_cards" in overrides:
        card_set.total_cards = int(overrides["total_cards"]) if overrides["total_cards"] else 0
    else:
        card_set.total_cards = data.get("total_cards", 0)
    if "rarity_distribution" in overrides:
        card_set.rarity_distribution = overrides["rarity_distribution"]
    else:
        rarity_dist = data.get("rarity_distribution")
        if rarity_dist:
            card_set.rarity_distribution = json.dumps(rarity_dist, ensure_ascii=False)
    db.flush()

    # Import cards
    for card_data in data.get("cards", []):
        _import_one_card(db, card_data, set_id, force)


def _import_one_card(
    db: Session, card_data: dict, set_id: str, force: bool
) -> None:
    """Import a single card and its rarity variants.

    - Cards with is_manual=True are skipped entirely.
    - For other cards, per-field overrides from card_overrides are respected.
    """
    card_id = card_data["card_id"]
    rarity_string = card_data.get("rarity", "N")

    # Upsert card
    card = db.query(CardModel).filter_by(card_id=card_id).first()

    if card is not None and card.is_manual and not force:
        # Never overwrite manually created cards (unless --force)
        logger.debug(f"Skipping manual card {card_id}")
        return

    if card is None:
        card = CardModel(card_id=card_id, set_id=set_id)
        db.add(card)
    # Never overwrite set_id for existing cards — scraper data may occasionally
    # reference a card under the wrong set (e.g. a cross-post on the blog).
    # Use --force to override this guard when a deliberate set move is needed.
    elif force:
        card.set_id = set_id

    # Load per-field overrides (skipped when force=True)
    overrides: dict[str, str | None] = {}
    if not force:
        for ov in db.query(CardOverrideModel).filter_by(card_id=card_id).all():
            overrides[ov.field_name] = ov.value

    def _val(field: str, scraper_val):  # noqa: ANN001
        if field in overrides:
            return overrides[field]
        return scraper_val
    card.name_jp = _val("name_jp", card_data.get("name_jp", ""))
    card.name_zh = _val("name_zh", card_data.get("name_zh", ""))
    card.card_type = _val("card_type", card_data.get("card_type", ""))
    card.attribute = _val("attribute", card_data.get("attribute"))
    card.monster_type = _val("monster_type", card_data.get("monster_type"))

    level_val = _val("level", card_data.get("level"))
    card.level = int(level_val) if level_val is not None else None

    card.atk = _val("atk", card_data.get("atk"))
    card.defense = _val("defense", card_data.get("defense"))
    card.maximum_atk = _val("maximum_atk", card_data.get("maximum_atk"))
    card.summon_condition = _val("summon_condition", card_data.get("summon_condition"))
    card.condition = _val("condition", card_data.get("condition"))
    card.effect = _val("effect", card_data.get("effect"))
    card.continuous_effect = _val("continuous_effect", card_data.get("continuous_effect"))

    is_legend_val = _val("is_legend", card_data.get("is_legend", False))
    if isinstance(is_legend_val, str):
        card.is_legend = is_legend_val.lower() == "true"
    else:
        card.is_legend = bool(is_legend_val)

    card.original_rarity_string = _val("original_rarity_string", rarity_string)
    db.flush()

    # Split rarity string into individual variants (use resolved value with override)
    resolved_rarity = card.original_rarity_string or rarity_string
    rarities = [r.strip() for r in resolved_rarity.split("/") if r.strip()]
    if not rarities:
        rarities = ["N"]

    image_file = card_data.get("image_file")

    # Load variant overrides (remap / delete) for this card
    variant_overrides: dict[str, CardVariantOverrideModel] = {}
    if not force:
        for ov in db.query(CardVariantOverrideModel).filter_by(card_id=card_id).all():
            variant_overrides[ov.scraper_rarity] = ov

    for sort_order, rarity in enumerate(rarities):
        ov = variant_overrides.get(rarity)
        if ov is None:
            _upsert_variant(db, card_id, rarity, sort_order, image_file)
        elif ov.action == "remap" and ov.target_rarity:
            _upsert_variant(db, card_id, ov.target_rarity, sort_order, image_file)
        # elif ov.action == "delete": skip — do not create/update this variant


def _upsert_variant(
    db: Session,
    card_id: str,
    rarity: str,
    sort_order: int,
    image_file: str | None,
) -> None:
    """Upsert a card variant, preserving owned_count."""
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity)
        .first()
    )
    if variant is None:
        variant = CardVariantModel(
            card_id=card_id,
            rarity=rarity,
            sort_order=sort_order,
            image_source="scraper" if image_file else None,
            image_path=image_file,
            scraper_image_path=image_file,
            owned_count=0,
        )
        db.add(variant)
    else:
        # Update sort order and image (if from scraper), but NEVER touch owned_count
        variant.sort_order = sort_order
        # Always keep scraper_image_path up to date with latest scraper data
        if image_file:
            variant.scraper_image_path = image_file
        if variant.image_source != "user_upload":
            variant.image_source = "scraper" if image_file else None
            variant.image_path = image_file
