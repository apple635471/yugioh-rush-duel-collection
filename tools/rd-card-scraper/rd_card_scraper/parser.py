"""Parse Rush Duel card data from blog post HTML.

=== HTML Structure Notes (across blog eras) ===

The blog has two sections per card-list post:
  1. Summary/index at the top: just card IDs + names, no stats. Used for table of contents.
  2. Detail section below: full card entries with stats, effects, images.

Detail entry structure (varies by era):

KP01 era (2020):
  <span color><b>RD/KP01-JP024  (R)ドラゴンズ・セットアッパー</b></span><br/>
  <span color><b>(龍之布局者)  效果怪獸  1  暗  龍族  0/1000</b></span><br/>
  <span>條件:...</span><br/>
  <span>效果:...</span><br/>

KP09 era (2022):
  <div><b><span color>RD/KP09-JP000  (SER/RR)リボルバー・ドラゴン(legend)</span></b></div>
  <div>(左輪手槍龍)  效果怪獸  7  暗  機械族  2600/2200</div>
  <div>條件:無</div>
  <div>效果:...</div>
  <div><img src="..."/></div>

KP23 era (2025):
  <div><b><span color>RD/KP23-JPS00  (ORRPBV)荘厳なるブレイズファント</span></b></div>
  <div>(莊嚴的火炎兵)  效果怪獸  9  炎  機械族  2500/800</div>
  <div>條件:...</div>
  <div>效果:...</div>
  <div><a href="..."><img src="..."/></a></div>

Key insight: card IDs appear TWICE (summary + detail). We parse the DETAIL section
by finding each card ID and gathering subsequent text/images until the next card ID.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag

from .models import Card, CardSet

logger = logging.getLogger(__name__)

# Regex to match card IDs like RD/KP01-JP000, RD/LGP1-JP001, RD/GRD1-JPS00
CARD_ID_RE = re.compile(r"(RD/\w+-JPS?\d{2,3})")

# Regex to extract set ID from card ID: e.g. "KP01" from "RD/KP01-JP000"
SET_ID_RE = re.compile(r"RD/(\w+)-JP")

# Rarity patterns in parentheses, e.g. (UR), (SR/SER), (RR), (ORRPBV)
RARITY_RE = re.compile(r"\(([A-Z/]+)\)")

# Stats line: (Chinese name) CardType [Level Attribute Race ATK/DEF]
# Compound types (X/Y怪獸) MUST appear before simple types so regex matches
# the longer form first; e.g. 儀式/效果怪獸 before 效果怪獸.
CARD_TYPES = (
    "儀式/效果怪獸|融合/效果怪獸|巨極/效果怪獸|"
    "通常怪獸|效果怪獸|融合怪獸|儀式怪獸|"
    "儀式魔法|通常魔法|速攻魔法|永續魔法|裝備魔法|場地魔法|"
    "通常陷阱|永續陷阱|反擊陷阱"
)
STATS_RE = re.compile(
    r"[（(]([^)）]+?)[）)]\s*"  # Chinese name
    r"(" + CARD_TYPES + r")"
    r"(?:\s+(\d+))?"       # Level
    r"(?:\s+(光|暗|炎|水|風|地))?"  # Attribute
    r"(?:\s+(\S+族))?"     # Race
    r"(?:\s+(\d+|\?)/(\d+|\?))?"  # ATK/DEF
)

# For inline entries where stats are on the same line as the card ID (KP01 JP023 style)
# e.g. "RD/KP01-JP023 (RR)セブンスロード・マジシャン(七王道魔術師) 暗 7星魔法使 21001500"
INLINE_STATS_RE = re.compile(
    r"[（(]([^)）]+?)[）)]\s*"  # Chinese name
    r"(光|暗|炎|水|風|地)\s+"
    r"(\d+)[星☆]\s*"       # Level + star character
    r"(\S+)\s+"            # Race (without 族 suffix sometimes)
    r"(\d+)(\d{3,4})$"    # ATK+DEF concatenated (e.g. 21001500)
)

CONDITION_RE = re.compile(r"條件[:：]\s*(.+)")
EFFECT_RE = re.compile(r"^效果[:：]\s*(.+)", re.DOTALL)
CONTINUOUS_EFFECT_RE = re.compile(r"永續效果[:：]\s*(.+)", re.DOTALL)

# Labels that can appear in card text; used to split a single chunk that
# contains multiple sections (e.g. "條件:…效果:…" on one line).
# The negative lookbehind (?<!永續) prevents "效果:" from splitting inside
# "永續效果:" — "永續效果" is matched as a whole unit instead.
_LABEL_SPLIT_RE = re.compile(r"(?=(?:條件|永續效果|(?<!永續)效果)[:：])")

# Product type mapping from set ID prefix
PRODUCT_TYPE_MAP = {
    "KP": "booster",
    "ST": "starter",
    "CP": "character_pack",
    "GRC": "go_rush_character",
    "GRD": "go_rush_deck",
    "B0": "battle_pack",
    "B2": "battle_pack",
    "MAX": "maximum_pack",
    "EXT": "extra_pack",
    "LGP": "legend_pack",
    "SD": "structure_deck",
    "VSP": "vs_pack",
    "TB": "tournament_pack",
    "AP": "advanced_pack",
    "ORP": "over_rush_pack",
}


def compute_content_hash(html: str) -> str:
    """Compute a hash of the post body HTML for change detection."""
    return hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]


def extract_post_body(html: str) -> Optional[Tag]:
    """Extract the post-body div from full page HTML."""
    soup = BeautifulSoup(html, "lxml")
    return soup.select_one(".post-body")


def extract_post_title(html: str) -> str:
    """Extract the post title."""
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("h3.post-title") or soup.select_one("title")
    return title_el.get_text(strip=True) if title_el else ""


def guess_product_type(set_id: str) -> str:
    for prefix, ptype in PRODUCT_TYPE_MAP.items():
        if set_id.startswith(prefix):
            return ptype
    return "unknown"


def parse_post(html: str, url: str = "") -> Optional[CardSet]:
    """Parse a blog post HTML into a CardSet with cards."""
    post_body = extract_post_body(html)
    if not post_body:
        logger.warning(f"No post-body found in {url}")
        return None

    title = extract_post_title(html)
    body_text = post_body.get_text()

    all_card_ids = CARD_ID_RE.findall(body_text)
    if not all_card_ids:
        logger.warning(f"No card IDs found in {url}")
        return None

    set_match = SET_ID_RE.search(all_card_ids[0])
    if not set_match:
        return None
    set_id = set_match.group(1)

    set_name_jp, set_name_zh, release_date, rarity_dist = _parse_set_metadata(
        post_body, title
    )

    card_set = CardSet(
        set_id=set_id,
        set_name_jp=set_name_jp,
        set_name_zh=set_name_zh or title,
        product_type=guess_product_type(set_id),
        release_date=release_date,
        post_url=url,
        rarity_distribution=rarity_dist,
    )

    cards = _extract_cards_from_body(post_body)
    card_set.cards = cards
    card_set.total_cards = len(cards)

    logger.info(f"Parsed {len(cards)} cards from set {set_id} ({url})")
    return card_set


def _parse_set_metadata(
    post_body: Tag, title: str
) -> tuple[str, str, Optional[str], dict]:
    text = post_body.get_text()
    set_name_jp = ""
    set_name_zh = title
    release_date = None
    rarity_dist: dict[str, int] = {}

    date_match = re.search(r"(\d{4}/\d{1,2}/\d{1,2})", text)
    if date_match:
        release_date = date_match.group(1)

    rarity_matches = re.findall(r"(\w+)\s+(\d+)種", text[:2000])
    for rarity, count in rarity_matches:
        rarity_dist[rarity] = int(count)

    lines = text.strip().split("\n")
    for line in lines[:10]:
        line = line.strip()
        if re.search(r"[\u30A0-\u30FF]{3,}", line) and "RD/" not in line:
            set_name_jp = line
            break

    return set_name_jp, set_name_zh, release_date, rarity_dist


def _extract_cards_from_body(post_body: Tag) -> list[Card]:
    """Extract cards using a text-based approach.

    Strategy:
    1. Get the full text of the post body, preserving line structure.
    2. Card IDs typically appear twice (summary + detail). We only parse detail entries,
       which are the ones followed by stats lines (containing card type keywords).
    3. For each card entry, collect text lines until the next card ID.
    4. Separately collect images in order and match them to cards.
    """
    # Build a flat list of "chunks" - each is either a text line or an image URL
    chunks = _flatten_to_chunks(post_body)

    # Find detail card entries (those followed by a stats line)
    cards: list[Card] = []
    seen_detail_ids: set[str] = set()
    i = 0

    while i < len(chunks):
        chunk = chunks[i]

        # Skip image-only chunks
        if chunk["type"] == "image":
            i += 1
            continue

        text = chunk["text"]
        card_id_match = CARD_ID_RE.search(text)

        if not card_id_match:
            i += 1
            continue

        card_id = card_id_match.group(1)

        # Look ahead: is this a detail entry (has stats nearby) or summary?
        is_detail = _is_detail_entry(chunks, i)

        if not is_detail:
            i += 1
            continue

        # Skip if we already parsed this card ID in detail
        if card_id in seen_detail_ids:
            i += 1
            continue
        seen_detail_ids.add(card_id)

        # Parse this card entry
        card = _parse_card_header(text, card_id)

        # Collect subsequent lines for stats, condition, effect, image
        j = i + 1
        context_texts: list[str] = []
        card_image: Optional[str] = None

        while j < len(chunks):
            next_chunk = chunks[j]

            if next_chunk["type"] == "image":
                if card_image is None:
                    card_image = next_chunk["url"]
                j += 1
                continue

            next_text = next_chunk["text"]

            # Stop if we hit another card ID
            if CARD_ID_RE.search(next_text):
                break

            # Stop at empty/separator lines after we've collected some content
            if not next_text.strip() and context_texts:
                # Check if the line after this blank is a new card
                if j + 1 < len(chunks) and chunks[j + 1]["type"] == "text":
                    if CARD_ID_RE.search(chunks[j + 1]["text"]):
                        break
                # Allow one blank line (might be followed by image)
                j += 1
                continue

            if next_text.strip():
                context_texts.append(next_text.strip())
            j += 1

        # Check if the header line itself contains inline stats (KP01 JP023 style)
        _parse_card_details(card, text, context_texts)

        if card_image:
            card.image_url = _normalize_image_url(card_image)

        cards.append(card)
        i = j

    return cards


def _flatten_to_chunks(post_body: Tag) -> list[dict]:
    """Flatten the post body into a flat list of text lines and images.

    Returns list of dicts:
      {"type": "text", "text": "..."} or
      {"type": "image", "url": "..."}
    """
    chunks: list[dict] = []

    def walk(el):
        if isinstance(el, NavigableString):
            text = str(el).strip()
            if text:
                chunks.append({"type": "text", "text": text})
            return

        if not isinstance(el, Tag):
            return

        if el.name in ("script", "style", "noscript"):
            return

        if el.name == "img":
            src = el.get("src", "") or el.get("data-src", "")
            if src and "googleusercontent" in src:
                chunks.append({"type": "image", "url": src})
            return

        if el.name == "br":
            return  # skip, we handle structure via divs/spans

        # For div and span: check if it's a leaf text node
        children = list(el.children)
        if not children:
            return

        # If this element contains only text (no sub-elements), emit as one chunk
        all_text = el.get_text(strip=True)
        has_child_tags = any(isinstance(c, Tag) and c.name not in ("br",) for c in children)

        if not has_child_tags and all_text:
            chunks.append({"type": "text", "text": all_text})
            # But also check for images
            for img in el.find_all("img"):
                src = img.get("src", "") or img.get("data-src", "")
                if src and "googleusercontent" in src:
                    chunks.append({"type": "image", "url": src})
            return

        # Otherwise recurse into children
        for child in children:
            walk(child)

    walk(post_body)
    return chunks


def _is_detail_entry(chunks: list[dict], idx: int) -> bool:
    """Check if a card ID at chunks[idx] is a detail entry (not summary).

    A detail entry has stats keywords nearby (within next 3 text chunks):
    card type keywords like 通常怪獸, 效果怪獸, 通常魔法, etc.
    OR the header line itself contains inline stats.
    """
    header_text = chunks[idx]["text"]

    # Check inline stats (same line as card ID)
    # Compound types listed first so they match before simple types
    card_type_keywords = [
        "儀式/效果怪獸", "融合/效果怪獸", "巨極/效果怪獸",
        "通常怪獸", "效果怪獸", "融合怪獸", "儀式怪獸",
        "儀式魔法", "通常魔法", "速攻魔法", "永續魔法", "裝備魔法", "場地魔法",
        "通常陷阱", "永續陷阱", "反擊陷阱",
    ]
    for kw in card_type_keywords:
        if kw in header_text:
            return True

    # Check next few text chunks
    checked = 0
    for j in range(idx + 1, min(idx + 6, len(chunks))):
        if chunks[j]["type"] != "text":
            continue
        text = chunks[j]["text"]
        # If we hit another card ID, this is summary
        if CARD_ID_RE.search(text):
            return False
        for kw in card_type_keywords:
            if kw in text:
                return True
        checked += 1
        if checked >= 3:
            break

    return False


def _normalize_image_url(url: str) -> str:
    """Normalize blogger/googleusercontent image URLs for high resolution."""
    url = re.sub(r"=w\d+-h\d+", "=s800", url)
    url = re.sub(r"=s\d+(-[a-z]+)?$", "=s800", url)
    if "googleusercontent.com" in url and "=s" not in url and "=w" not in url:
        url = url.rstrip("/") + "=s800"
    return url


def _parse_card_header(header_text: str, card_id: str) -> Card:
    """Parse card ID, rarity, and JP name from header text."""
    rarity = "N"
    rarity_match = RARITY_RE.search(header_text)
    if rarity_match:
        rarity = rarity_match.group(1)

    # Remove card ID
    name_part = header_text.replace(card_id, "").strip()
    # Remove rarity in parentheses
    name_part = RARITY_RE.sub("", name_part).strip()

    # Check for (legend) marker
    is_legend = bool(re.search(r"\(legend\)", name_part, re.IGNORECASE))
    name_part = re.sub(r"\(legend\)", "", name_part, flags=re.IGNORECASE).strip()

    # If inline stats exist (rare KP01 pattern), extract just the JP name
    # e.g. "セブンスロード・マジシャン(七王道魔術師) 暗 7星魔法使 21001500"
    # The JP name is everything before the first ( for Chinese name
    paren_idx = name_part.find("(")
    if paren_idx == -1:
        paren_idx = name_part.find("（")
    if paren_idx > 0:
        # Check if this parenthesized part is a Chinese name (not a rarity)
        potential_zh = name_part[paren_idx:]
        if re.match(r"[（(][\u4e00-\u9fff]", potential_zh):
            name_part = name_part[:paren_idx].strip()

    return Card(
        card_id=card_id,
        rarity=rarity,
        name_jp=name_part,
        name_zh="",
        card_type="",
        is_legend=is_legend,
    )


def _parse_card_details(
    card: Card, header_text: str, context_lines: list[str]
) -> None:
    """Parse stats, condition, effect from context lines and possibly header."""
    # Combine header + context for full text search
    all_text = header_text + "\n" + "\n".join(context_lines)

    # Try standard stats pattern from context lines
    for line in context_lines:
        stats_match = STATS_RE.search(line)
        if stats_match:
            card.name_zh = stats_match.group(1)
            card.card_type = stats_match.group(2)
            if stats_match.group(3):
                card.level = int(stats_match.group(3))
            card.attribute = stats_match.group(4)
            card.monster_type = stats_match.group(5)
            if stats_match.group(6):
                card.atk = stats_match.group(6)
            if stats_match.group(7):
                card.defense = stats_match.group(7)
            break

    # If no stats found in context, check header for inline stats
    if not card.card_type:
        stats_match = STATS_RE.search(header_text)
        if stats_match:
            card.name_zh = stats_match.group(1)
            card.card_type = stats_match.group(2)
            if stats_match.group(3):
                card.level = int(stats_match.group(3))
            card.attribute = stats_match.group(4)
            card.monster_type = stats_match.group(5)
            if stats_match.group(6):
                card.atk = stats_match.group(6)
            if stats_match.group(7):
                card.defense = stats_match.group(7)

    # Parse condition, effect, continuous effect, and summon condition.
    #
    # Context lines after the stats line may contain:
    #   - Summon condition text (before 條件:), e.g. "此卡只能用…特殊召喚"
    #   - 條件:...
    #   - 效果:...
    #   - 永續效果:...
    #
    # A single chunk may contain multiple labels joined together, e.g.
    # "條件:…可以發動效果:…". We split such chunks before classifying.

    # Step 1: collect lines after the stats line, splitting multi-label chunks
    post_stats_lines: list[str] = []
    stats_seen = False
    for line in context_lines:
        if not stats_seen:
            if STATS_RE.search(line):
                stats_seen = True
            continue
        # Split a single line like "條件:…效果:…" into separate parts.
        # _LABEL_SPLIT_RE uses lookahead so the label text is preserved.
        parts = _LABEL_SPLIT_RE.split(line)
        for p in parts:
            p = p.strip()
            if p:
                post_stats_lines.append(p)

    # Step 2: classify each part
    summon_cond_parts: list[str] = []
    cond_parts: list[str] = []
    effect_parts: list[str] = []
    cont_effect_parts: list[str] = []
    seen_condition = False
    seen_effect = False
    in_section: str = ""  # "cond", "effect", "cont_effect", or ""

    for line in post_stats_lines:
        cond_match = CONDITION_RE.match(line)
        eff_match = EFFECT_RE.match(line)
        cont_eff_match = CONTINUOUS_EFFECT_RE.match(line)

        if cond_match:
            cond_parts.append(cond_match.group(1))
            seen_condition = True
            in_section = "cond"
        elif cont_eff_match:
            cont_effect_parts.append(cont_eff_match.group(1))
            seen_effect = True
            in_section = "cont_effect"
        elif eff_match:
            effect_parts.append(eff_match.group(1))
            seen_effect = True
            in_section = "effect"
        elif not seen_condition and not seen_effect and line:
            # Text between stats and 條件: → summon condition
            summon_cond_parts.append(line)
        elif in_section == "effect" and line and not STATS_RE.search(line):
            effect_parts.append(line)
        elif in_section == "cont_effect" and line and not STATS_RE.search(line):
            cont_effect_parts.append(line)

    if summon_cond_parts:
        card.summon_condition = "".join(summon_cond_parts)
    if cond_parts:
        card.condition = "".join(cond_parts)
    if effect_parts:
        card.effect = "".join(effect_parts)
    if cont_effect_parts:
        card.continuous_effect = "".join(cont_effect_parts)
