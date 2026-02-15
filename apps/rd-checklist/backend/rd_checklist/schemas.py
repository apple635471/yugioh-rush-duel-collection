"""Pydantic schemas for API request/response."""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


# ── Card Variant ──


class CardVariantOut(BaseModel):
    id: int
    card_id: str
    rarity: str
    sort_order: int
    image_source: Optional[str] = None
    image_path: Optional[str] = None
    owned_count: int = 0

    class Config:
        from_attributes = True


# ── Card ──


class CardOut(BaseModel):
    card_id: str
    set_id: str
    name_jp: str
    name_zh: str
    card_type: str
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level: Optional[int] = None
    atk: Optional[str] = None
    defense: Optional[str] = None
    summon_condition: Optional[str] = None
    condition: Optional[str] = None
    effect: Optional[str] = None
    continuous_effect: Optional[str] = None
    is_legend: bool = False
    original_rarity_string: str = ""
    variants: list[CardVariantOut] = []

    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    name_jp: Optional[str] = None
    name_zh: Optional[str] = None
    card_type: Optional[str] = None
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level: Optional[int] = None
    atk: Optional[str] = None
    defense: Optional[str] = None
    summon_condition: Optional[str] = None
    condition: Optional[str] = None
    effect: Optional[str] = None
    continuous_effect: Optional[str] = None


# ── Card Set ──


class CardSetOut(BaseModel):
    set_id: str
    set_name_jp: str
    set_name_zh: str
    product_type: str
    release_date: Optional[str] = None
    post_url: str = ""
    total_cards: int = 0
    rarity_distribution: Optional[str] = None

    class Config:
        from_attributes = True


class CardSetWithCardsOut(CardSetOut):
    cards: list[CardOut] = []


class ProductTypeOut(BaseModel):
    product_type: str
    display_name: str
    set_count: int


# ── Ownership ──


class OwnershipUpdate(BaseModel):
    owned_count: int


class OwnershipBatchItem(BaseModel):
    card_id: str
    rarity: str
    owned_count: int


class OwnershipBatchUpdate(BaseModel):
    updates: list[OwnershipBatchItem]


class OwnershipStatsOut(BaseModel):
    total_variants: int
    owned_variants: int
    total_owned_copies: int


# ── Search ──


class SearchParams(BaseModel):
    q: Optional[str] = None
    card_type: Optional[str] = None
    attribute: Optional[str] = None
    level: Optional[int] = None
    set_id: Optional[str] = None
    rarity: Optional[str] = None
    owned: Optional[str] = None  # "all", "owned", "missing"
    limit: int = 100
    offset: int = 0


# ── Import ──


class ImportResult(BaseModel):
    sets_imported: int
    cards_imported: int
    variants_created: int
    message: str
