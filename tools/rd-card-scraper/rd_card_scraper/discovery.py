"""Discover Rush Duel card list posts from blog listing pages.

Strategy: "title first, content fallback"

1. Crawl blog listing pages (paginated, ~20 posts/page) to collect post
   URLs and titles — no individual page fetches needed for most posts.
2. Title-based fast filter: titles containing [卡表資料] + Rush Duel / RD/
   keywords are accepted immediately as card lists.
3. URL-based fallback: remaining posts whose URL contains 'rush-duel' or
   'rdgrd' (but title didn't match) are fetched and verified by content.
4. Explicit exclusion: ban lists, meta reports, combo guides, etc. are
   excluded by both title and URL patterns.

Date range: by default only listing pages from 2020 onwards are crawled
(RD launched in April 2020). The ``since_year`` parameter controls this.
The cutoff is based on the pagination cursor (``updated-max``), not on
individual post URL years, because Blogger sorts by last-update time
which can differ from the URL publication date.

Incremental optimisation: when known_urls is provided (e.g. from scrape
state), listing crawl stops early once a full page of already-known posts
is encountered.
"""

from __future__ import annotations

import re
import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BLOG_BASE = "https://ntucgm.blogspot.com"

# ---------- Date range ----------

# Rush Duel launched in April 2020; no RD posts before this year.
DEFAULT_SINCE_YEAR = 2020

# ---------- Title-based classification ----------

# The blog consistently uses [卡表資料] for card list posts
CARD_LIST_TITLE_TAG = "卡表資料"

# RD keywords that must appear alongside CARD_LIST_TITLE_TAG
RD_TITLE_KEYWORDS = [
    "Rush Duel",
    "rush duel",
    "RD/",
    "超速決鬥",
    "ラッシュデュエル",
    "RDGRD",
    "rdgrd",
    "Revolution Booster",
]

# Title keywords that definitively mean NOT a card list
EXCLUDE_TITLE_KEYWORDS = [
    "禁限卡表",       # ban list
    "Meta",           # meta reports
    "meta",
    "Combo",          # combo guides
    "combo",
    "基礎介紹",       # introductory articles
    "卡圖故事",       # card lore articles
]

# ---------- URL-based fallback classification ----------

# URL substrings for Rush Duel related posts (broad match)
RD_URL_MARKERS = ["rush-duel", "rdgrd", "revolution-booster"]

# URL patterns to EXCLUDE — definitively NOT card lists
EXCLUDE_URL_PATTERNS = [
    r"/rush-duel-202\d{2,}",   # ban list updates (20231, 20234, 202410…)
    r"/rush-duel-duel",         # introductory article
    r"meta-\d",                 # meta reports
    r"combo",                   # combo guides
    r"jump-festa.*pr",          # Jump Festa promo (mixed OCG/RD)
]

# ---------- Rate limits ----------
LISTING_PAGE_DELAY = 1.5   # seconds between listing page requests
VERIFY_DELAY = 1.5         # seconds between individual post verify fetches

# Blogger caps at ~20 posts per listing page
LISTING_PAGE_SIZE = 20

# Regex to extract year from pagination cursor (updated-max=YYYY-...)
_PAGINATION_YEAR_RE = re.compile(r"updated-max=(\d{4})-")


def _extract_pagination_year(url: str) -> int | None:
    """Extract the year from a Blogger pagination cursor URL."""
    m = _PAGINATION_YEAR_RE.search(url)
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ #
#  Title / URL classification helpers
# ------------------------------------------------------------------ #

def _is_rd_card_list_by_title(title: str) -> bool | None:
    """Classify a post by its title.

    Returns:
        True  — definitely an RD card list (accept immediately)
        False — definitely NOT an RD card list (reject immediately)
        None  — can't tell from title alone (needs further check)
    """
    for kw in EXCLUDE_TITLE_KEYWORDS:
        if kw in title:
            return False

    if CARD_LIST_TITLE_TAG in title:
        for kw in RD_TITLE_KEYWORDS:
            if kw in title:
                return True
        return False  # [卡表資料] but no RD keyword → probably OCG

    return None


