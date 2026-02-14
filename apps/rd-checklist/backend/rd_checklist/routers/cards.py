"""Card detail and editing API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardEditModel, CardModel
from ..schemas import CardOut, CardUpdate

router = APIRouter(prefix="/api/cards", tags=["cards"])


@router.get("/{card_id:path}", response_model=CardOut)
def get_card(card_id: str, db: Session = Depends(get_db)):
    """Get a card with all its variants."""
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
    return card


@router.patch("/{card_id:path}", response_model=CardOut)
def update_card(card_id: str, body: CardUpdate, db: Session = Depends(get_db)):
    """Edit card fields (name, effect, etc.)."""
    card = db.query(CardModel).filter_by(card_id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

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

    db.commit()
    db.refresh(card)
    return card
