"""One-off, idempotent migration: collapse synonym rarities to canonical codes.

Rewrites existing DB rows and on-disk user uploads so that SRP/PSR→SPR,
NRP/PNR→NPR, URP/PUR→UPR. Safe to run repeatedly — once everything is
canonical it becomes a no-op.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..config import USER_IMAGES_DIR
from ..models import CardModel, CardVariantModel, CardVariantOverrideModel
from ..rarities import normalize_rarity, normalize_rarity_string
from .image_service import _make_upload_filename

logger = logging.getLogger(__name__)


def migrate_rarities(db: Session) -> dict[str, int]:
    """Run the migration. Returns a stats dict of what changed."""
    stats = {
        "variants_renamed": 0,
        "variants_merged": 0,
        "cards_string_updated": 0,
        "overrides_updated": 0,
        "images_renamed": 0,
        "images_skipped_conflict": 0,
    }

    _migrate_variants(db, stats)
    _migrate_card_strings(db, stats)
    _migrate_overrides(db, stats)
    db.flush()
    _migrate_user_images(db, stats)
    db.commit()
    return stats


def _migrate_variants(db: Session, stats: dict[str, int]) -> None:
    """Rename synonym-rarity variants to canonical, merging on collision."""
    variants = db.query(CardVariantModel).all()
    for v in variants:
        canon = normalize_rarity(v.rarity)
        if canon == v.rarity:
            continue  # already canonical

        existing = (
            db.query(CardVariantModel)
            .filter_by(
                card_id=v.card_id,
                rarity=canon,
                is_alternate_art=v.is_alternate_art,
            )
            .first()
        )
        if existing is not None and existing.id != v.id:
            # Collision: fold this synonym variant into the canonical one.
            existing.owned_count += v.owned_count
            # Prefer a user upload over a scraper image.
            if existing.image_source != "user_upload" and v.image_source == "user_upload":
                existing.image_source = "user_upload"
                existing.image_path = f"user_uploads/{_make_upload_filename(existing.card_id, canon)}"
            db.delete(v)
            stats["variants_merged"] += 1
            logger.info("Merged variant %s %s → %s", v.card_id, v.rarity, canon)
        else:
            v.rarity = canon
            if v.image_source == "user_upload":
                v.image_path = f"user_uploads/{_make_upload_filename(v.card_id, canon)}"
            stats["variants_renamed"] += 1


def _migrate_card_strings(db: Session, stats: dict[str, int]) -> None:
    """Canonicalize cards.original_rarity_string."""
    for card in db.query(CardModel).all():
        if not card.original_rarity_string:
            continue
        new = normalize_rarity_string(card.original_rarity_string)
        if new != card.original_rarity_string:
            card.original_rarity_string = new
            stats["cards_string_updated"] += 1


def _migrate_overrides(db: Session, stats: dict[str, int]) -> None:
    """Canonicalize variant-override rarity columns, dropping duplicates."""
    seen: set[tuple[str, str]] = set()
    for ov in db.query(CardVariantOverrideModel).all():
        new_scraper = normalize_rarity(ov.scraper_rarity)
        new_target = normalize_rarity(ov.target_rarity) if ov.target_rarity else ov.target_rarity
        changed = new_scraper != ov.scraper_rarity or new_target != ov.target_rarity
        key = (ov.card_id, new_scraper)
        if key in seen:
            # A different override already claims (card_id, canonical scraper_rarity).
            db.delete(ov)
            stats["overrides_updated"] += 1
            continue
        seen.add(key)
        if changed:
            ov.scraper_rarity = new_scraper
            ov.target_rarity = new_target
            stats["overrides_updated"] += 1


def _migrate_user_images(db: Session, stats: dict[str, int]) -> None:
    """Rename user-uploaded image files with synonym rarity suffixes."""
    if not USER_IMAGES_DIR.exists():
        return
    for path in USER_IMAGES_DIR.glob("*.jpg"):
        stem = path.stem  # e.g. "RD_5TH1-JP003_PUR"
        if "_" not in stem:
            continue
        safe_id, _, rarity_part = stem.rpartition("_")
        canon = normalize_rarity(rarity_part)
        if canon == rarity_part:
            continue  # already canonical
        target = path.with_name(f"{safe_id}_{canon}{path.suffix}")
        if target.exists():
            # Canonical file already present — keep it, drop the synonym duplicate.
            path.unlink()
            stats["images_skipped_conflict"] += 1
            logger.info("User image conflict, removed duplicate %s", path.name)
        else:
            path.rename(target)
            stats["images_renamed"] += 1
            logger.info("Renamed user image %s → %s", path.name, target.name)
