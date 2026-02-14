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
    condition = Column(Text)
    effect = Column(Text)
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
    image_path = Column(String)  # relative path to image file
    owned_count = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("card_id", "rarity"),)

    card = relationship("CardModel", back_populates="variants")


class CardEditModel(Base):
    __tablename__ = "card_edits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False)
    field_name = Column(String, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    edited_at = Column(String, nullable=False, server_default=func.datetime("now"))
