"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path

# Base directories
BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "rd_checklist.db"
USER_IMAGES_DIR = DATA_DIR / "images" / "user_uploads"

# Scraper data directory (can override via env var)
SCRAPER_DATA_DIR = Path(
    os.environ.get(
        "SCRAPER_DATA_DIR",
        str(BACKEND_DIR.parent.parent.parent / "tools" / "rd-card-scraper" / "data"),
    )
)

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
USER_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