def _is_rd_related_url(url: str) -> bool:
    """Check if a URL contains Rush Duel markers (broad match)."""
    url_lower = url.lower()
    return any(marker in url_lower for marker in RD_URL_MARKERS)


def _is_excluded_url(url: str) -> bool:
    """Check if a URL matches known non-card-list patterns."""
    return any(re.search(p, url) for p in EXCLUDE_URL_PATTERNS)


# ------------------------------------------------------------------ #
#  Content-based verification (fallback)
# ------------------------------------------------------------------ #

def verify_post_is_card_list(url: str, session: requests.Session) -> bool:
    """Fetch a post and verify it contains Rush Duel card data.

    A valid card list must have:
    1. RD/ card IDs in standard format (e.g. RD/KP01-JP001)
    2. Card type keywords (通常怪獸, 效果怪獸, etc.)
    """
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        post_body = soup.select_one(".post-body")
        if not post_body:
            return False
        text = post_body.get_text()
        has_rd_ids = bool(re.search(r"RD/\w+-JPS?\d{2,3}", text))
        has_card_types = any(
            kw in text
            for kw in [
                "通常怪獸", "效果怪獸", "融合怪獸", "儀式怪獸",
                "儀式/效果怪獸", "融合/效果怪獸", "巨極/效果怪獸",
                "通常魔法", "儀式魔法", "通常陷阱",
            ]
        )
        return has_rd_ids and has_card_types
    except Exception as e:
        logger.warning(f"Could not verify {url}: {e}")
        return False


# ------------------------------------------------------------------ #
#  Listing page crawler
# ------------------------------------------------------------------ #

