"""Pydantic schemas for API request/response."""

from __future__ import annotations

from pydantic import BaseModel, field_validator
from typing import Optional


# ── Card Variant ──


class CardVariantOut(BaseModel):
    id: int
    card_id: str
    rarity: str
    is_alternate_art: bool = False
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
    maximum_atk: Optional[str] = None
    description: Optional[str] = None
    summon_condition: Optional[str] = None
    condition: Optional[str] = None
    effect: Optional[str] = None
    continuous_effect: Optional[str] = None
    is_legend: bool = False
    is_manual: bool = False
    original_rarity_string: str = ""
    variants: list[CardVariantOut] = []

    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    """Create a new card with one initial variant."""

    card_id: str
    set_id: str

    @field_validator("card_id", "set_id", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v
    name_jp: str = ""
    name_zh: str = ""
    card_type: str = ""
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level: Optional[int] = None
    atk: Optional[str] = None
    defense: Optional[str] = None
    maximum_atk: Optional[str] = None
    description: Optional[str] = None
    summon_condition: Optional[str] = None
    condition: Optional[str] = None
    effect: Optional[str] = None
    continuous_effect: Optional[str] = None
    is_legend: bool = False
    rarity: str = "N"


class VariantCreate(BaseModel):
    """Add a new rarity variant to an existing card."""

    rarity: str
    is_alternate_art: bool = False


class VariantRarityUpdate(BaseModel):
    """Change the rarity of an existing variant."""

    new_rarity: str


class NextCardIdOut(BaseModel):
    next_card_id: str


class CardUpdate(BaseModel):
    name_jp: Optional[str] = None
    name_zh: Optional[str] = None
    card_type: Optional[str] = None
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level: Optional[int] = None
    atk: Optional[str] = None
    defense: Optional[str] = None
    maximum_atk: Optional[str] = None
    description: Optional[str] = None
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
    is_manual: bool = False

    class Config:
        from_attributes = True


class CardSetCreate(BaseModel):
    """Create a new card set manually."""

    set_id: str
    set_name_jp: str = ""
    set_name_zh: str = ""
    product_type: str = "other"
    release_date: Optional[str] = None


class CardSetUpdate(BaseModel):
    """Partial update for card set metadata.

    Only provided fields will be updated and stored as overrides.
    total_cards and rarity_distribution are auto-computed from card data, not editable.
    """

    set_name_jp: Optional[str] = None
    set_name_zh: Optional[str] = None
    product_type: Optional[str] = None
    release_date: Optional[str] = None


class CardSetOverrideOut(BaseModel):
    set_id: str
    field_name: str
    value: Optional[str] = None
    updated_at: str

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
