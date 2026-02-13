"""Data models for Rush Duel card scraping."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Card:
    card_id: str  # e.g. "RD/KP01-JP000"
    rarity: str  # e.g. "RR", "UR", "SR", "R", "N", "UR/SER"
    name_jp: str  # Japanese name
    name_zh: str  # Chinese name (Traditional)
    card_type: str  # 通常怪獸, 效果怪獸, 通常魔法, 通常陷阱, etc.
    attribute: Optional[str] = None  # 光, 暗, 炎, 水, 風, 地
    monster_type: Optional[str] = None  # 龍族, 魔法使族, etc.
    level: Optional[int] = None
    atk: Optional[str] = None  # str because some may be "?"
    defense: Optional[str] = None
    condition: Optional[str] = None
    effect: Optional[str] = None
    image_url: Optional[str] = None
    image_file: Optional[str] = None  # relative path to downloaded image
    is_legend: bool = False

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CardSet:
    set_id: str  # e.g. "KP01", "ST01", "LGP1"
    set_name_jp: str
    set_name_zh: str
    product_type: str  # booster, starter, character_pack, battle_pack, etc.
    release_date: Optional[str] = None
    post_url: str = ""
    total_cards: int = 0
    rarity_distribution: dict = field(default_factory=dict)
    cards: list[Card] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cards"] = [c.to_dict() for c in self.cards]
        return d

    def save(self, base_dir: Path) -> None:
        set_dir = base_dir / self.set_id
        set_dir.mkdir(parents=True, exist_ok=True)
        data_file = set_dir / "cards.json"
        data_file.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, base_dir: Path, set_id: str) -> Optional[CardSet]:
        data_file = base_dir / set_id / "cards.json"
        if not data_file.exists():
            return None
        data = json.loads(data_file.read_text(encoding="utf-8"))
        cards = [Card(**c) for c in data.pop("cards", [])]
        cs = cls(**{k: v for k, v in data.items() if k != "cards"})
        cs.cards = cards
        return cs


@dataclass
class ScrapeState:
    """Tracks which posts have been scraped and their last-modified info."""

    posts: dict[str, PostState] = field(default_factory=dict)

    def save(self, path: Path) -> None:
        data = {url: asdict(ps) for url, ps in self.posts.items()}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> ScrapeState:
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        posts = {url: PostState(**ps) for url, ps in data.items()}
        return cls(posts=posts)


@dataclass
class PostState:
    url: str
    title: str
    set_id: str
    last_scraped: str  # ISO timestamp
    content_hash: str  # hash of post HTML to detect changes
    card_count: int = 0
