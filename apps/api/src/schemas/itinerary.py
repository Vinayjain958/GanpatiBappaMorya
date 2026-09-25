"""Itinerary schemas (Phase 8).

ComposeItineraryRequest carries NO traveler_id field — it is always
server-derived from the authenticated user (require_traveler), matching
the Phase 7 /recommendations contract (see src/api/v1/itineraries.py).
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ItineraryStatusLiteral = Literal["DRAFT", "VALIDATED", "BOOKING_REQUESTED", "COMPLETED", "CANCELLED"]
ItinerarySourceLiteral = Literal["COMPOSER", "MANUAL"]
PaceLiteral = Literal["relaxed", "balanced", "packed"]


class ComposeItineraryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    interests: list[str] = Field(default_factory=list)
    category_slugs: list[str] = Field(default_factory=list)
    itinerary_date: date
    start_time: time
    end_time: time
    max_experiences: int | None = Field(default=None, ge=1, le=20)
    max_budget: float | None = Field(default=None, ge=0)
    pace: PaceLiteral = "balanced"
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    travel_mode: Literal["driving", "walking", "cycling"] = "driving"
    party_size: int | None = Field(default=None, ge=1, le=50)
    accessibility_requirements: list[Literal["wheelchair_accessible", "step_free"]] = Field(
        default_factory=list
    )
    city: str | None = None
    locality: str | None = None

    @model_validator(mode="after")
    def _check_window(self) -> ComposeItineraryRequest:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ItineraryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experience_id: str
    sequence_order: int
    planned_start: datetime
    planned_end: datetime
    duration_minutes: int
    travel_from_previous_minutes: float | None = None
    travel_from_previous_distance_km: float | None = None
    travel_mode: str | None = None
    buffer_before_minutes: int
    buffer_after_minutes: int
    estimated_cost: float | None = None
    source_rank_position: int | None = None
    source_ranking_score: float | None = None
    narrative_text: str | None = None
    is_locked: bool = False
    item_state: str = "ACTIVE"

    # Denormalized display facts (never authoritative pricing/hours source
    # — populated from the canonical Experience at response-build time).
    title: str | None = None
    short_description: str | None = None
    category_name: str | None = None
    location_place_name: str | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    traveler_id: str
    title: str
    itinerary_date: date
    start_time: time
    end_time: time
    status: ItineraryStatusLiteral
    source: ItinerarySourceLiteral
    total_duration_minutes: int | None = None
    total_travel_minutes: float | None = None
    estimated_total_cost: float | None = None
    currency: str
    narrative_title: str | None = None
    narrative_summary: str | None = None
    narrative_closing_message: str | None = None
    ranking_model_version: str | None = None
    narrative_model_version: str | None = None
    generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[ItineraryItemResponse] = Field(default_factory=list)

    # ─── Phase 9: versioning/replanning state ───────────────────────────
    version: int = 1
    replanning_status: str = "STABLE"
    context_last_updated_at: datetime | None = None


class ItineraryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ItineraryResponse]
    total: int


class CompositionValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    constraint: str
    message: str
    evidence: dict[str, object] = Field(default_factory=dict)


class CompositionValidationResponse(BaseModel):
    """Returned instead of an ItineraryResponse when composition could not
    produce a valid plan — never a forced/partial itinerary."""

    model_config = ConfigDict(extra="forbid")

    valid: bool = False
    reason_code: str
    message: str
    issues: list[CompositionValidationIssue] = Field(default_factory=list)
    candidate_count: int = 0
    feasible_count: int = 0


class AddItineraryItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str
    planned_start: datetime | None = None
    travel_mode: Literal["driving", "walking", "cycling"] = "driving"


__all__ = [
    "AddItineraryItemRequest",
    "ComposeItineraryRequest",
    "CompositionValidationIssue",
    "CompositionValidationResponse",
    "ItineraryItemResponse",
    "ItineraryListResponse",
    "ItineraryResponse",
]
