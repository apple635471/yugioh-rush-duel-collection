"""Image file management - serving and uploading."""

from __future__ import annotations

import re
from pathlib import Path

from ..config import SCRAPER_DATA_DIR, USER_IMAGES_DIR


def get_image_path(
    set_id: str, filename: str
) -> Path | None:
    """Get the filesystem path for a scraper card image.

    Looks in: {SCRAPER_DATA_DIR}/{set_id}/images/{filename}
    """
    path = SCRAPER_DATA_DIR / set_id / "images" / filename
    if path.exists() and path.is_file():
        return path
    return None


def get_user_image_path(card_id: str, rarity: str) -> Path | None:
    """Get the filesystem path for a user-uploaded image."""
    filename = _make_upload_filename(card_id, rarity)
    path = USER_IMAGES_DIR / filename
    if path.exists() and path.is_file():
        return path
    return None


def save_user_image(card_id: str, rarity: str, content: bytes) -> str:
    """Save a user-uploaded image. Returns the relative path."""
    filename = _make_upload_filename(card_id, rarity)
    path = USER_IMAGES_DIR / filename
    path.write_bytes(content)
    return f"user_uploads/{filename}"


def delete_user_image(card_id: str, rarity: str) -> bool:
    """Delete a user-uploaded image. Returns True if deleted."""
    filename = _make_upload_filename(card_id, rarity)
    path = USER_IMAGES_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False


def _make_upload_filename(card_id: str, rarity: str) -> str:
    """Create a safe filename from card_id and rarity.

    e.g. "RD/KP23-JP000" + "UR" -> "RD_KP23-JP000_UR.jpg"
    """
    safe_id = card_id.replace("/", "_")
    safe_rarity = re.sub(r"[^A-Za-z0-9]", "", rarity)
    return f"{safe_id}_{safe_rarity}.jpg"
