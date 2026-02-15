"""Command-line interface for the Rush Duel card scraper."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .scraper import RushDuelScraper


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh Rush Duel card scraper for ntucgm.blogspot.com"
    )
    parser.add_argument(
        "-d", "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory to store scraped data (default: ./data)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip downloading card images",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scrape even if content hasn't changed",
    )
    parser.add_argument(
        "--since",
        type=int,
        default=None,
        metavar="YEAR",
        help="Only discover posts from this year onwards (default: 2020)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scrape-all: full scrape
    subparsers.add_parser(
        "scrape-all",
        help="Scrape all discovered Rush Duel card list posts",
    )

    # update: incremental update
    subparsers.add_parser(
        "update",
        help="Only scrape new or changed posts (incremental)",
    )

    # scrape-url: scrape a specific URL
    url_parser = subparsers.add_parser(
        "scrape-url",
        help="Scrape a specific blog post URL",
    )
    url_parser.add_argument("url", help="The blog post URL to scrape")

    # discover: list discovered post URLs
    subparsers.add_parser(
        "discover",
        help="Discover and list Rush Duel card list post URLs",
    )

    # check: check for updates
    subparsers.add_parser(
        "check",
        help="Check for new or updated posts without scraping",
    )

    # summary: show current data summary
    subparsers.add_parser(
        "summary",
        help="Show summary of currently scraped data",
    )

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Build optional kwargs for discovery
    discover_kwargs: dict = {}
    if args.since is not None:
        discover_kwargs["since_year"] = args.since

    scraper = RushDuelScraper(
        data_dir=args.data_dir,
        download_images_flag=not args.no_images,
        force=args.force,
    )

    if args.command == "scrape-all":
        stats = scraper.scrape_all(**discover_kwargs)
        print(f"\nScrape complete:")
        print(f"  Discovered: {stats['discovered']} posts")
        print(f"  Scraped:    {stats['scraped']} posts")
        print(f"  Skipped:    {stats['skipped']} (unchanged)")
        print(f"  Errors:     {stats['errors']}")

    elif args.command == "update":
        stats = scraper.update(**discover_kwargs)
        print(f"\nUpdate complete:")
        print(f"  Discovered: {stats['discovered']} posts")
        print(f"  New:        {stats['new']} posts")
        print(f"  Updated:    {stats['updated']} posts")
        print(f"  Unchanged:  {stats['unchanged']} posts")
        print(f"  Errors:     {stats['errors']}")

    elif args.command == "scrape-url":
        result = scraper.scrape_post(args.url)
        print(f"\nResult: {result}")

    elif args.command == "discover":
        from .discovery import discover_rd_posts
        posts = discover_rd_posts(**discover_kwargs)
        print(f"\nDiscovered {len(posts)} Rush Duel card list posts:")
        for p in sorted(posts, key=lambda x: x["url"]):
            title = p["title"][:60] if p["title"] else "(no title)"
            print(f"  {title:<62s} {p['url']}")

    elif args.command == "check":
        updates = scraper.check_updates(**discover_kwargs)
        if updates:
            print(f"\n{len(updates)} posts need updating:")
            for url in updates:
                print(f"  {url}")
        else:
            print("\nAll posts are up to date.")

    elif args.command == "summary":
        s = scraper.summary()
        print(f"\nData summary:")
        print(f"  Total sets:  {s['total_sets']}")
        print(f"  Total cards: {s['total_cards']}")
        if s["sets"]:
            print(f"\n  Sets:")
            for set_id, info in sorted(s["sets"].items()):
                print(f"    {set_id}: {info['cards']} cards - {info['title']}")


if __name__ == "__main__":
    main()
