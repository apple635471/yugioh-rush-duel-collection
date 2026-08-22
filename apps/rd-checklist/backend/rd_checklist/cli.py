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
from .services.set_service import (
    delete_card_set,
    find_split_candidates,
    merge_set,
    resplit_set,
)
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

    # merge-set
    mrg = sub.add_parser(
        "merge-set",
        help="Move every card of one set into another and pin them there, so "
        "resplit-set leaves them alone (e.g. 21CC into PROMO)",
    )
    mrg.add_argument("source_id", help="Set ID to empty out, e.g. 21CC")
    mrg.add_argument(
        "--into", dest="target_id", required=True, help="Set ID to move the cards into"
    )

    # resplit-set
    resp = sub.add_parser(
        "resplit-set",
        help="Move a set's cards to the sets their own card numbers point at "
        "(for posts now split into several sets); deletes the source set when "
        "it ends up empty",
    )
    resp.add_argument(
        "set_id",
        nargs="?",
        help="Set ID to re-split, e.g. S254 (omit with --all)",
    )
    resp.add_argument(
        "--all",
        action="store_true",
        dest="all_sets",
        help="Re-split every set that holds cards numbered for another set",
    )
    resp.add_argument(
        "--dry-run", action="store_true", help="Only report what would move"
    )
    resp.add_argument(
        "--keep-source",
        action="store_true",
        help="Keep the source set even when it ends up with no cards",
    )

    # delete-set
    dele = sub.add_parser(
        "delete-set",
        help="Delete a card set and its cards/variants/overrides "
        "(for sets that no longer exist upstream, e.g. after a post is split)",
    )
    dele.add_argument("set_id", help="Set ID to delete, e.g. S254")
    dele.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt"
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

    elif args.command == "merge-set":
        init_db()
        db = SessionLocal()
        try:
            stats = merge_set(db, args.source_id, args.target_id)
            print(
                f"\nMerged {stats['source_id']} → {stats['target_id']}: "
                f"{stats['moved']} card(s)"
            )
            print("  Cards are pinned; resplit-set will leave them in place.")
            if stats["source_deleted"]:
                print(f"  Source set {stats['source_id']} was empty and has been deleted.")
        except (LookupError, ValueError) as exc:
            print(exc)
            sys.exit(1)
        finally:
            db.close()

    elif args.command == "resplit-set":
        if not args.set_id and not args.all_sets:
            print("Give a set ID, or --all to sweep every set.")
            sys.exit(1)
        init_db()
        db = SessionLocal()
        try:
            candidates = find_split_candidates(db)
            targets = sorted(candidates) if args.all_sets else [args.set_id]

            if args.dry_run:
                if not candidates:
                    print("Nothing to split — every card sits in the set its number names.")
                for set_id in targets:
                    counts = candidates.get(set_id, {})
                    if not counts:
                        print(f"{set_id}: nothing to move")
                        continue
                    detail = ", ".join(f"{t} ×{n}" for t, n in sorted(counts.items()))
                    print(f"{set_id}: {detail}")
                sys.exit(0)

            total_moved = 0
            for set_id in targets:
                stats = resplit_set(db, set_id, delete_when_empty=not args.keep_source)
                total_moved += stats["moved"]
                if not stats["moved"]:
                    print(f"{stats['set_id']}: nothing to move")
                    continue
                detail = ", ".join(f"{t} ×{n}" for t, n in stats["by_target"].items())
                print(f"{stats['set_id']}: moved {stats['moved']} → {detail}")
                if stats["created"]:
                    print(f"    created set(s): {', '.join(stats['created'])}")
                if stats["kept_pinned"]:
                    print(f"    left {stats['kept_pinned']} pinned card(s) in place")
                if stats["source_deleted"]:
                    print("    source set was empty and has been deleted")
                elif stats["source_empty_kept"]:
                    print("    source set is empty but was kept (manually created)")
            print(f"\nTotal cards moved: {total_moved}")
        except LookupError as exc:
            print(exc)
            sys.exit(1)
        finally:
            db.close()

    elif args.command == "delete-set":
        init_db()
        db = SessionLocal()
        try:
            from .models import CardModel, CardSetModel

            card_set = db.get(CardSetModel, args.set_id)
            if card_set is None:
                print(f"Card set not found: {args.set_id}")
                sys.exit(1)
            card_count = db.query(CardModel).filter(CardModel.set_id == args.set_id).count()
            print(f"{args.set_id}  {card_set.set_name_zh or card_set.set_name_jp}")
            print(f"  {card_count} cards will be deleted along with their variants and overrides.")
            if not args.yes:
                if input("Type the set ID to confirm: ").strip() != args.set_id:
                    print("Aborted.")
                    sys.exit(1)

            stats = delete_card_set(db, args.set_id)
            print(f"\nDeleted {stats['set_id']}:")
            print(f"  Cards:    {stats['cards']}")
            print(f"  Variants: {stats['variants']}")
            if stats["owned_count"]:
                print(f"  ⚠ owned_count discarded: {stats['owned_count']}")
            if stats["user_uploaded_images"]:
                print(
                    f"  ⚠ {stats['user_uploaded_images']} variant(s) had user-uploaded "
                    "images; the files are left in data/images/user_uploads/"
                )
        finally:
            db.close()


if __name__ == "__main__":
    main()
