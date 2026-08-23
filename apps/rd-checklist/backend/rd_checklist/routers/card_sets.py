"""Card sets API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..product_types import label_for
from ..models import (
    CardModel,
    CardSetImageModel,
    CardSetModel,
    CardSetOverrideModel,
    CardVariantModel,
)
from ..schemas import (
    CardOut,
    CardSetCreate,
    CardSetOut,
    CardSetOverrideOut,
    CardSetUpdate,
    CardSetImageOut,
    CardSetWithCardsOut,
    ProductTypeOut,
    SetListApplyOut,
    SetListApplyRequest,
    SetListCompareOut,
    SetListCompareRequest,
)
from ..services.card_service import delete_card_and_variants
from ..services.set_image_service import refresh_set_images
from ..services.set_list_compare import compare_with_yugipedia
from ..services.variant_service import (
    delete_variant as delete_variant_row,
    remap_variant as remap_variant_row,
)
from ..services.yugipedia import YugipediaError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/card-sets", tags=["card-sets"])


@router.get("/product-types", response_model=list[ProductTypeOut])
def list_product_types(db: Session = Depends(get_db)):
    """List all product types with set counts."""
    rows = (
        db.query(CardSetModel.product_type, func.count(CardSetModel.set_id))
        .group_by(CardSetModel.product_type)
        .all()
    )
    result = []
    for pt, count in rows:
        name_en, name_zh = label_for(pt)
        result.append(
            ProductTypeOut(
                product_type=pt,
                display_name=name_en,
                display_name_zh=name_zh,
                set_count=count,
            )
        )
    return result


@router.get("", response_model=list[CardSetOut])
def list_card_sets(
    product_type: str | None = None,
    db: Session = Depends(get_db),
):
    """List card sets, optionally filtered by product type."""
    q = db.query(CardSetModel)
    if product_type:
        q = q.filter(CardSetModel.product_type == product_type)
    # release_date is stored as "YYYY/M/D" (months/days may be single-digit).
    # Build a zero-padded "YYYYMM" key so numeric order is correct (e.g. "202511" > "202508").
    # Sets without a date sort last, then by set_id.
    q = q.order_by(
        text(
            "CASE WHEN release_date IS NULL THEN '0' "
            "ELSE printf('%04d%02d',"
            "  CAST(substr(release_date,1,4) AS INTEGER),"
            "  CAST(substr(release_date,6,2) AS INTEGER)"
            ") END DESC"
        ),
        CardSetModel.set_id,
    )
    return q.all()


@router.post("", response_model=CardSetOut, status_code=201)
def create_card_set(body: CardSetCreate, db: Session = Depends(get_db)):
    """Manually create a new card set (is_manual=True, import will not overwrite)."""
    existing = db.query(CardSetModel).filter_by(set_id=body.set_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Set {body.set_id} already exists")

    now = datetime.now(timezone.utc).isoformat()
    card_set = CardSetModel(
        set_id=body.set_id,
        set_name_jp=body.set_name_jp,
        set_name_zh=body.set_name_zh,
        product_type=body.product_type,
        release_date=body.release_date,
        post_url="",
        total_cards=0,
        is_manual=True,
        created_at=now,
        updated_at=now,
    )
    db.add(card_set)
    db.commit()
    db.refresh(card_set)
    return card_set


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
        yugipedia_url=card_set.yugipedia_url,
        total_cards=card_set.total_cards,
        rarity_distribution=card_set.rarity_distribution,
        is_manual=card_set.is_manual,
        cards=[CardOut.model_validate(c) for c in cards],
    )


# ── Overridable fields ──
_OVERRIDABLE_FIELDS = {
    "set_name_jp",
    "set_name_zh",
    "product_type",
    "release_date",
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

    # yugipedia_url is the user's own note about where the set lives, not
    # something an import could overwrite — so it is stored on the row without
    # an override. Setting it also pulls the set's gallery images, which is the
    # whole point of remembering it.
    if "yugipedia_url" in updates:
        new_url = (updates["yugipedia_url"] or "").strip() or None
        changed = new_url != card_set.yugipedia_url
        card_set.yugipedia_url = new_url
        if changed and new_url:
            db.commit()
            try:
                refresh_set_images(db, set_id, new_url)
            except (YugipediaError, httpx.HTTPError) as exc:
                # The URL is saved either way; the pictures can be retried.
                logger.warning("%s: gallery fetch failed: %s", set_id, exc)

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


@router.post("/{set_id}/compare", response_model=SetListCompareOut)
def compare_set_list(
    set_id: str, body: SetListCompareRequest, db: Session = Depends(get_db)
):
    """Check this set against its card list on yugipedia.

    Reports printings the list has that we don't, and ones we have that it
    doesn't. Read-only — applying the differences is a separate call.
    """
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    url = (body.url or "").strip() or card_set.yugipedia_url
    if not url:
        raise HTTPException(
            status_code=400,
            detail="這個卡組還沒有 yugipedia 頁面網址，請在下方貼上一次，之後就會記住",
        )

    try:
        result = compare_with_yugipedia(db, set_id, url)
    except YugipediaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"讀取 yugipedia 失敗：{exc}"
        ) from exc

    # The URL just proved itself, so remember it — and pick up the set's
    # gallery pictures while we are here.
    if url != card_set.yugipedia_url:
        card_set.yugipedia_url = url
        db.commit()
        try:
            refresh_set_images(db, set_id, url)
        except (YugipediaError, httpx.HTTPError) as exc:
            logger.warning("%s: gallery fetch failed: %s", set_id, exc)

    return result


@router.post("/{set_id}/compare/apply", response_model=SetListApplyOut)
def apply_set_list_diff(
    set_id: str, body: SetListApplyRequest, db: Session = Depends(get_db)
):
    """Create the missing printings and delete the extra ones.

    Creating a printing of a card we already hold adds a variant; creating one
    for an unknown card creates the card too, with just the id, Japanese name
    and rarity — the rest is for the scraper or the user to fill in.

    Deleting the last printing of a card deletes the card, since a card with no
    printings is not something the checklist can show.
    """
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if not card_set:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

    errors: list[str] = []
    cards_created = variants_created = variants_deleted = cards_deleted = 0
    variants_remapped = 0

    # Remaps first: they free the old rarity and fill the new one, so a later
    # create/delete in the same batch sees the corrected state.
    for remap in body.remap:
        try:
            if remap_variant_row(
                db,
                remap.card_id,
                remap.from_rarity,
                remap.to_rarity,
                remap.from_is_alternate_art,
                remap.to_is_alternate_art,
            ):
                variants_remapped += 1
            else:
                errors.append(
                    f"{remap.card_id} {remap.from_rarity} → {remap.to_rarity}: 無法改（來源不存在或目標已存在）"
                )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{remap.card_id} {remap.from_rarity} → {remap.to_rarity}: {exc}")

    db.flush()

    for item in body.create:
        try:
            card = db.query(CardModel).filter_by(card_id=item.card_id).first()
            if card is None:
                card = CardModel(
                    card_id=item.card_id,
                    set_id=set_id,
                    name_jp=item.name_jp,
                    is_manual=True,
                    original_rarity_string=item.rarity,
                )
                db.add(card)
                db.flush()
                cards_created += 1
            elif card.set_id != set_id:
                errors.append(f"{item.card_id} 屬於 {card.set_id}，未建立")
                continue

            exists = (
                db.query(CardVariantModel)
                .filter_by(
                    card_id=item.card_id,
                    rarity=item.rarity,
                    is_alternate_art=item.is_alternate_art,
                )
                .first()
            )
            if exists:
                continue

            sort_order = (
                db.query(func.count(CardVariantModel.id))
                .filter_by(card_id=item.card_id)
                .scalar()
                or 0
            )
            db.add(
                CardVariantModel(
                    card_id=item.card_id,
                    rarity=item.rarity,
                    is_alternate_art=item.is_alternate_art,
                    sort_order=sort_order,
                    owned_count=0,
                )
            )
            variants_created += 1
        except Exception as exc:  # noqa: BLE001 - report and carry on
            errors.append(f"{item.card_id} {item.rarity}: {exc}")

    db.flush()

    for item in body.delete:
        try:
            variant = (
                db.query(CardVariantModel)
                .filter_by(
                    card_id=item.card_id,
                    rarity=item.rarity,
                    is_alternate_art=item.is_alternate_art,
                )
                .first()
            )
            if variant is None:
                continue

            remaining = (
                db.query(CardVariantModel).filter_by(card_id=item.card_id).count()
            )
            if remaining <= 1:
                deleted = delete_card_and_variants(db, item.card_id)
                variants_deleted += deleted
                cards_deleted += 1
            elif delete_variant_row(
                db, item.card_id, item.rarity, item.is_alternate_art
            ):
                variants_deleted += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{item.card_id} {item.rarity}: {exc}")

    db.commit()
    return SetListApplyOut(
        variants_remapped=variants_remapped,
        cards_created=cards_created,
        variants_created=variants_created,
        variants_deleted=variants_deleted,
        cards_deleted=cards_deleted,
        errors=errors,
    )


@router.get("/{set_id}/images", response_model=list[CardSetImageOut])
def list_set_images(set_id: str, db: Session = Depends(get_db)):
    """Pictures of the set, in gallery order."""
    return (
        db.query(CardSetImageModel)
        .filter_by(set_id=set_id)
        .order_by(CardSetImageModel.sort_order)
        .all()
    )


@router.post("/{set_id}/images/refresh", response_model=list[CardSetImageOut])
def refresh_images(set_id: str, db: Session = Depends(get_db)):
    """Re-read the set's yugipedia gallery and download anything new."""
    try:
        return refresh_set_images(db, set_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except YugipediaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"讀取 yugipedia 失敗：{exc}") from exc