def _crawl_listing_pages(
    session: requests.Session,
    *,
    since_year: int = DEFAULT_SINCE_YEAR,
    known_urls: set[str] | None = None,
) -> list[dict]:
    """Crawl blog listing pages to collect posts with titles.

    Pages are traversed from newest to oldest. Crawling stops when:
    - there are no more pages, OR
    - the *pagination cursor* year drops below ``since_year`` — this
      means ALL remaining pages contain posts older than our cutoff, OR
    - all posts on a page are already in ``known_urls`` (incremental).

    Note: the cutoff is intentionally based on the pagination cursor
    (``updated-max``) rather than individual post URL years, because
    Blogger can re-sort posts when they are edited. A post from 2020
    might appear on a 2021 listing page if it was edited in 2021.

    Args:
        session: HTTP session.
        since_year: Only crawl pages whose cursor is from this year
            onwards (default 2020).
        known_urls: URLs already known; enables early-stop optimisation.

    Returns:
        List of {"url": str, "title": str} dicts.
    """
    all_posts: list[dict] = []
    seen_urls: set[str] = set()

    next_url: str | None = (
        f"{BLOG_BASE}/search?updated-max=2099-01-01T00:00:00-08:00"
        f"&max-results={LISTING_PAGE_SIZE}"
    )

    page_num = 0

    while next_url:
        page_num += 1
        if page_num > 1:
            time.sleep(LISTING_PAGE_DELAY)

        logger.info(f"Fetching listing page {page_num}...")
        try:
            resp = session.get(next_url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch listing page {page_num}: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        post_links = soup.select("h3.post-title a[href]")
        new_count = 0
        known_on_page = 0

        for link in post_links:
            href = link.get("href", "").strip()
            title = link.get_text(strip=True)
            if not href or not href.endswith(".html") or href in seen_urls:
                continue
            seen_urls.add(href)
            all_posts.append({"url": href, "title": title})
            new_count += 1
            if known_urls and href in known_urls:
                known_on_page += 1

        if new_count == 0:
            logger.info(f"No new posts on page {page_num}, stopping.")
            break

        # Early stop: all posts on this page already known
        if known_urls and known_on_page == new_count:
            logger.info(
                f"All {new_count} posts on page {page_num} already known, "
                f"stopping early."
            )
            break

        # Find "next page" link
        next_url = None
        older_link = soup.select_one("a.blog-pager-older-link")
        if older_link:
            next_url = older_link.get("href")
        else:
            for a in soup.select("#blog-pager a[href]"):
                href_attr = a.get("href", "")
                if "updated-max=" in href_attr and "max-results=" in href_attr:
                    next_url = href_attr
                    break

        # Date cutoff: check the NEXT page's cursor year.
        # If the next page starts from before since_year, stop.
        if next_url:
            cursor_year = _extract_pagination_year(next_url)
            if cursor_year is not None and cursor_year < since_year:
                logger.info(
                    f"Next page cursor is {cursor_year} "
                    f"(before {since_year}), stopping."
                )
                break

    logger.info(
        f"Crawled {page_num} listing pages, found {len(all_posts)} total posts"
    )
    return all_posts


# ------------------------------------------------------------------ #
#  Main discovery entry point
# ------------------------------------------------------------------ #

def discover_rd_posts(
    verify: bool = True,
    known_urls: set[str] | None = None,
    since_year: int = DEFAULT_SINCE_YEAR,
) -> list[dict]:
    """Discover all Rush Duel card list post URLs.

    Strategy:
    Phase 1 — Crawl listing pages for posts since ``since_year``.
    Phase 2 — Title-based fast classification:
              [卡表資料] + RD keyword → accept; excluded keywords → reject.
    Phase 3 — URL-based fallback for unclassified posts:
              URL has rush-duel/rdgrd marker AND not excluded → verify.
    Phase 4 — Content verification for Phase 3 candidates.

    Args:
        verify: Verify Phase 3 candidates by fetching content (default True).
        known_urls: Previously discovered URLs for incremental early-stop.
        since_year: Only crawl listing pages from this year onwards
            (default 2020). Uses pagination cursor for the cutoff.

    Returns:
        List of dicts with 'url' and 'title' keys.
    """
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; RD-Card-Scraper/0.1)"
    )

    # Phase 1: Crawl listing pages
    logger.info(f"Phase 1: Crawling blog listing pages (since {since_year})...")
    all_posts = _crawl_listing_pages(
        session, since_year=since_year, known_urls=known_urls
    )

    # Phase 2 & 3: Classify each post
    accepted: list[dict] = []
    needs_verify: list[dict] = []
    title_accepted = 0
    title_rejected = 0
    url_candidates = 0

    for post in all_posts:
        url, title = post["url"], post["title"]

        verdict = _is_rd_card_list_by_title(title)
        if verdict is True:
            accepted.append(post)
            title_accepted += 1
            continue
        if verdict is False:
            title_rejected += 1
            continue

        # Title inconclusive → check URL
        if _is_rd_related_url(url) and not _is_excluded_url(url):
            needs_verify.append(post)
            url_candidates += 1

    logger.info(
        f"Phase 2 title filter: {title_accepted} accepted, "
        f"{title_rejected} rejected, "
        f"{len(all_posts) - title_accepted - title_rejected} unclassified"
    )
    logger.info(
        f"Phase 3 URL fallback: {url_candidates} candidates need verification"
    )

    # Phase 4: Verify URL-based candidates
    if needs_verify:
        if verify:
            logger.info(
                f"Phase 4: Verifying {len(needs_verify)} candidates..."
            )
            for i, post in enumerate(needs_verify, 1):
                time.sleep(VERIFY_DELAY)
                ok = verify_post_is_card_list(post["url"], session)
                symbol = "✓" if ok else "✗"
                logger.info(
                    f"  [{i}/{len(needs_verify)}] {symbol} "
                    f"{post['title']} — {post['url']}"
                )
                if ok:
                    accepted.append(post)
        else:
            accepted.extend(needs_verify)

    logger.info(f"Discovered {len(accepted)} Rush Duel card list posts")
    return accepted
