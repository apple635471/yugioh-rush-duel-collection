"""Import scraped card data (JSON) into the SQLite database."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import CardModel, CardSetModel, CardVariantModel

logger = logging.getLogger(__name__)


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
    """Import a single card set from parsed JSON data."""
    set_id = data["set_id"]

    # Upsert card_set
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if card_set is None:
        card_set = CardSetModel(set_id=set_id)
        db.add(card_set)

    card_set.set_name_jp = data.get("set_name_jp", "")
    card_set.set_name_zh = data.get("set_name_zh", "")
    card_set.product_type = data.get("product_type", "unknown")
    card_set.release_date = data.get("release_date")
    card_set.post_url = data.get("post_url", "")
    card_set.total_cards = data.get("total_cards", 0)
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
    """Import a single card and its rarity variants."""
    card_id = card_data["card_id"]
    rarity_string = card_data.get("rarity", "N")

    # Upsert card
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if card is None:
        card = CardModel(card_id=card_id, set_id=set_id)
        db.add(card)

    # Always update card fields from scraper (these are source-of-truth)
    card.set_id = set_id
    card.name_jp = card_data.get("name_jp", "")
    card.name_zh = card_data.get("name_zh", "")
    card.card_type = card_data.get("card_type", "")
    card.attribute = card_data.get("attribute")
    card.monster_type = card_data.get("monster_type")
    card.level = card_data.get("level")
    card.atk = card_data.get("atk")
    card.defense = card_data.get("defense")
    card.summon_condition = card_data.get("summon_condition")
    card.condition = card_data.get("condition")
    card.effect = card_data.get("effect")
    card.continuous_effect = card_data.get("continuous_effect")
    card.is_legend = card_data.get("is_legend", False)
    card.original_rarity_string = rarity_string
    db.flush()

    # Split rarity string into individual variants
    rarities = [r.strip() for r in rarity_string.split("/") if r.strip()]
    if not rarities:
        rarities = ["N"]

    image_file = card_data.get("image_file")

    for sort_order, rarity in enumerate(rarities):
        _upsert_variant(db, card_id, rarity, sort_order, image_file)


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
