from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.mixins import ProvenanceMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.availability import ExperienceAvailability
    from src.models.category import ExperienceCategory
    from src.models.embedding import ExperienceEmbedding
    from src.models.location import Location
    from src.models.opening_hour import ExperienceOpeningHour
    from src.models.provider import Provider
    from src.models.interaction import TravelerInteraction

ExperienceStatus = Enum(
    "active", "draft", "inactive", name="experience_status", native_enum=False
)
VerificationStatus = Enum(
    "unverified", "catalog_imported", "curated", "verified",
    name="experience_verification_status", native_enum=False,
)
PriceType = Enum(
    "fixed", "range", "free", "unknown", name="experience_price_type", native_enum=False
)


class Experience(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """A discoverable local experience.

    Populated from two lineages (see data/README.md):
      1. Overture Places → normalized → enriched (is_synthetic=False, is_enriched=True)
      2. LocaLens synthetic templates (is_synthetic=True)

    Fields with a `_source`/`_estimated`/`_confidence` counterpart exist so
    the API and frontend can distinguish a verified source fact from a
    LocaLens-derived estimate. Nothing here decides feasibility or ranking
    — that is Phase 6/7.
    """

    __tablename__ = "experiences"
    __table_args__ = (
        UniqueConstraint("source_type", "source_record_id", name="uq_experience_source_record"),
    )

    provider_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experience_categories.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    short_description: Mapped[str] = mapped_column(String(300), nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_type: Mapped[str] = mapped_column(PriceType, default="unknown", nullable=False)
    price_source: Mapped[str] = mapped_column(String(20), default="unavailable", nullable=False)
    price_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_price_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    minimum_group_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maximum_group_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(ExperienceStatus, default="active", nullable=False)
    verification_status: Mapped[str] = mapped_column(
        VerificationStatus, default="unverified", nullable=False
    )

    wheelchair_accessible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    step_free: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    accessibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    suitability: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    opening_hours_status: Mapped[str] = mapped_column(
        String(20), default="unavailable", nullable=False
    )

    provider: Mapped[Provider] = relationship(back_populates="experiences")
    category: Mapped[ExperienceCategory] = relationship(back_populates="experiences")
    location: Mapped[Location] = relationship(back_populates="experiences")
    opening_hours: Mapped[list[ExperienceOpeningHour]] = relationship(
        back_populates="experience",
        cascade="all, delete-orphan",
        order_by="ExperienceOpeningHour.day_of_week",
    )
    # Phase 3 ExperienceAvailability declares its own relationship() with no
    # back_populates (see models/availability.py); this side is added in
    # Phase 6 so FeasibilityService/repositories can eager-load slots via
    # `Experience.availability_slots` without a second query pattern.
    availability_slots: Mapped[list[ExperienceAvailability]] = relationship(
        back_populates="experience",
        cascade="all, delete-orphan",
        order_by="ExperienceAvailability.starts_at",
    )
    embedding: Mapped[ExperienceEmbedding | None] = relationship(
        back_populates="experience", cascade="all, delete-orphan", uselist=False
    )
    interactions: Mapped[list["TravelerInteraction"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan"
    )
