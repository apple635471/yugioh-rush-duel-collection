"""Pictures of a set — pack shots and promotional posters from yugipedia.

Downloaded rather than hotlinked: the app should not lean on someone else's
server for every page view, and the files are small and few (one or two per
set).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from ..config import SET_IMAGES_DIR
from ..models import CardSetImageModel, CardSetModel
from .yugipedia import USER_AGENT, YugipediaError, fetch_set_gallery

logger = logging.getLogger(__name__)

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _filename_from_url(url: str) -> str:
    return _SAFE_NAME_RE.sub("_", url.rsplit("/", 1)[-1]) or "image"


def image_path(relative: str) -> Path | None:
    """Absolute path of a stored set image, or None when it is gone."""
    path = SET_IMAGES_DIR / relative
    return path if path.is_file() else None


def refresh_set_images(db: Session, set_id: str, url: str | None = None) -> list[CardSetImageModel]:
    """Re-read a set's gallery and store what is missing.

    Existing rows are matched on the source URL, so running this again after a
    set gains a poster only downloads the new one. Rows whose picture is no
    longer in the gallery are dropped, along with the file.
    """
    card_set = db.query(CardSetModel).filter_by(set_id=set_id).first()
    if card_set is None:
        raise LookupError(f"Card set not found: {set_id}")

    page_url = url or card_set.yugipedia_url
    if not page_url:
        raise YugipediaError("這個卡組還沒有填 yugipedia 頁面網址")

    gallery = fetch_set_gallery(page_url)
    existing = {
        img.source_url: img
        for img in db.query(CardSetImageModel).filter_by(set_id=set_id).all()
    }

    target_dir = SET_IMAGES_DIR / set_id
    target_dir.mkdir(parents=True, exist_ok=True)

    kept: list[CardSetImageModel] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True) as client:
        for order, item in enumerate(gallery):
            row = existing.pop(item.url, None)
            relative = f"{set_id}/{_filename_from_url(item.url)}"

            if row is None or not image_path(relative):
                try:
                    resp = client.get(item.url)
                    resp.raise_for_status()
                    (SET_IMAGES_DIR / relative).write_bytes(resp.content)
                except httpx.HTTPError as exc:
                    logger.warning("Could not download %s: %s", item.url, exc)
                    continue

            if row is None:
                row = CardSetImageModel(set_id=set_id, source_url=item.url)
                db.add(row)
            row.title = item.title
            row.file_path = relative
            row.width = item.width
            row.height = item.height
            row.sort_order = order
            kept.append(row)

    # Anything still in `existing` is no longer in the gallery.
    for stale in existing.values():
        path = image_path(stale.file_path)
        if path:
            path.unlink(missing_ok=True)
        db.delete(stale)

    db.commit()
    logger.info("%s: %d gallery image(s)", set_id, len(kept))
    return (
        db.query(CardSetImageModel)
        .filter_by(set_id=set_id)
        .order_by(CardSetImageModel.sort_order)
        .all()
    )
