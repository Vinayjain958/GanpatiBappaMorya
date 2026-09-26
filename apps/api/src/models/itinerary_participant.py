"""ItineraryParticipant model (personalized planning, ADR-056).

One row per traveler in an itinerary's group. Reachable ONLY through its
owning Itinerary (ownership is always derived from Itinerary.traveler_id
— there is no traveler/user id column here to trust or leak).

Data minimization: no names, no contact details — only the age and the
self-described gender the traveler chose to provide. `age_band` is
derived from `age_years` by src/core/itinerary_planning.derive_age_band at
write time (never accepted from a client), and a CHECK constraint keeps
age within the validated range so a contradictory pair can't be stored
through the application.

Gender is context only — it never feeds ranking, similarity, or
feasibility (see src/core/itinerary_planning.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from src.core.db import Base
from src.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.models.itinerary import Itinerary


class ItineraryParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "itinerary_participants"

    itinerary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 1-based position within the group ("Traveler 1", "Traveler 2", ...).
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    age_band: Mapped[str] = mapped_column(String(10), nullable=False)
    # Controlled vocabulary (PARTICIPANT_GENDERS) or NULL = not provided.
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)

    itinerary: Mapped[Itinerary] = relationship(back_populates="participants")

    __table_args__ = (
        UniqueConstraint("itinerary_id", "sequence", name="uq_itinerary_participant_sequence"),
        CheckConstraint("age_years >= 0 AND age_years <= 120", name="ck_itinerary_participant_age_range"),
        CheckConstraint("sequence >= 1", name="ck_itinerary_participant_sequence_positive"),
    )


__all__ = ["ItineraryParticipant"]
