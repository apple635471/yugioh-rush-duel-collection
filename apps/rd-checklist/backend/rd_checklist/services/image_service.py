"""Image file management - serving and uploading."""

from __future__ import annotations

import re
from pathlib import Path

import httpx

from ..config import SCRAPER_DATA_DIR, USER_IMAGES_DIR

# Rarity name mapping: app rarity → Konami CDN suffix
_KONAMI_RARITY_MAP: dict[str, str] = {
    "UPR": "urp",
    "SER": "se",
    "FORR": "for",
}


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


def build_konami_image_url(
    card_id: str, rarity: str, set_id: str | None = None
) -> str | None:
    """Build the Konami CDN URL for a card image.

    card_id can be the full form "RD/5TH1-JP005" or short form "JP005"
    (in which case set_id like "5TH1" is required).
    """
    if "/" in card_id:
        after_slash = card_id.split("/", 1)[1]  # "5TH1-JP005"
    elif set_id:
        after_slash = f"{set_id}-{card_id}"  # "5TH1-JP005"
    else:
        return None

    if "-" not in after_slash:
        return None

    set_part, num_part = after_slash.split("-", 1)  # "5TH1", "JP005"
    konami_rarity = _KONAMI_RARITY_MAP.get(rarity.upper(), rarity.lower())
    return (
        f"https://img.konami.com/yugioh/rushduel/products/"
        f"{set_part.lower()}/cards/{num_part.lower()}_{konami_rarity}.jpg"
    )


async def fetch_konami_image(
    card_id: str, rarity: str, set_id: str | None = None
) -> bytes | None:
    """Fetch card image from Konami CDN.

    Returns raw image bytes if found (HTTP 200), None otherwise.
    """
    url = build_konami_image_url(card_id, rarity, set_id)
    if not url:
        return None
    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.get(url, timeout=10.0)
        if resp.status_code == 200:
            return resp.content
    return None


def _make_upload_filename(card_id: str, rarity: str) -> str:
    """Create a safe filename from card_id and rarity.

    e.g. "RD/KP23-JP000" + "UR" -> "RD_KP23-JP000_UR.jpg"
    """
    safe_id = card_id.replace("/", "_")
    safe_rarity = re.sub(r"[^A-Za-z0-9]", "", rarity)
    return f"{safe_id}_{safe_rarity}.jpg"
