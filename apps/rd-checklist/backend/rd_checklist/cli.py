"""CLI for database initialization and data import."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import SCRAPER_DATA_DIR
from .database import SessionLocal, init_db
from .services.import_service import import_scraper_data
from .services.product_type_migration import migrate_product_types
from .services.rarity_migration import migrate_rarities


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh Rush Duel Checklist - Database Management"
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command")

    # init-db
    sub.add_parser("init-db", help="Create database tables")

    # import
    imp = sub.add_parser("import", help="Import scraper data into database")
    imp.add_argument(
        "--scraper-data",
        type=Path,
        default=SCRAPER_DATA_DIR,
        help=f"Path to scraper data directory (default: {SCRAPER_DATA_DIR})",
    )
    imp.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite (but never overwrites owned_count)",
    )

    # normalize-rarities
    sub.add_parser(
        "normalize-rarities",
        help="Collapse synonym rarities (SRP/PSR→SPR, NRP/PNR→NPR, URP/PUR→UPR) "
        "in existing DB rows and user-uploaded images (idempotent)",
    )

    # reclassify-product-types
    sub.add_parser(
        "reclassify-product-types",
        help="Re-classify existing sets onto the current product types "
        "(retired types → other, tournament_pack → triple_build_pack, "
        "old other → promo; user overrides are kept). Idempotent.",
    )

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init-db":
        init_db()
        print("Database tables created.")

    elif args.command == "import":
        init_db()
        scraper_dir = args.scraper_data
        if not scraper_dir.exists():
            print(f"Error: scraper data directory not found: {scraper_dir}")
            print("Run the scraper first, or specify --scraper-data path.")
            sys.exit(1)

        db = SessionLocal()
        try:
            stats = import_scraper_data(db, scraper_dir, force=args.force)
            print(f"\nImport complete:")
            print(f"  Sets:     {stats['sets_imported']}")
            print(f"  Cards:    {stats['cards_imported']}")
            print(f"  Variants: {stats['variants_created']}")
        finally:
            db.close()

    elif args.command == "normalize-rarities":
        init_db()
        db = SessionLocal()
        try:
            stats = migrate_rarities(db)
            print("\nRarity normalization complete:")
            print(f"  Variants renamed:  {stats['variants_renamed']}")
            print(f"  Variants merged:   {stats['variants_merged']}")
            print(f"  Card strings:      {stats['cards_string_updated']}")
            print(f"  Overrides updated: {stats['overrides_updated']}")
            print(f"  Images renamed:    {stats['images_renamed']}")
            print(f"  Images de-duped:   {stats['images_skipped_conflict']}")
        finally:
            db.close()

    elif args.command == "reclassify-product-types":
        init_db()
        db = SessionLocal()
        try:
            stats = migrate_product_types(db)
            print("\nProduct type re-classification complete:")
            print(f"  Sets changed:        {stats['sets_changed']}")
            print(f"  Overrides rewritten: {stats['overrides_rewritten']}")
            for set_id, before, after in stats["changes"]:
                print(f"    {set_id}: {before} → {after}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
