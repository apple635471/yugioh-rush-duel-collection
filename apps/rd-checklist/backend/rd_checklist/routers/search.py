"""Search API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardModel, CardVariantModel
from ..schemas import CardOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[CardOut])
def search_cards(
    q: str | None = Query(None, description="Search query (name, card_id)"),
    card_type: str | None = Query(None, description="Filter by card type"),
    attribute: str | None = Query(None, description="Filter by attribute"),
    level: int | None = Query(None, description="Filter by level"),
    set_id: str | None = Query(None, description="Filter by set"),
    rarity: str | None = Query(None, description="Filter by rarity"),
    owned: str | None = Query(None, description="all, owned, or missing"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Search cards with filters."""
    query = db.query(CardModel)

    # Text search across name_jp, name_zh, card_id
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                CardModel.name_jp.ilike(pattern),
                CardModel.name_zh.ilike(pattern),
                CardModel.card_id.ilike(pattern),
            )
        )

    if card_type:
        # Use LIKE so compound types are searchable by component,
        # e.g. "儀式" matches both "儀式怪獸" and "儀式/效果怪獸"
        query = query.filter(CardModel.card_type.ilike(f"%{card_type}%"))

    if attribute:
        query = query.filter(CardModel.attribute == attribute)

    if level is not None:
        query = query.filter(CardModel.level == level)

    if set_id:
        query = query.filter(CardModel.set_id == set_id)

    # Rarity filter: check card_variants
    if rarity:
        card_ids_with_rarity = (
            db.query(CardVariantModel.card_id)
            .filter(CardVariantModel.rarity == rarity)
            .subquery()
        )
        query = query.filter(CardModel.card_id.in_(card_ids_with_rarity.select()))

    # Ownership filter
    if owned in ("owned", "missing"):
        if owned == "owned":
            card_ids_owned = (
                db.query(CardVariantModel.card_id)
                .filter(CardVariantModel.owned_count > 0)
                .distinct()
                .subquery()
            )
            query = query.filter(CardModel.card_id.in_(card_ids_owned.select()))
        elif owned == "missing":
            # Cards where ALL variants have owned_count == 0
            card_ids_owned = (
                db.query(CardVariantModel.card_id)
                .filter(CardVariantModel.owned_count > 0)
                .distinct()
                .subquery()
            )
            query = query.filter(~CardModel.card_id.in_(card_ids_owned.select()))

    query = query.order_by(CardModel.card_id).offset(offset).limit(limit)
    return query.all()
