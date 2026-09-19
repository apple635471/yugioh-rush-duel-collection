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


class ProductTypeModel(Base):
    """A product line, and the set_id patterns that put a set in it.

    This table *is* the classification: a set has no stored product type, it
    is whatever these rules say it is (see ``services.product_type_service``).
    Editing a rule therefore re-files every set at once — nothing to migrate.

    Exactly one row is the fallback (``other``): it carries no rules and
    catches every set no other row claims.
    """

    __tablename__ = "product_types"

    code = Column(String, primary_key=True)  # "booster" — used in URLs
    name_en = Column(String, nullable=False, default="")
    name_zh = Column(String)  # None when there isn't a meaningful one
    group_label = Column(String, nullable=False, default="")  # sidebar grouping
    color = Column(String, nullable=False, default="#8C90A3")  # timeline colour
    sort_order = Column(Integer, nullable=False, default=0)
    is_fallback = Column(Boolean, nullable=False, default=False)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    rules = relationship(
        "ProductTypeRuleModel",
        back_populates="product_type",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductTypeRuleModel.sort_order",
    )


class ProductTypeRuleModel(Base):
    """One regular expression matched against a set_id.

    Matched with ``re.search`` and case-insensitively, so an unanchored
    pattern means "contains" (JMP → SJMP / VJMP / WJMP) while an anchored one
    pins the shape (^\d{2}PR$ → 23PR, 24PR, …).
    """

    __tablename__ = "product_type_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_type_code = Column(
        String,
        ForeignKey("product_types.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pattern = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))

    product_type = relationship("ProductTypeModel", back_populates="rules")


class CardSetModel(Base):
    __tablename__ = "card_sets"

    set_id = Column(String, primary_key=True)
    set_name_jp = Column(String, nullable=False, default="")
    set_name_zh = Column(String, nullable=False, default="")
    release_date = Column(String)
    post_url = Column(String, nullable=False, default="")
    # The set's page on yugipedia, entered by the user. Remembered so the card
    # list comparison does not have to be told the URL every time, and used to
    # pull the set's gallery images.
    yugipedia_url = Column(String)
    total_cards = Column(Integer, nullable=False, default=0)
    rarity_distribution = Column(Text)  # JSON string
    is_manual = Column(Boolean, nullable=False, default=False)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    cards = relationship("CardModel", back_populates="card_set", lazy="selectin")

    @property
    def product_type(self) -> str:
        """Which product line this set belongs to, per the rules in the DB.

        A read-only derived value, not a column — so every response schema
        that reads ``product_type`` keeps working unchanged.
        """
        from .services.product_type_service import classify_set

        return classify_set(self.set_id)


class CardSetImageModel(Base):
    """A picture of the set itself — pack shot, promotional poster.

    Fetched from the set's yugipedia gallery and stored on disk, so the app
    does not hotlink someone else's server on every page view.
    """

    __tablename__ = "card_set_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    set_id = Column(String, ForeignKey("card_sets.set_id"), nullable=False, index=True)
    title = Column(String, nullable=False, default="")       # gallery caption
    source_url = Column(String, nullable=False, default="")   # where it came from
    file_path = Column(String, nullable=False)                # relative to SET_IMAGES_DIR
    width = Column(Integer)
    height = Column(Integer)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("set_id", "source_url"),)


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
    maximum_atk = Column(String)
    description = Column(Text)
    summon_condition = Column(Text)
    condition = Column(Text)
    effect = Column(Text)
    continuous_effect = Column(Text)
    is_legend = Column(Boolean, nullable=False, default=False)
    is_manual = Column(Boolean, nullable=False, default=False)
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
    is_alternate_art = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    image_source = Column(String)  # "scraper" or "user_upload"
    image_path = Column(String)  # relative path to current image file
    scraper_image_path = Column(String)  # original scraper path (never overwritten by upload)
    owned_count = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("card_id", "rarity", "is_alternate_art"),)

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


class CardOverrideModel(Base):
    """User overrides for individual card fields.

    When a user manually edits a card field, the override is stored here.
    During import, fields with overrides are NOT overwritten by scraper data.
    For cards with is_manual=True, the entire card is skipped during import.
    """

    __tablename__ = "card_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False, index=True)
    field_name = Column(String, nullable=False)
    value = Column(Text)  # stored as string
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("card_id", "field_name"),)

    card = relationship("CardModel")


class CardVariantOverrideModel(Base):
    """Rarity correction overrides for card variants.

    Protects user edits from being overwritten during reimport:
    - action="remap": when scraper creates a variant with scraper_rarity,
      use target_rarity instead (e.g. wrong "A" → correct "B")
    - action="delete": when scraper would create a variant with scraper_rarity,
      skip it entirely
    """

    __tablename__ = "card_variant_overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False, index=True)
    scraper_rarity = Column(String, nullable=False)  # rarity as seen in scraper data
    action = Column(String, nullable=False)  # "remap" | "delete"
    target_rarity = Column(String, nullable=True)  # used when action="remap"
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
    updated_at = Column(String, nullable=False, server_default=func.datetime("now"))

    __table_args__ = (UniqueConstraint("card_id", "scraper_rarity"),)

    card = relationship("CardModel")


class CardEditModel(Base):
    __tablename__ = "card_edits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("cards.card_id"), nullable=False)
    field_name = Column(String, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    edited_at = Column(String, nullable=False, server_default=func.datetime("now"))
