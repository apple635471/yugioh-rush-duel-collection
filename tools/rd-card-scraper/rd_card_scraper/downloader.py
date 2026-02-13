"""Download card images with rate limiting and caching."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DEFAULT_DELAY = 0.3  # seconds between image downloads


def sanitize_filename(card_id: str) -> str:
    """Convert card ID to a safe filename. e.g. RD/KP01-JP000 -> RD_KP01-JP000.jpg"""
    return card_id.replace("/", "_") + ".jpg"


def download_images(
    cards: list,
    set_id: str,
    base_dir: Path,
    session: requests.Session,
    delay: float = DEFAULT_DELAY,
    force: bool = False,
) -> int:
    """Download card images for a set.

    Args:
        cards: List of Card objects with image_url populated.
        set_id: The set identifier (used for directory naming).
        base_dir: Base data directory.
        session: HTTP session for requests.
        delay: Delay between downloads in seconds.
        force: Re-download even if file exists.

    Returns:
        Number of images downloaded.
    """
    img_dir = base_dir / set_id / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for card in cards:
        if not card.image_url:
            continue

        filename = sanitize_filename(card.card_id)
        filepath = img_dir / filename
        relative_path = f"{set_id}/images/{filename}"

        if filepath.exists() and not force:
            card.image_file = relative_path
            continue

        try:
            time.sleep(delay)
            resp = session.get(card.image_url, timeout=30)
            resp.raise_for_status()

            # Verify it's actually an image
            content_type = resp.headers.get("content-type", "")
            if "image" not in content_type and len(resp.content) < 1000:
                logger.warning(
                    f"Skipping non-image response for {card.card_id}: {content_type}"
                )
                continue

            filepath.write_bytes(resp.content)
            card.image_file = relative_path
            downloaded += 1
            logger.debug(f"Downloaded image for {card.card_id}")

        except Exception as e:
            logger.warning(f"Failed to download image for {card.card_id}: {e}")

    logger.info(f"Downloaded {downloaded} images for set {set_id}")
    return downloaded
