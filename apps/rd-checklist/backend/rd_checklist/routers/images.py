"""Image serving and upload API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardVariantModel
from ..schemas import CardVariantOut
from ..services.image_service import (
    delete_user_image,
    get_image_path,
    get_user_image_path,
    save_user_image,
)

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/{set_id}/{filename}")
def serve_image(set_id: str, filename: str):
    """Serve a card image from scraper data."""
    path = get_image_path(set_id, filename)
    if not path:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/card/{card_id:path}/{rarity}")
def serve_card_image(
    card_id: str,
    rarity: str,
    db: Session = Depends(get_db),
):
    """Serve the image for a specific card variant.

    Checks user uploads first, falls back to scraper image.
    """
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity)
        .first()
    )
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Try user upload first
    if variant.image_source == "user_upload":
        user_path = get_user_image_path(card_id, rarity)
        if user_path:
            return _no_cache_file_response(user_path)

    # Fall back to scraper image
    if variant.image_path:
        # image_path is like "KP23/images/RD_KP23-JP000.jpg"
        parts = variant.image_path.split("/")
        if len(parts) >= 3:
            set_id = parts[0]
            filename = parts[-1]
            path = get_image_path(set_id, filename)
            if path:
                return FileResponse(path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Image not found")


def _no_cache_file_response(path) -> Response:
    """Return an image file with no-cache headers to prevent stale browser cache."""
    content = path.read_bytes()
    return Response(
        content=content,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.post("/card/{card_id:path}/{rarity}/upload", response_model=CardVariantOut)
async def upload_image(
    card_id: str,
    rarity: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a replacement image for a card variant."""
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity)
        .first()
    )
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    content = await file.read()
    rel_path = save_user_image(card_id, rarity, content)

    # Preserve scraper path before overwriting (one-time backfill for old data)
    if not variant.scraper_image_path and variant.image_source == "scraper" and variant.image_path:
        variant.scraper_image_path = variant.image_path

    variant.image_source = "user_upload"
    variant.image_path = rel_path
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/card/{card_id:path}/{rarity}/upload", response_model=CardVariantOut)
def revert_image(
    card_id: str,
    rarity: str,
    db: Session = Depends(get_db),
):
    """Revert a card variant's image to the original scraper image."""
    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity)
        .first()
    )
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    delete_user_image(card_id, rarity)

    # Restore from the preserved scraper_image_path (always reliable)
    original_path = variant.scraper_image_path
    variant.image_source = "scraper" if original_path else None
    variant.image_path = original_path
    db.commit()
    db.refresh(variant)
    return variant
