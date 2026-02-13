"""Discover Rush Duel card list posts from the blog sitemap and search."""

from __future__ import annotations

import re
import logging
import time
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BLOG_BASE = "https://ntucgm.blogspot.com"
SITEMAP_INDEX = f"{BLOG_BASE}/sitemap.xml"
# Only scrape card list posts (卡表資料), not ban lists (禁限卡表)
CARD_LIST_TAG = "卡表資料"

# URL patterns that indicate Rush Duel card list posts
RD_URL_PATTERNS = [
    r"/rush-duel-kp\d",       # KP booster packs
    r"/rush-duel-st0",        # starter decks
    r"/rush-duel-cp0",        # character packs
    r"/rush-duel-b00",        # battle packs (B001-B004)
    r"/rush-duel-b2[234]",    # battle packs (B221-B244)
    r"/rush-duel-max",        # maximum packs
    r"/rush-duel-ext",        # extra packs
    r"/rush-duel-lgp",        # legend packs
    r"/rush-duel-grc",        # Go Rush character packs
    r"/rdgrd",                # Go Rush decks
    r"/rush-duel-sd-",        # structure decks
    r"/rush-duel-vsp",        # VS packs
    r"/rush-duel-tb0",        # tournament packs
    r"/rush-duel-.*卡表",
    r"/rush-duel-\d+-\d+1\d", # date-based posts that are card lists (e.g. 1211, 1216)
    r"revolution-booster",    # special named boosters
    r"/rush-duel-ap0",        # advanced packs
]

# URL patterns to EXCLUDE (not card lists)
EXCLUDE_PATTERNS = [
    r"/rush-duel-2024\d",     # ban list updates (20241, 20244, 20247, 202410)
    r"/rush-duel-2023\d",     # ban list updates
    r"/rush-duel-2025\d",     # ban list updates (20251, 20254, 20257, 202510)
    r"/rush-duel-2026\d",     # ban list updates
    r"/rush-duel-duel",       # introductory article
    r"meta-\d",               # meta reports
    r"combo",                 # combo guides
    r"jump-festa.*pr",        # Jump Festa promo (mixed OCG/RD)
]


def get_sitemap_urls() -> list[str]:
    """Fetch all post URLs from the blog sitemap."""
    all_urls = []
    try:
        resp = requests.get(SITEMAP_INDEX, timeout=30)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_locs = [loc.text for loc in root.findall(".//sm:loc", ns)]

        for sitemap_url in sitemap_locs:
            time.sleep(0.5)
            resp = requests.get(sitemap_url, timeout=30)
            resp.raise_for_status()
            sub_root = ElementTree.fromstring(resp.content)
            for loc in sub_root.findall(".//sm:loc", ns):
                if loc.text:
                    all_urls.append(loc.text)
    except Exception as e:
        logger.error(f"Failed to fetch sitemap: {e}")
    return all_urls


def is_rd_card_list_url(url: str) -> bool:
    """Check if a URL is likely a Rush Duel card list post."""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, url):
            return False
    for pattern in RD_URL_PATTERNS:
        if re.search(pattern, url):
            return True
    return False


def verify_post_is_card_list(url: str, session: requests.Session) -> bool:
    """Fetch a post and check if it actually contains Rush Duel card data."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        post_body = soup.select_one(".post-body")
        if not post_body:
            return False
        text = post_body.get_text()
        # Must contain RD/ card IDs
        has_rd_ids = bool(re.search(r"RD/\w+-JP\d{3}", text))
        # Must have card type keywords
        has_card_types = any(
            kw in text
            for kw in ["通常怪獸", "效果怪獸", "通常魔法", "通常陷阱", "融合怪獸"]
        )
        return has_rd_ids and has_card_types
    except Exception as e:
        logger.warning(f"Could not verify {url}: {e}")
        return False


def discover_rd_posts(verify: bool = False) -> list[dict]:
    """Discover all Rush Duel card list post URLs.

    Returns list of dicts with 'url' and 'title' keys.
    """
    logger.info("Fetching sitemap...")
    all_urls = get_sitemap_urls()
    logger.info(f"Found {len(all_urls)} total blog URLs")

    rd_urls = [u for u in all_urls if is_rd_card_list_url(u)]
    logger.info(f"Filtered to {len(rd_urls)} potential Rush Duel card list URLs")

    # Also try to get titles from the blog search
    posts = []
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; RD-Card-Scraper/0.1)"
    )

    for url in rd_urls:
        post_info = {"url": url, "title": ""}
        if verify:
            time.sleep(1)
            if not verify_post_is_card_list(url, session):
                logger.info(f"Skipping non-card-list post: {url}")
                continue
        posts.append(post_info)

    # Also search for posts we might have missed
    _search_for_additional_posts(posts, session)

    logger.info(f"Discovered {len(posts)} Rush Duel card list posts")
    return posts


def _search_for_additional_posts(
    posts: list[dict], session: requests.Session
) -> None:
    """Search the blog for Rush Duel posts that might not match URL patterns."""
    known_urls = {p["url"] for p in posts}
    search_queries = [
        "Rush Duel 補充包",
        "Rush Duel 卡表",
        "超速決鬥 卡表",
    ]
    for query in search_queries:
        try:
            time.sleep(1)
            resp = session.get(
                f"{BLOG_BASE}/search",
                params={"q": query},
                timeout=30,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for link in soup.select("a[href]"):
                href = link.get("href", "")
                if (
                    href.startswith(BLOG_BASE)
                    and href.endswith(".html")
                    and href not in known_urls
                    and is_rd_card_list_url(href)
                ):
                    known_urls.add(href)
                    posts.append({"url": href, "title": link.get_text(strip=True)})
        except Exception as e:
            logger.warning(f"Search for '{query}' failed: {e}")
