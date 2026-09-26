"""ItineraryPlanningProfile model (personalized planning, ADR-056).

A normalized snapshot of the planning context that produced one
successfully generated itinerary (1:1 with Itinerary). Its purpose is to
let ItinerarySimilarityService compare historical generated trips
deterministically WITHOUT loading full itinerary/participant graphs —
the similarity query selects only these columns.

Deliberately NOT duplicated here (read from Itinerary instead):
  - itinerary_date / start_time / end_time (Itinerary is single-day in
    this phase, so start_date == end_date == itinerary_date and
    duration_days is always 1 — no columns for them; a future multi-day
    migration adds them here),
  - discoverability (Itinerary.is_discoverable is the single privacy flag),
  - traveler/owner (always derived through Itinerary.traveler_id).

Group signals are aggregate counts only (no gender, no per-person rows)
so similarity never needs to touch ItineraryParticipant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import Index

from src.core.db import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.itinerary import Itinerary


class ItineraryPlanningProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "itinerary_planning_profiles"

    itinerary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # normalize_destination(city, locality): "mumbai" or "mumbai|fort".
    destination_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    destination_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    group_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    teens_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adults_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seniors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    age_band_distribution: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)

    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    pace: Mapped[str] = mapped_column(String(20), nullable=False, default="balanced")
    accessibility_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    travel_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="driving")
    # 1-12, the trip month — weak "season" similarity signal.
    trip_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Starting location the route's first leg departs from. Coordinates
    # are the ones the traveler explicitly chose (search result or an
    # explicit "use my location") — stored rounded to ~11m (4 dp) because
    # precise location isn't needed to render a city-scale route.
    start_location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_location_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    similarity_signature: Mapped[str] = mapped_column(String(40), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(40), nullable=False)

    itinerary: Mapped[Itinerary] = relationship(back_populates="planning_profile")

    __table_args__ = (
        Index("ix_itinerary_planning_profiles_destination_key", "destination_key"),
    )


__all__ = ["ItineraryPlanningProfile"]
