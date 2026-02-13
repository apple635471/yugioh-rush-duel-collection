"""Main scraper orchestrator with incremental update support."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .discovery import discover_rd_posts, is_rd_card_list_url, get_sitemap_urls
from .downloader import download_images
from .models import CardSet, PostState, ScrapeState
from .parser import compute_content_hash, extract_post_body, parse_post

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path("data")
STATE_FILE = "scrape_state.json"
FETCH_DELAY = 1.5  # seconds between page fetches


class RushDuelScraper:
    def __init__(
        self,
        data_dir: Path = DEFAULT_DATA_DIR,
        download_images_flag: bool = True,
        force: bool = False,
    ):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.download_images_flag = download_images_flag
        self.force = force
        self.state = ScrapeState.load(data_dir / STATE_FILE)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; RD-Card-Scraper/0.1)"
        )

    def save_state(self) -> None:
        self.state.save(self.data_dir / STATE_FILE)

    def scrape_all(self) -> dict:
        """Scrape all discovered Rush Duel card list posts.

        Returns summary stats.
        """
        posts = discover_rd_posts(verify=False)
        stats = {"discovered": len(posts), "scraped": 0, "skipped": 0, "errors": 0}

        for post_info in posts:
            url = post_info["url"]
            try:
                result = self.scrape_post(url)
                if result == "scraped":
                    stats["scraped"] += 1
                elif result == "skipped":
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                stats["errors"] += 1

        self.save_state()
        return stats

    def scrape_post(self, url: str) -> str:
        """Scrape a single post.

        Returns:
            "scraped" if new data was saved
            "skipped" if content hasn't changed
        """
        time.sleep(FETCH_DELAY)
        logger.info(f"Fetching {url}")
        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        html = resp.text

        # Check if content changed
        post_body = extract_post_body(html)
        if not post_body:
            logger.warning(f"No post body found: {url}")
            return "skipped"

        content_hash = compute_content_hash(str(post_body))

        existing_state = self.state.posts.get(url)
        if existing_state and existing_state.content_hash == content_hash and not self.force:
            logger.info(f"No changes detected, skipping: {url}")
            return "skipped"

        # Parse the post
        card_set = parse_post(html, url)
        if not card_set or not card_set.cards:
            logger.warning(f"No cards parsed from {url}")
            return "skipped"

        # Download images
        if self.download_images_flag:
            download_images(
                card_set.cards,
                card_set.set_id,
                self.data_dir,
                self.session,
                force=self.force,
            )

        # Save card data
        card_set.save(self.data_dir)

        # Update state
        self.state.posts[url] = PostState(
            url=url,
            title=card_set.set_name_zh,
            set_id=card_set.set_id,
            last_scraped=datetime.now(timezone.utc).isoformat(),
            content_hash=content_hash,
            card_count=len(card_set.cards),
        )
        self.save_state()

        logger.info(
            f"Scraped {len(card_set.cards)} cards from {card_set.set_id}"
        )
        return "scraped"

    def scrape_url(self, url: str) -> str:
        """Scrape a specific URL (for manual/targeted scraping)."""
        return self.scrape_post(url)

    def check_updates(self) -> list[str]:
        """Check for new or updated posts without scraping.

        Returns list of URLs that need updating.
        """
        posts = discover_rd_posts(verify=False)
        needs_update = []

        for post_info in posts:
            url = post_info["url"]
            if url not in self.state.posts:
                needs_update.append(url)
                continue

            # Optionally fetch and check content hash
            try:
                time.sleep(FETCH_DELAY)
                resp = self.session.get(url, timeout=60)
                resp.raise_for_status()
                post_body = extract_post_body(resp.text)
                if post_body:
                    current_hash = compute_content_hash(str(post_body))
                    if current_hash != self.state.posts[url].content_hash:
                        needs_update.append(url)
            except Exception as e:
                logger.warning(f"Could not check {url}: {e}")

        return needs_update

    def update(self) -> dict:
        """Only scrape new or changed posts (incremental update).

        Returns summary stats.
        """
        posts = discover_rd_posts(verify=False)
        stats = {"discovered": len(posts), "new": 0, "updated": 0, "unchanged": 0, "errors": 0}

        for post_info in posts:
            url = post_info["url"]
            is_new = url not in self.state.posts

            try:
                result = self.scrape_post(url)
                if result == "scraped":
                    if is_new:
                        stats["new"] += 1
                    else:
                        stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
            except Exception as e:
                logger.error(f"Error updating {url}: {e}")
                stats["errors"] += 1

        self.save_state()
        return stats

    def summary(self) -> dict:
        """Get a summary of currently scraped data."""
        sets = {}
        for ps in self.state.posts.values():
            sets[ps.set_id] = {
                "title": ps.title,
                "cards": ps.card_count,
                "last_scraped": ps.last_scraped,
                "url": ps.url,
            }
        return {
            "total_sets": len(sets),
            "total_cards": sum(s["cards"] for s in sets.values()),
            "sets": sets,
        }
