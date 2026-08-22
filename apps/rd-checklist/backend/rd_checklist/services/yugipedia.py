"""Read a set's card list from yugipedia.

Used to check a set in the DB against the published list: which printings are
missing, which ones we have that the list doesn't mention.

The wikitext is the source rather than the rendered page — a `{{Set list}}`
block is one card per line and far steadier than the HTML table:

    {{Set list|region=JP|rarities=C|print=New|
    RD/KP20-JP001; Insect Knight (Rush Duel); R
    RD/KP20-JP002; Silver Red Pulsar
    RD/KP20-JP007; Variable Stellarizer; SR, ScR
    RD/KP20-JP007; Variable Stellarizer; ScR // description :: (alternate artwork)
    }}

Three things that are easy to get wrong:
  * A row with no rarity column inherits the block's `rarities=` default
    (most rows do — above, JP002 is a Common).
  * Rarities appear both abbreviated (`ScR`) and spelled out (`Secret Rare`),
    varying by page.
  * An alternate artwork is a *second row for the same card id*, usually
    tagged `// description :: (alternate artwork)`.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://yugipedia.com/api.php"
USER_AGENT = "rd-checklist/0.1 (personal Rush Duel collection tracker)"
TIMEOUT = 30

# Card list subpages hang off the set page under one of these suffixes.
LIST_PAGE_SUFFIXES = ("(OCG-JP)", "(Rush Duel-JP)", "(JP)")

# yugipedia rarity → our code. Both the abbreviations and the spelled-out
# names appear in the wild, sometimes on neighbouring pages.
RARITY_MAP: dict[str, str] = {
    # Common
    "c": "N",
    "common": "N",
    # Rare
    "r": "R",
    "rare": "R",
    # Super / Ultra
    "sr": "SR",
    "super rare": "SR",
    "ur": "UR",
    "ultra rare": "UR",
    # Secret
    "scr": "SER",
    "secret rare": "SER",
    # Rush / Over Rush family
    "rr": "RR",
    "rush rare": "RR",
    "grr": "GRR",
    "gold rush rare": "GRR",
    "orr": "ORR",
    "over rush rare": "ORR",
    "forr": "FORR",
    "full over rush rare": "FORR",
    "orrblack": "ORRPBV",
    "over rush rare (premium black version)": "ORRPBV",
    # Parallel
    "npr": "NPR",
    "normal parallel rare": "NPR",
    "spr": "SPR",
    "super parallel rare": "SPR",
    "upr": "UPR",
    "ultra parallel rare": "UPR",
    # Special red
    "rur": "RUR",
    "ultra rare (special red version)": "RUR",
}

_SET_LIST_RE = re.compile(r"\{\{Set list([^\n]*)\n(.*?)\n\}\}", re.S)
# Japanese names carry furigana markup: {{Ruby|連|れん}}撃竜 → 連撃竜
_RUBY_RE = re.compile(r"\{\{Ruby\|([^|}]*)\|[^}]*\}\}")
_WIKILINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
_ALT_ART_RE = re.compile(r"alternate\s+artwork", re.I)
_CARD_ID_RE = re.compile(r"^RD/[\w-]+-JPS?\d{2,3}$")


@dataclass
class ExpectedVariant:
    """One printing of one card, as the list says it exists."""

    card_id: str
    rarity: str
    is_alternate_art: bool
    name_en: str
    name_jp: str = ""


@dataclass
class SetListResult:
    list_page: str
    variants: list[ExpectedVariant] = field(default_factory=list)
    # Rarity strings we could not map — surfaced rather than silently dropped,
    # since a missed rarity would look like a missing card downstream.
    unknown_rarities: list[str] = field(default_factory=list)


class YugipediaError(Exception):
    """The page could not be fetched or holds no usable card list."""


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, follow_redirects=True
    )


def page_title_from_url(url: str) -> str:
    """Page title from a yugipedia URL, or the input if it is already a title."""
    url = url.strip()
    if not url:
        raise YugipediaError("請輸入 yugipedia 頁面網址")
    if "://" not in url:
        return url.replace("_", " ")

    parsed = urllib.parse.urlparse(url)
    if "yugipedia.com" not in parsed.netloc:
        raise YugipediaError("只支援 yugipedia.com 的頁面網址")

    path = urllib.parse.unquote(parsed.path)
    for prefix in ("/wiki/", "/index.php/"):
        if path.startswith(prefix):
            path = path[len(prefix):]
            break
    else:
        path = path.lstrip("/")
    if not path:
        raise YugipediaError("網址裡看不出頁面名稱")
    return path.replace("_", " ")


def _fetch_wikitext(client: httpx.Client, title: str) -> str | None:
    resp = client.get(
        API_URL,
        params={"action": "parse", "page": title, "prop": "wikitext", "format": "json"},
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        return None
    return data["parse"]["wikitext"]["*"]


def _normalize_rarity(token: str) -> str | None:
    return RARITY_MAP.get(token.strip().lower())


def parse_set_list(wikitext: str) -> tuple[list[ExpectedVariant], list[str]]:
    """Every printing named by the `{{Set list}}` blocks in a page."""
    variants: list[ExpectedVariant] = []
    unknown: list[str] = []
    seen_ids: set[str] = set()

    for header, body in _SET_LIST_RE.findall(wikitext):
        # Header params: |region=JP|rarities=C|print=New|
        params = dict(
            part.split("=", 1)
            for part in (p.strip() for p in header.split("|"))
            if "=" in part
        )
        default_rarities = params.get("rarities", "")

        for line in body.split("\n"):
            line = line.strip()
            if not line or line.startswith(("!", "|", "<", "{")):
                continue

            cells = [c.strip() for c in line.split(";")]
            card_id = cells[0]
            if not _CARD_ID_RE.match(card_id):
                continue

            name_en = cells[1] if len(cells) > 1 else ""
            rarity_cell = cells[2] if len(cells) > 2 and cells[2] else default_rarities

            # "ScR // description :: (alternate artwork)" — the note rides along
            # in the rarity cell.
            note = ""
            if "//" in rarity_cell:
                rarity_cell, note = rarity_cell.split("//", 1)
            trailing = " ".join(cells[3:])

            # An alternate artwork is a second row for a card id we already saw;
            # the explicit tag confirms it (and covers a first row that is one).
            is_alt = bool(_ALT_ART_RE.search(note) or _ALT_ART_RE.search(trailing))
            if card_id in seen_ids:
                is_alt = True
            seen_ids.add(card_id)

            for token in rarity_cell.split(","):
                token = token.strip()
                if not token:
                    continue
                rarity = _normalize_rarity(token)
                if rarity is None:
                    if token not in unknown:
                        unknown.append(token)
                    continue
                variants.append(
                    ExpectedVariant(
                        card_id=card_id,
                        rarity=rarity,
                        is_alternate_art=is_alt,
                        name_en=name_en,
                    )
                )

    return variants, unknown


def _clean_ja_name(raw: str) -> str:
    """Strip the furigana and link markup wrapped around a Japanese name."""
    name = _RUBY_RE.sub(r"\1", raw)
    name = _WIKILINK_RE.sub(r"\1", name)
    name = re.sub(r"<!--.*?-->", "", name)
    # Trailing template params or comments after the value
    name = name.split("|")[0]
    return name.strip()


def fetch_japanese_names(
    client: httpx.Client, page_titles: list[str]
) -> dict[str, str]:
    """Japanese card names, by English page title.

    The set list only carries English names, but a card created here should
    read like the rest of the collection. Fetched in batches of 50 — the API's
    limit for anonymous multi-page queries.
    """
    names: dict[str, str] = {}
    titles = [t for t in dict.fromkeys(page_titles) if t]
    _lookup(client, titles, names)

    # Two cases where the name lives on another page:
    #   "Dark Magician (Rush Duel)" — ja_name omitted, it is on "Dark Magician"
    #   "… King [L]" / "[R]" — the halves of a Maximum monster share one page,
    #     and the suffix belongs on the Japanese name too, as it does here.
    retry: dict[str, tuple[str, str]] = {}
    for t in titles:
        if t in names:
            continue
        for suffix in (" [L]", " [R]"):
            if t.endswith(suffix):
                retry[t] = (t[: -len(suffix)], suffix.strip())
                break
        else:
            if t.endswith(")") and " (" in t:
                retry[t] = (t.rsplit(" (", 1)[0], "")

    if retry:
        base_names: dict[str, str] = {}
        _lookup(client, list(dict.fromkeys(base for base, _ in retry.values())), base_names)
        for title, (base, suffix) in retry.items():
            if base in base_names:
                names[title] = base_names[base] + suffix

    return names


def _lookup(client: httpx.Client, titles: list[str], out: dict[str, str]) -> None:
    """Fill `out` with ja_name for each title that has one."""
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        resp = client.get(
            API_URL,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "titles": "|".join(batch),
                "format": "json",
                "formatversion": "2",
            },
        )
        resp.raise_for_status()
        for page in resp.json().get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            try:
                revision = page["revisions"][0]
            except (KeyError, IndexError):
                continue
            # yugipedia runs an older MediaWiki: content sits on the revision
            # itself rather than under a slot.
            content = revision.get("content") or revision.get("*", "")
            m = re.search(r"\|\s*ja_name\s*=\s*(.+)", content)
            if m:
                cleaned = _clean_ja_name(m.group(1))
                if cleaned:
                    out[page["title"]] = cleaned


def fetch_set_list(url: str, with_japanese_names: bool = True) -> SetListResult:
    """Read a set's card list, given the set page (or the list page) URL."""
    title = page_title_from_url(url)

    candidates = [title] if title.startswith("Set Card Lists:") else [
        f"Set Card Lists:{title} {suffix}" for suffix in LIST_PAGE_SUFFIXES
    ]

    with _client() as client:
        for candidate in candidates:
            wikitext = _fetch_wikitext(client, candidate)
            if wikitext is None:
                continue
            variants, unknown = parse_set_list(wikitext)
            if not variants:
                continue

            if with_japanese_names:
                names = fetch_japanese_names(client, [v.name_en for v in variants])
                for v in variants:
                    v.name_jp = names.get(v.name_en, "")

            logger.info("%s: %d printings from %s", title, len(variants), candidate)
            return SetListResult(
                list_page=candidate, variants=variants, unknown_rarities=unknown
            )

    raise YugipediaError(
        f"在 yugipedia 找不到「{title}」的卡表子頁"
        f"（試過 {', '.join(LIST_PAGE_SUFFIXES)}）"
    )
