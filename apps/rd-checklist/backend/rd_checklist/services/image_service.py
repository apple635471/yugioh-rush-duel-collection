"""Image file management - serving and uploading."""

from __future__ import annotations

import re
from pathlib import Path

import httpx

from ..config import SCRAPER_DATA_DIR, USER_IMAGES_DIR

# Rarity name mapping: app rarity → Konami CDN filename suffix (empty string = no suffix)
# Rarities not listed here (e.g. erroneous "N"/"NR" entries) return None from .get(),
# causing build_konami_image_url to return None and triggering the Rush DB fallback.
_KONAMI_RARITY_MAP: dict[str, str] = {
    "N":    "",      # Normal            → jp001.jpg  (no suffix)
    "R":    "r",     # Rare              → jp001_r.jpg
    "RR":   "rr",    # Rush Rare         → jp001_rr.jpg
    "SR":   "sr",    # Super Rare        → jp001_sr.jpg
    "UR":   "ur",    # Ultra Rare        → jp001_ur.jpg
    "UPR":  "urp",   # Ultra Premium Rare
    "SER":  "se",    # Secret Rare
    "FORR": "for",   # Full Over Rush Rare
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
    suffix = _KONAMI_RARITY_MAP.get(rarity.upper())
    if suffix is None:
        # Unknown rarity - can't build a reliable URL
        return None
    if suffix == "":
        filename = f"{num_part.lower()}.jpg"
    else:
        filename = f"{num_part.lower()}_{suffix}.jpg"
    return (
        f"https://img.konami.com/yugioh/rushduel/products/"
        f"{set_part.lower()}/cards/{filename}"
    )


async def fetch_konami_image(
    card_id: str, rarity: str, set_id: str | None = None
) -> bytes | None:
    """Fetch card image from Konami, trying CDN first then Rush DB fallback.

    Returns raw image bytes if found, None otherwise.
    """
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # 1) Try the direct CDN URL first
        url = build_konami_image_url(card_id, rarity, set_id)
        if url:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                return resp.content

        # 2) Fallback: search Rush DB by card number
        return await _fetch_from_rushdb(client, card_id, rarity)


_CDN_SUFFIXES_FALLBACK = ("", "_sp", "_r", "_rr", "_sr", "_ur", "_urp", "_se", "_for")


async def _fetch_from_rushdb(
    client: httpx.AsyncClient, card_id: str, rarity: str = ""
) -> bytes | None:
    """Fallback: search Rush DB by card number to locate the correct CDN image.

    Strategy:
    1. Search Rush DB with stype=4 to confirm the card exists and get cid/ciid/enc.
    2. Try every known CDN suffix for that card number (higher quality than get_image.action).
    3. If all CDN attempts fail, use get_image.action as the last resort.
    """
    # Extract the card number part: "RD/KP03-JP004" → "KP03-JP004"
    card_num = card_id.split("/", 1)[-1] if "/" in card_id else card_id

    search_url = (
        "https://www.db.yugioh-card.com/rushdb/card_search.action"
        f"?ope=1&request_locale=ja&stype=4&keyword={card_num}&rp=1"
    )
    resp = await client.get(search_url, timeout=15.0, follow_redirects=True)
    if resp.status_code != 200:
        return None

    # Parse cid, ciid, enc from JS: cid=15783&ciid=1&enc=xxxxx
    m = re.search(r"cid=(\d+)&ciid=(\d+)&enc=([A-Za-z0-9_\-]+)", resp.text)
    if not m:
        return None

    cid, ciid, enc = m.group(1), m.group(2), m.group(3)

    # Derive set/num parts from card_num e.g. "KP03-JP004" → "kp03", "jp004"
    if "-" in card_num:
        set_part, num_part = card_num.split("-", 1)
        cdn_base = (
            f"https://img.konami.com/yugioh/rushduel/products/"
            f"{set_part.lower()}/cards/{num_part.lower()}"
        )
        # 把 rarity 對應的尾綴排到第一個，其餘補在後面
        rarity_suffix = _KONAMI_RARITY_MAP.get(rarity.upper())
        if rarity_suffix is not None:
            rarity_cdn = f"_{rarity_suffix}" if rarity_suffix else ""
            ordered = [rarity_cdn] + [s for s in _CDN_SUFFIXES_FALLBACK if s != rarity_cdn]
        else:
            ordered = list(_CDN_SUFFIXES_FALLBACK)

        # Try all known CDN suffixes – prefer CDN over get_image.action for quality
        for suffix in ordered:
            cdn_resp = await client.get(f"{cdn_base}{suffix}.jpg", timeout=10.0)
            if cdn_resp.status_code == 200:
                return cdn_resp.content

    # Last resort: use Rush DB get_image.action (lower quality SAMPLE)
    img_url = (
        f"https://www.db.yugioh-card.com/rushdb/get_image.action"
        f"?type=1&osplang=1&cid={cid}&ciid={ciid}&enc={enc}"
    )
    img_resp = await client.get(img_url, timeout=15.0, follow_redirects=True)
    if img_resp.status_code == 200:
        return img_resp.content
    return None


def _make_upload_filename(card_id: str, rarity: str) -> str:
    """Create a safe filename from card_id and rarity.

    e.g. "RD/KP23-JP000" + "UR" -> "RD_KP23-JP000_UR.jpg"
    """
    safe_id = card_id.replace("/", "_")
    safe_rarity = re.sub(r"[^A-Za-z0-9]", "", rarity)
    return f"{safe_id}_{safe_rarity}.jpg"
