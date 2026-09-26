"""Itinerary schemas (Phase 8, extended for personalized planning in ADR-056).

ComposeItineraryRequest carries NO traveler_id field — it is always
server-derived from the authenticated user (require_traveler), matching
the Phase 7 /recommendations contract (see src/api/v1/itineraries.py).

Personalized planning extends the SAME compose contract via an optional
nested `planning` object (ItineraryPlanningContext) instead of a second
compose endpoint. Starting-location coordinates reuse the existing
origin_lat/origin_lng fields; only the human-readable label is new.

Validation here is authoritative (the web form only mirrors it for UX):
group_size bounds, participants == group_size, sequences exactly 1..N,
integer ages 0-120, controlled gender vocabulary, coordinate ranges.
Invalid input is rejected with 422 — never silently corrected.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from src.core.config import get_settings
from src.core.itinerary_planning import (
    MAX_PARTICIPANT_AGE,
    MIN_PARTICIPANT_AGE,
    SIMILARITY_DEFAULT_LIMIT,
    SIMILARITY_MAX_LIMIT,
    SIMILARITY_MAX_OFFSET,
    AgeBand,
    ParticipantGender,
)

ItineraryStatusLiteral = Literal["DRAFT", "VALIDATED", "BOOKING_REQUESTED", "COMPLETED", "CANCELLED"]
ItinerarySourceLiteral = Literal["COMPOSER", "MANUAL"]
PaceLiteral = Literal["relaxed", "balanced", "packed"]
TravelModeLiteral = Literal["driving", "walking", "cycling"]
AccessibilityLiteral = Literal["wheelchair_accessible", "step_free"]
RouteLegStatusLiteral = Literal["ROUTED", "ESTIMATED", "UNAVAILABLE", "NOT_APPLICABLE"]
RouteSummaryStatusLiteral = Literal["COMPLETE", "PARTIAL", "UNAVAILABLE", "NO_LEGS"]

# Defense-in-depth hard ceiling on list sizes, enforced by Pydantic BEFORE
# any validator runs (rejects a thousand-row payload cheaply). The real,
# configurable business cap is Settings.itinerary_max_participants.
_PARTICIPANTS_HARD_CEILING = 50
_MAX_LIST_ITEMS = 20


class ParticipantInput(BaseModel):
    """One traveler in the group. No name/contact fields — data minimization."""

    model_config = ConfigDict(extra="forbid")

    sequence: StrictInt = Field(ge=1, le=_PARTICIPANTS_HARD_CEILING)
    # StrictInt: 21.5, "21" and true are all rejected, never coerced.
    age_years: StrictInt = Field(ge=MIN_PARTICIPANT_AGE, le=MAX_PARTICIPANT_AGE)
    # Self-described; null = not provided. Context only — never a ranking signal.
    gender: ParticipantGender | None = None


class ItineraryPlanningContext(BaseModel):
    """Group + personalization context carried by both POST
    /itineraries/similar and POST /itineraries/compose."""

    model_config = ConfigDict(extra="forbid")

    group_size: StrictInt = Field(ge=1, le=_PARTICIPANTS_HARD_CEILING)
    participants: list[ParticipantInput] = Field(default_factory=list, max_length=_PARTICIPANTS_HARD_CEILING)
    # Display label for the starting point; its coordinates travel in the
    # compose request's existing origin_lat/origin_lng.
    start_location_label: str | None = Field(default=None, max_length=200)
    # Owner opt-in to let an anonymized summary appear as a similar-plan
    # example for other travelers. Default private.
    is_discoverable: bool = False

    @model_validator(mode="after")
    def _check_group(self) -> ItineraryPlanningContext:
        max_participants = get_settings().itinerary_max_participants
        if self.group_size > max_participants:
            raise ValueError(f"group_size must be at most {max_participants}")
        if len(self.participants) != self.group_size:
            raise ValueError(
                f"participants must contain exactly group_size ({self.group_size}) entries, "
                f"got {len(self.participants)}"
            )
        sequences = [p.sequence for p in self.participants]
        if len(set(sequences)) != len(sequences):
            raise ValueError("participant sequence values must be unique")
        if sorted(sequences) != list(range(1, self.group_size + 1)):
            raise ValueError("participant sequence values must be exactly 1..group_size")
        return self


class ComposeItineraryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(default=None, max_length=500)
    interests: list[str] = Field(default_factory=list, max_length=_MAX_LIST_ITEMS)
    category_slugs: list[str] = Field(default_factory=list, max_length=_MAX_LIST_ITEMS)
    itinerary_date: date
    start_time: time
    end_time: time
    max_experiences: int | None = Field(default=None, ge=1, le=20)
    max_budget: float | None = Field(default=None, ge=0)
    pace: PaceLiteral = "balanced"
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    travel_mode: TravelModeLiteral = "driving"
    party_size: int | None = Field(default=None, ge=1, le=50)
    accessibility_requirements: list[AccessibilityLiteral] = Field(default_factory=list)
    city: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=120)
    # Personalized planning context (optional — the plain compose flow
    # keeps working unchanged without it).
    planning: ItineraryPlanningContext | None = None

    @model_validator(mode="after")
    def _check_window(self) -> ComposeItineraryRequest:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if (self.origin_lat is None) != (self.origin_lng is None):
            raise ValueError("origin_lat and origin_lng must be provided together")
        if (
            self.planning is not None
            and self.party_size is not None
            and self.party_size != self.planning.group_size
        ):
            raise ValueError("party_size must equal planning.group_size when both are provided")
        return self

    @property
    def effective_party_size(self) -> int | None:
        """The group size fed into the EXISTING FeasibilityService capacity
        check (never a second capacity checker)."""
        if self.planning is not None:
            return self.planning.group_size
        return self.party_size


class SimilarItinerariesRequest(BaseModel):
    """POST /itineraries/similar — read-only lookup. Deliberately carries
    no start-location coordinates (not a similarity signal; data
    minimization) and never causes anything to be persisted."""

    model_config = ConfigDict(extra="forbid")

    city: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=120)
    itinerary_date: date
    interests: list[str] = Field(default_factory=list, max_length=_MAX_LIST_ITEMS)
    category_slugs: list[str] = Field(default_factory=list, max_length=_MAX_LIST_ITEMS)
    query: str | None = Field(default=None, max_length=500)
    max_budget: float | None = Field(default=None, ge=0)
    pace: PaceLiteral = "balanced"
    accessibility_requirements: list[AccessibilityLiteral] = Field(default_factory=list)
    planning: ItineraryPlanningContext
    limit: int = Field(default=SIMILARITY_DEFAULT_LIMIT, ge=1, le=SIMILARITY_MAX_LIMIT)
    offset: int = Field(default=0, ge=0, le=SIMILARITY_MAX_OFFSET)

    @model_validator(mode="after")
    def _check_destination(self) -> SimilarItinerariesRequest:
        if not (self.city and self.city.strip()) and not (self.locality and self.locality.strip()):
            raise ValueError("a destination (city or locality) is required")
        return self


class SimilarItinerarySummary(BaseModel):
    """Safe, anonymized preview of a DISCOVERABLE historical itinerary.
    Never includes owner identity, participant ages/genders, narrative
    text, notes, or any field of a private itinerary."""

    model_config = ConfigDict(extra="forbid")

    example_id: str
    destination_label: str | None = None
    duration_days: int = 1
    group_size: int
    pace: str
    interests: list[str] = Field(default_factory=list)
    category_names: list[str] = Field(default_factory=list)
    stop_count: int
    total_distance_km: float | None = None
    total_travel_minutes: float | None = None
    similarity_score: float
    matched_dimensions: list[str] = Field(default_factory=list)


class SimilarItinerariesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Number of previously generated, eligible (non-cancelled, composer-
    # generated, other travelers'), similar itineraries. Private ones
    # count toward this aggregate only — they are never examples.
    similar_count: int
    examples: list[SimilarItinerarySummary] = Field(default_factory=list)
    # How many discoverable examples exist in total (for pagination).
    examples_total: int = 0
    limit: int
    offset: int
    has_more: bool = False


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence: int
    age_years: int
    age_band: AgeBand
    gender: ParticipantGender | None = None


class PlanningProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    destination_label: str | None = None
    # Single-day phase: start_date == end_date == itinerary_date.
    start_date: date
    end_date: date
    duration_days: int = 1
    group_size: int
    children_count: int = 0
    teens_count: int = 0
    adults_count: int = 0
    seniors_count: int = 0
    age_band_distribution: dict[str, int] = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)
    budget_max: float | None = None
    pace: str
    accessibility_requirements: list[str] = Field(default_factory=list)
    travel_mode: str
    start_location_label: str | None = None
    start_location_lat: float | None = None
    start_location_lng: float | None = None


class RoutePoint(BaseModel):
    lat: float
    lng: float
    label: str | None = None


class MapStop(BaseModel):
    """One numbered stop. `sequence` == ItineraryItem.sequence_order
    (1-based) and is the visible stop number everywhere."""

    item_id: str
    sequence: int
    day_index: int = 0
    title: str | None = None
    lat: float | None = None
    lng: float | None = None


class RouteLegResponse(BaseModel):
    """The leg ARRIVING at stop `to_sequence`. distance/duration are only
    populated for ROUTED/ESTIMATED legs and geometry only for ROUTED ones —
    never invented for an UNAVAILABLE leg."""

    to_item_id: str
    to_sequence: int
    from_sequence: int | None = None  # None = departs from the start location
    day_index: int = 0
    origin: RoutePoint | None = None
    destination: RoutePoint | None = None
    status: RouteLegStatusLiteral
    distance_meters: float | None = None
    duration_seconds: float | None = None
    geometry: dict[str, Any] | None = None  # GeoJSON LineString
    routing_source: str | None = None
    travel_mode: str | None = None
    calculated_at: datetime | None = None


class RouteSummaryResponse(BaseModel):
    """Backend-computed totals over ROUTED/ESTIMATED legs only. The
    frontend formats these numbers — it never re-aggregates them."""

    status: RouteSummaryStatusLiteral
    total_distance_meters: float | None = None
    total_duration_seconds: float | None = None
    # "osrm" | "haversine_estimate" | "mixed" | None (nothing routed)
    routing_source: str | None = None
    routing_sources: list[str] = Field(default_factory=list)
    leg_count: int = 0
    routed_leg_count: int = 0
    estimated_leg_count: int = 0
    unavailable_leg_count: int = 0
    stop_count: int = 0
    day_count: int = 1


class ItineraryMapData(BaseModel):
    start_location: RoutePoint | None = None
    stops: list[MapStop] = Field(default_factory=list)
    legs: list[RouteLegResponse] = Field(default_factory=list)
    summary: RouteSummaryResponse


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
    # Route leg arriving at this item (geometry lives in ItineraryResponse.route.legs).
    route_status: RouteLegStatusLiteral | None = None
    route_source: str | None = None

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

    # ─── Personalized planning + route snapshot (ADR-056) ───────────────
    # Only ever returned to the itinerary's owner (every itinerary
    # endpoint is ownership-checked). The list endpoint omits
    # participants and route geometry to stay light.
    is_discoverable: bool = False
    # validation_alias: never auto-read from the ORM relationship (the
    # response adds derived start/end dates) — the route handler sets it.
    planning_profile: PlanningProfileResponse | None = Field(
        default=None, validation_alias="planning_profile_response"
    )
    participants: list[ParticipantResponse] = Field(
        default_factory=list, validation_alias="participants_response"
    )
    route: ItineraryMapData | None = None


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
    travel_mode: TravelModeLiteral = "driving"


__all__ = [
    "AddItineraryItemRequest",
    "ComposeItineraryRequest",
    "CompositionValidationIssue",
    "CompositionValidationResponse",
    "ItineraryItemResponse",
    "ItineraryListResponse",
    "ItineraryMapData",
    "ItineraryPlanningContext",
    "ItineraryResponse",
    "MapStop",
    "ParticipantInput",
    "ParticipantResponse",
    "PlanningProfileResponse",
    "RouteLegResponse",
    "RoutePoint",
    "RouteSummaryResponse",
    "SimilarItinerariesRequest",
    "SimilarItinerariesResponse",
    "SimilarItinerarySummary",
]
