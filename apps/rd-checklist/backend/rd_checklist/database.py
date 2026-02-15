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
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                # Column already exists — ignore
                conn.rollback()
