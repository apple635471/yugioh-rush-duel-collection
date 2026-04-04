"""SQLite database setup and session management."""

from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session, auto-closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and add any missing columns."""
    from .models import Base
    Base.metadata.create_all(bind=engine)

    # Migrate: add columns that may not exist in older databases.
    # ALTER TABLE ADD COLUMN is a no-op if the column already exists
    # (SQLite raises "duplicate column name" which we catch and ignore).
    _migrate_add_columns()


def _migrate_add_columns():
    """Add new columns to existing tables (safe to run repeatedly)."""
    migrations = [
        "ALTER TABLE cards ADD COLUMN summon_condition TEXT",
        "ALTER TABLE cards ADD COLUMN continuous_effect TEXT",
        "ALTER TABLE card_variants ADD COLUMN scraper_image_path TEXT",
        "ALTER TABLE cards ADD COLUMN is_manual BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE cards ADD COLUMN description TEXT",
        "ALTER TABLE cards ADD COLUMN maximum_atk TEXT",
        "ALTER TABLE card_sets ADD COLUMN is_manual BOOLEAN NOT NULL DEFAULT 0",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                # Column already exists — ignore
                conn.rollback()

        # Backfill: copy image_path → scraper_image_path where not yet set
        try:
            conn.execute(text(
                "UPDATE card_variants SET scraper_image_path = image_path "
                "WHERE scraper_image_path IS NULL AND image_source = 'scraper' AND image_path IS NOT NULL"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        # Migration: add is_alternate_art column + change unique constraint.
        # SQLite cannot DROP CONSTRAINT, so we recreate the table when needed.
        _migrate_card_variants_alt_art(conn)


def _migrate_card_variants_alt_art(conn) -> None:
    """Recreate card_variants with is_alternate_art column + new unique constraint.

    Only runs when the column is absent (i.e. on first upgrade from older DBs).
    Safe to call repeatedly — the check is based on the live table DDL.
    """
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='card_variants'")
    ).fetchone()
    if row is None:
        # Table doesn't exist yet; create_all will handle it.
        return
    if "is_alternate_art" in row[0]:
        # Already migrated.
        return

    # Recreate with the new schema (SQLite requires table rename approach).
    stmts = [
        "PRAGMA foreign_keys=OFF",
        """
        CREATE TABLE card_variants_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id VARCHAR NOT NULL,
            rarity VARCHAR NOT NULL,
            is_alternate_art BOOLEAN NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            image_source VARCHAR,
            image_path VARCHAR,
            scraper_image_path VARCHAR,
            owned_count INTEGER NOT NULL DEFAULT 0,
            created_at VARCHAR NOT NULL DEFAULT (datetime('now')),
            updated_at VARCHAR NOT NULL DEFAULT (datetime('now')),
            UNIQUE (card_id, rarity, is_alternate_art),
            FOREIGN KEY (card_id) REFERENCES cards (card_id)
        )
        """,
        """
        INSERT INTO card_variants_new
            (id, card_id, rarity, is_alternate_art, sort_order,
             image_source, image_path, scraper_image_path,
             owned_count, created_at, updated_at)
        SELECT id, card_id, rarity, 0, sort_order,
               image_source, image_path, scraper_image_path,
               owned_count, created_at, updated_at
        FROM card_variants
        """,
        "DROP TABLE card_variants",
        "ALTER TABLE card_variants_new RENAME TO card_variants",
        "CREATE INDEX IF NOT EXISTS ix_card_variants_card_id ON card_variants (card_id)",
        "PRAGMA foreign_key_check",
        "PRAGMA foreign_keys=ON",
    ]
    try:
        for stmt in stmts:
            conn.execute(text(stmt))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
