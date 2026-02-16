"""SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class CardSetModel(Base):
    __tablename__ = "card_sets"

    set_id = Column(String, primary_key=True)
    set_name_jp = Column(String, nullable=False, default="")
    set_name_zh = Column(String, nullable=False, default="")
    product_type = Column(String, nullable=False, index=True)
    release_date = Column(String)
    post_url = Column(String, nullable=False, default="")
    total_cards = Column(Integer, nullable=False, default=0)
    rarity_distribution = Column(Text)  # JSON string
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    cards = relationship("CardModel", back_populates="card_set", lazy="selectin")


class CardModel(Base):
    __tablename__ = "cards"

    card_id = Column(String, primary_key=True)
    set_id = Column(String, ForeignKey("card_sets.set_id"), nullable=False, index=True)
    name_jp = Column(String, nullable=False, default="")
    name_zh = Column(String, nullable=False, default="")
    card_type = Column(String, nullable=False, default="", index=True)
    attribute = Column(String)
    monster_type = Column(String)
    level = Column(Integer)
    atk = Column(String)
    defense = Column(String)
    summon_condition = Column(Text)
    condition = Column(Text)
    effect = Column(Text)
    continuous_effect = Column(Text)
    is_legend = Column(Boolean, nullable=False, default=False)
    original_rarity_string = Column(String, nullable=False, default="")
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    card_set = relationship("CardSetModel", back_populates="cards")
    variants = relationship("CardVariantModel", back_populates="card", lazy="selectin")


class CardVariantModel(Base):
    __tablename__ = "card_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False, index=True)
    rarity = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    image_source = Column(String)  # "scraper" or "user_upload"
    image_path = Column(String)  # relative path to current image file
    scraper_image_path = Column(String)  # original scraper path (never overwritten by upload)
    owned_count = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("card_id", "rarity"),)

    card = relationship("CardModel", back_populates="variants")


class CardSetOverrideModel(Base):
    """User overrides for card set metadata fields.

    When a user manually edits a card set field, the override is stored here.
    During import, fields with overrides are NOT overwritten by scraper data.
    Deleting an override reverts the field to the scraper value on next import.
    """

    __tablename__ = "card_set_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    set_id = Column(String, ForeignKey("card_sets.set_id"), nullable=False, index=True)
    field_name = Column(String, nullable=False)
    value = Column(Text)  # stored as string; JSON for rarity_distribution
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("set_id", "field_name"),)

    card_set = relationship("CardSetModel")


class CardEditModel(Base):
    __tablename__ = "card_edits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False)
    field_name = Column(String, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    edited_at = Column(String, nullable=False, server_default=func.datetime("now"))
