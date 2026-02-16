"""Card sets API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardModel, CardSetModel, CardSetOverrideModel, CardVariantModel
from ..schemas import (
    CardOut,
    CardSetOut,
    CardSetOverrideOut,
    CardSetUpdate,
    CardSetWithCardsOut,
    ProductTypeOut,
)

router = APIRouter(prefix="/api/card-sets", tags=["card-sets"])

PRODUCT_TYPE_LABELS = {
    "booster": "補充包 Booster Pack",
    "starter": "預組 Starter Deck",
    "structure_deck": "構築包 Structure Deck",
    "character_pack": "角色包 Character Pack",
    "go_rush_character": "Go Rush 角色包",
    "go_rush_deck": "Go Rush 預組",
    "battle_pack": "戰鬥包 Battle Pack",
    "maximum_pack": "Maximum 包",
    "extra_pack": "Extra 包",
    "legend_pack": "傳說包 Legend Pack",
    "vs_pack": "VS 包",
    "tournament_pack": "大會包 Tournament Pack",
    "advanced_pack": "進階包 Advanced Pack",
    "over_rush_pack": "Over Rush 包",
    "unknown": "其他",
}


@router.get("/product-types", response_model=list[ProductTypeOut])
def list_product_types(db: Session = Depends(get_db)):
    """List all product types with set counts."""
    rows = (
        db.query(CardSetModel.product_type, func.count(CardSetModel.set_id))
        .group_by(CardSetModel.product_type)
        .all()
    )
    return [
        ProductTypeOut(
            product_type=pt,
            display_name=PRODUCT_TYPE_LABELS.get(pt, pt),
            set_count=count,
        )
        for pt, count in rows
    ]


@router.get("", response_model=list[CardSetOut])
def list_card_sets(
    product_type: str | None = None,
    db: Session = Depends(get_db),
):
    """List card sets, optionally filtered by product type."""
    q = db.query(CardSetModel)
    if product_type:
        q = q.filter(CardSetModel.product_type == product_type)
    q = q.order_by(CardSetModel.release_date.desc().nullslast(), CardSetModel.set_id)
    return q.all()


@router.get("/{set_id}", response_model=CardSetWithCardsOut)
def get_card_set(set_id: str, db: Session = Depends(get_db)):
    """Get a card set with all its cards and variants."""
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    cards = (
        db.query(CardModel)
        .filter_by(set_id=set_id)
        .order_by(CardModel.card_id)
        .all()
    )

    return CardSetWithCardsOut(
        set_id=card_set.set_id,
        set_name_jp=card_set.set_name_jp,
        set_name_zh=card_set.set_name_zh,
        product_type=card_set.product_type,
        release_date=card_set.release_date,
        post_url=card_set.post_url,
        total_cards=card_set.total_cards,
        rarity_distribution=card_set.rarity_distribution,
        cards=[CardOut.model_validate(c) for c in cards],
    )


# ── Overridable fields ──
_OVERRIDABLE_FIELDS = {
    "set_name_jp",
    "set_name_zh",
    "product_type",
    "release_date",
    "total_cards",
    "rarity_distribution",
}


@router.patch("/{set_id}", response_model=CardSetOut)
def update_card_set(
    set_id: str,
    body: CardSetUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a card set and persist overrides.

    Each provided field is:
    1. Written to card_sets immediately.
    2. Saved as a card_set_override so future imports won't overwrite it.
    """
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = body.model_dump(exclude_unset=True)

    for field, new_value in updates.items():
        if field not in _OVERRIDABLE_FIELDS:
            continue

        # Convert to string for storage in override table
        str_value = str(new_value) if new_value is not None else None

        # 1) Apply to card_set row
        setattr(card_set, field, new_value)

        # 2) Upsert override
        override = (
            db.query(CardSetOverrideModel)
            .filter_by(set_id=set_id, field_name=field)
            .first()
        )
        if override is None:
            override = CardSetOverrideModel(
                set_id=set_id, field_name=field, value=str_value
            )
            db.add(override)
        else:
            override.value = str_value
            override.updated_at = now

    card_set.updated_at = now
    db.commit()
    db.refresh(card_set)
    return card_set


@router.get("/{set_id}/overrides", response_model=list[CardSetOverrideOut])
def list_overrides(set_id: str, db: Session = Depends(get_db)):
    """List all user overrides for a card set."""
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    overrides = (
        db.query(CardSetOverrideModel)
        .filter_by(set_id=set_id)
        .order_by(CardSetOverrideModel.field_name)
        .all()
    )
    return [
        CardSetOverrideOut(
            set_id=o.set_id,
            field_name=o.field_name,
            value=o.value,
            updated_at=o.updated_at,
        )
        for o in overrides
    ]


@router.delete("/{set_id}/overrides/{field_name}")
def delete_override(
    set_id: str,
    field_name: str,
    db: Session = Depends(get_db),
):
    """Delete a single override, reverting the field to scraper value on next import."""
    override = (
        db.query(CardSetOverrideModel)
        .filter_by(set_id=set_id, field_name=field_name)
        .first()
    )
    if not override:
        raise HTTPException(
            status_code=404,
            detail=f"No override for {set_id}.{field_name}",
        )
    db.delete(override)
    db.commit()
    return {"detail": f"Override {set_id}.{field_name} deleted. Will revert on next import."}
