"""ItineraryItem model (Phase 8).

One scheduled experience slot inside an Itinerary. References the
canonical Experience by id only (never duplicates its row) — the
composer/validator always re-load the live Experience when they need its
current facts (docs/AI_CONTEXT.md: single source of truth for catalog
data). Items are only reachable through their owning Itinerary.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import Index, UniqueConstraint

from src.core.db import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.itinerary import Itinerary


class ItineraryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "itinerary_items"

    itinerary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experience_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiences.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Travel FROM the previous item TO this one. Null for the first item,
    # or when travel time genuinely could not be determined (UNKNOWN) —
    # never defaulted to 0, see src/services/experience_composer.py.
    travel_from_previous_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    travel_from_previous_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    travel_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    buffer_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Provenance from the Phase 7 ranked candidate this item was selected
    # from — never recomputed by the composer, only carried through.
    source_rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_ranking_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Gemini per-item narrative text (facts-only — see itinerary_narrator.py).
    narrative_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # ─── Phase 9: locking, replan provenance ──────────────────────────────
    # A locked item is never auto-replaced by ReplanningService — a hard
    # invalidation on a locked item surfaces REQUIRES_USER_ACTION instead
    # of a silent swap (see src/services/replanning.py).
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # ACTIVE | AFFECTED | INVALIDATED | CANCELLED — set by
    # ContextImpactService/ReplanningService; never edited by Gemini.
    item_state: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    # ─── Route leg snapshot (ADR-056) ─────────────────────────────────────
    # Each item stores the route leg that ARRIVES at it (from the previous
    # stop, or from the planning profile's start location for stop 1).
    # A single-day itinerary is one linear sequence, so exactly one leg
    # per item — no separate ItineraryRouteLeg table (that would duplicate
    # travel_from_previous_distance_km/minutes, which remain the leg's
    # distance/duration). Written by src/services/itinerary_routes.py
    # only; never recomputed on GET.
    #
    # route_status: ROUTED (real routing-adapter result, geometry when the
    # provider returned one) | ESTIMATED (explicitly labelled haversine
    # estimate — never drawn as a road route) | UNAVAILABLE (routing
    # failed: NoRoute/timeout/provider error — no distance/time/geometry
    # is claimed) | NOT_APPLICABLE (first stop with no start location).
    route_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    route_source: Mapped[str | None] = mapped_column(String(30), nullable=True)  # "osrm" | "haversine_estimate"
    route_geometry: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # GeoJSON LineString
    # Identifies the waypoint pair + mode this leg was computed for; a
    # mismatch after a replan means the leg is stale and is recomputed.
    route_waypoint_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    route_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    itinerary: Mapped[Itinerary] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("itinerary_id", "sequence_order", name="uq_itinerary_item_sequence"),
        Index("ix_itinerary_items_itinerary_id_experience_id", "itinerary_id", "experience_id"),
    )


__all__ = ["ItineraryItem"]
