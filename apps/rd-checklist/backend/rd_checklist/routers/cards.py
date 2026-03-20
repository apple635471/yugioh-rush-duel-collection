"""Card detail and editing API endpoints."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CardEditModel,
    CardModel,
    CardOverrideModel,
    CardSetModel,
    CardVariantModel,
    CardVariantOverrideModel,
)
from ..schemas import (
    CardCreate,
    CardOut,
    CardUpdate,
    CardVariantOut,
    NextCardIdOut,
    VariantCreate,
    VariantRarityUpdate,
)

router = APIRouter(prefix="/api/cards", tags=["cards"])


# ── Fixed-path routes MUST come before {card_id:path} catch-all ──


@router.get("/next-id/{set_id}", response_model=NextCardIdOut)
def get_next_card_id(set_id: str, db: Session = Depends(get_db)):
    """Get the next available card_id for a set.

    Scans existing card_ids in the set, finds the max numeric suffix,
    and returns max+1 with the same zero-padding.
    """
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    existing = (
        db.query(CardModel.card_id)
        .filter_by(set_id=set_id)
        .all()
    )

    max_num = -1
    pad_width = 3  # default
    prefix = ""

    # Detect card_id pattern: find the last group of digits
    # e.g. "RD/KP01-JP000" → suffix "000"
    # Derive prefix and pad_width from the card with the highest numeric suffix
    for (cid,) in existing:
        match = re.search(r"(\d+)$", cid)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                pad_width = len(match.group(1))
                prefix = cid[: match.start()]

    if max_num < 0:
        next_num = 0
    else:
        next_num = max_num + 1

    if not prefix:
        prefix = f"RD/{set_id}-JP"

    next_card_id = f"{prefix}{str(next_num).zfill(pad_width)}"
    return NextCardIdOut(next_card_id=next_card_id)


@router.post("", response_model=CardOut, status_code=201)
def create_card(body: CardCreate, db: Session = Depends(get_db)):
    """Create a new manually-created card with one initial variant."""
    card_set = db.query(CardSetModel).filter_by(set_id=body.set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {body.set_id} not found")

    if db.query(CardModel).filter_by(card_id=body.card_id).first():
        raise HTTPException(status_code=409, detail=f"Card {body.card_id} already exists")

    card = CardModel(
        card_id=body.card_id,
        set_id=body.set_id,
        name_jp=body.name_jp,
        name_zh=body.name_zh,
        card_type=body.card_type,
        attribute=body.attribute,
        monster_type=body.monster_type,
        level=body.level,
        atk=body.atk,
        defense=body.defense,
        maximum_atk=body.maximum_atk,
        summon_condition=body.summon_condition,
        condition=body.condition,
        effect=body.effect,
        continuous_effect=body.continuous_effect,
        is_legend=body.is_legend,
        is_manual=True,
        original_rarity_string=body.rarity,
    )
    db.add(card)
    db.flush()

    variant = CardVariantModel(
        card_id=body.card_id,
        rarity=body.rarity,
        sort_order=0,
        image_source=None,
        image_path=None,
        scraper_image_path=None,
        owned_count=0,
    )
    db.add(variant)
    db.commit()
    db.refresh(card)
    return card


# ── Path-parameter routes ──


@router.get("/{card_id:path}", response_model=CardOut)
def get_card(card_id: str, db: Session = Depends(get_db)):
    """Get a card with all its variants."""
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
    return card


@router.patch("/{card_id:path}/variants/{rarity}", response_model=CardOut)
def edit_variant_rarity(card_id: str, rarity: str, body: VariantRarityUpdate, db: Session = Depends(get_db)):
    """Change the rarity of an existing variant.

    Creates/updates a card_variant_override so that reimport maps the old
    scraper rarity to the new rarity and never reverts the change.
    """
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

    variant = db.query(CardVariantModel).filter_by(card_id=card_id, rarity=rarity).first()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variant {card_id} ({rarity}) not found")

    if rarity == body.new_rarity:
        db.refresh(card)
        return card

    if db.query(CardVariantModel).filter_by(card_id=card_id, rarity=body.new_rarity).first():
        raise HTTPException(status_code=409, detail=f"Variant {card_id} ({body.new_rarity}) already exists")

    now = datetime.now(timezone.utc).isoformat()

    # Find the scraper_rarity that ultimately maps to the current rarity.
    # If a previous remap (A→rarity) exists, update it to (A→new_rarity).
    chained = (
        db.query(CardVariantOverrideModel)
        .filter_by(card_id=card_id, action="remap")
        .filter(CardVariantOverrideModel.target_rarity == rarity)
        .first()
    )
    if chained:
        chained.target_rarity = body.new_rarity
        chained.updated_at = now
    else:
        # Check for an existing override keyed on the current rarity (e.g. a
        # previous delete that we're overriding again).
        existing = (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, scraper_rarity=rarity)
            .first()
        )
        if existing:
            existing.action = "remap"
            existing.target_rarity = body.new_rarity
            existing.updated_at = now
        else:
            db.add(CardVariantOverrideModel(
                card_id=card_id,
                scraper_rarity=rarity,
                action="remap",
                target_rarity=body.new_rarity,
            ))

    # Rename the variant in the DB
    variant.rarity = body.new_rarity

    # Keep original_rarity_string in sync
    rarities = [r.strip() for r in card.original_rarity_string.split("/") if r.strip()]
    if rarity in rarities:
        rarities[rarities.index(rarity)] = body.new_rarity
    card.original_rarity_string = "/".join(rarities)

    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id:path}/variants/{rarity}", status_code=204)
def delete_variant(card_id: str, rarity: str, db: Session = Depends(get_db)):
    """Delete a rarity variant.

    Creates a deletion override so reimport does not recreate the variant from
    scraper data. Cannot delete the last remaining variant.
    """
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

    variant = db.query(CardVariantModel).filter_by(card_id=card_id, rarity=rarity).first()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variant {card_id} ({rarity}) not found")

    if db.query(CardVariantModel).filter_by(card_id=card_id).count() <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only variant of a card")

    now = datetime.now(timezone.utc).isoformat()

    # Determine the scraper_rarity for the override (handle remap chains).
    # If this rarity was previously remapped from a scraper rarity, mark that
    # original scraper rarity as "delete" instead.
    chained = (
        db.query(CardVariantOverrideModel)
        .filter_by(card_id=card_id, action="remap")
        .filter(CardVariantOverrideModel.target_rarity == rarity)
        .first()
    )
    if chained:
        chained.action = "delete"
        chained.target_rarity = None
        chained.updated_at = now
    else:
        existing = (
            db.query(CardVariantOverrideModel)
            .filter_by(card_id=card_id, scraper_rarity=rarity)
            .first()
        )
        if existing:
            existing.action = "delete"
            existing.target_rarity = None
            existing.updated_at = now
        else:
            db.add(CardVariantOverrideModel(
                card_id=card_id,
                scraper_rarity=rarity,
                action="delete",
                target_rarity=None,
            ))

    db.delete(variant)

    # Keep original_rarity_string in sync
    rarities = [r.strip() for r in card.original_rarity_string.split("/") if r.strip() and r.strip() != rarity]
    card.original_rarity_string = "/".join(rarities)

    db.commit()


@router.patch("/{card_id:path}", response_model=CardOut)
def update_card(card_id: str, body: CardUpdate, db: Session = Depends(get_db)):
    """Edit card fields. Creates overrides for import protection (non-manual cards)."""
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

    now = datetime.now(timezone.utc).isoformat()
    update_data = body.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(card, field)
        if old_value != new_value:
            # Log the edit
            db.add(
                CardEditModel(
                    card_id=card_id,
                    field_name=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None,
                )
            )
            setattr(card, field, new_value)

            # Create/update override for non-manual cards
            if not card.is_manual:
                str_value = str(new_value) if new_value is not None else None
                override = (
                    db.query(CardOverrideModel)
                    .filter_by(card_id=card_id, field_name=field)
                    .first()
                )
                if override is None:
                    override = CardOverrideModel(
                        card_id=card_id, field_name=field, value=str_value
                    )
                    db.add(override)
                else:
                    override.value = str_value
                    override.updated_at = now

    db.commit()
    db.refresh(card)
    return card


@router.post("/{card_id:path}/variants", response_model=CardVariantOut, status_code=201)
def add_variant(card_id: str, body: VariantCreate, db: Session = Depends(get_db)):
    """Add a new rarity variant to an existing card."""
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

    existing = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=body.rarity)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Variant {card_id} ({body.rarity}) already exists",
        )

    max_sort = (
        db.query(func.max(CardVariantModel.sort_order))
        .filter_by(card_id=card_id)
        .scalar()
    )
    sort_order = (max_sort or 0) + 1

    variant = CardVariantModel(
        card_id=card_id,
        rarity=body.rarity,
        sort_order=sort_order,
        image_source=None,
        image_path=None,
        scraper_image_path=None,
        owned_count=0,
    )
    db.add(variant)

    # Update original_rarity_string
    existing_rarities = [r.strip() for r in card.original_rarity_string.split("/") if r.strip()]
    if body.rarity not in existing_rarities:
        existing_rarities.append(body.rarity)
        card.original_rarity_string = "/".join(existing_rarities)

    db.commit()
    db.refresh(variant)
    return variant
