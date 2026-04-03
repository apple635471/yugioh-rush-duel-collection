"""Ownership tracking API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardVariantModel
from ..utils import parse_rarity_key
from ..schemas import (
    CardVariantOut,
    OwnershipBatchUpdate,
    OwnershipStatsOut,
    OwnershipUpdate,
)

router = APIRouter(prefix="/api/ownership", tags=["ownership"])


@router.patch("/{card_id:path}/{rarity}", response_model=CardVariantOut)
def update_ownership(
    card_id: str,
    rarity: str,
    body: OwnershipUpdate,
    db: Session = Depends(get_db),
):
    """Update owned_count for a specific card variant.

    rarity is a rarity key: "SR" for normal, "SR-alt" for alternate art.
    """
    actual_rarity, is_alt = parse_rarity_key(rarity)
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=actual_rarity, is_alternate_art=is_alt)
        .first()
    )
    if not variant:
        raise HTTPException(
            status_code=404,
            detail=f"Variant {card_id} ({rarity}) not found",
        )

    variant.owned_count = max(0, body.owned_count)
    db.commit()
    db.refresh(variant)
    return variant


@router.patch("/batch", response_model=list[CardVariantOut])
def batch_update_ownership(
    body: OwnershipBatchUpdate,
    db: Session = Depends(get_db),
):
    """Batch update ownership for multiple variants."""
    results = []
    for item in body.updates:
        actual_rarity, is_alt = parse_rarity_key(item.rarity)
        variant = (
            db.query(CardVariantModel)
            .filter_by(card_id=item.card_id, rarity=actual_rarity, is_alternate_art=is_alt)
            .first()
        )
        if variant:
            variant.owned_count = max(0, item.owned_count)
            results.append(variant)
    db.commit()
    for v in results:
        db.refresh(v)
    return results


@router.get("/stats", response_model=OwnershipStatsOut)
def get_stats(db: Session = Depends(get_db)):
    """Get overall collection statistics."""
    total = db.query(CardVariantModel).count()
    owned = db.query(CardVariantModel).filter(CardVariantModel.owned_count > 0).count()
    copies = (
        db.query(func.sum(CardVariantModel.owned_count)).scalar() or 0
    )
    return OwnershipStatsOut(
        total_variants=total,
        owned_variants=owned,
        total_owned_copies=copies,
    )


@router.get("/stats-bulk", response_model=dict[str, OwnershipStatsOut])
def get_all_set_stats(db: Session = Depends(get_db)):
    """Get collection statistics for every set in one query."""
    from ..models import CardModel
    from sqlalchemy import case as sa_case

    rows = (
        db.query(
            CardModel.set_id,
            func.count(CardVariantModel.id).label("total"),
            func.sum(sa_case((CardVariantModel.owned_count > 0, 1), else_=0)).label("owned"),
            func.sum(CardVariantModel.owned_count).label("copies"),
        )
        .join(CardVariantModel, CardVariantModel.card_id == CardModel.card_id)
        .group_by(CardModel.set_id)
        .all()
    )
    return {
        row.set_id: OwnershipStatsOut(
            total_variants=row.total,
            owned_variants=row.owned,
            total_owned_copies=int(row.copies or 0),
        )
        for row in rows
    }


@router.get("/stats/{set_id}", response_model=OwnershipStatsOut)
def get_set_stats(set_id: str, db: Session = Depends(get_db)):
    """Get collection statistics for a specific set."""
    from ..models import CardModel

    card_ids = (
        db.query(CardModel.card_id).filter_by(set_id=set_id).subquery()
    )
    q = db.query(CardVariantModel).filter(
        CardVariantModel.card_id.in_(card_ids.select())
    )
    total = q.count()
    owned = q.filter(CardVariantModel.owned_count > 0).count()
    copies = (
        db.query(func.sum(CardVariantModel.owned_count))
        .filter(CardVariantModel.card_id.in_(card_ids.select()))
        .scalar()
        or 0
    )
    return OwnershipStatsOut(
        total_variants=total,
        owned_variants=owned,
        total_owned_copies=copies,
    )
