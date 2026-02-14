"""Card sets API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardModel, CardSetModel, CardVariantModel
from ..schemas import CardOut, CardSetOut, CardSetWithCardsOut, ProductTypeOut

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
