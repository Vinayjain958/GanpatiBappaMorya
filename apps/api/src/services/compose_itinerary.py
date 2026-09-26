"""Orchestrates the full Phase 8 pipeline for one compose request:

RETRIEVAL -> FEASIBILITY -> RANKING -> COMPOSITION -> POST-COMPOSITION
VALIDATION -> ROUTE LEGS -> NARRATIVE -> persist (itinerary + items with
route snapshot + planning profile + participants).

Personalized planning (ADR-056) only EXTENDS this pipeline's inputs:
  - planning.group_size is fed as party_size into the existing
    FeasibilityService capacity/maximum_group_size check (both the
    candidate gate and the post-composition validator) — never a second
    capacity checker;
  - participant ages/genders are persisted as context. They do NOT alter
    retrieval, ranking or feasibility: the catalog has no authoritative
    age-restriction fields, so age can't be used without fabricating
    restrictions, and gender is never a preference signal;
  - the route pass (src/services/itinerary_routes.py) runs after
    validation on the FINAL sequence only.

This module — not the route handler — owns the ordering invariant so it
can be reused identically by both POST /itineraries/compose and the
compose_experience Gemini tool (src/services/ai_tools.py), which must
never re-run the Phase 6/7 pipeline redundantly when a valid ranked
candidate context is already available (see execute_compose_experience).
"""

from __future__ import annotations

import logging
import time as time_module
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.ai import AIAdapter
from src.adapters.embedding import EmbeddingAdapter
from src.adapters.routing import RoutingAdapter
from src.core.config import Settings
from src.core.feasibility_reasons import FeasibilityReasonCode
from src.core.itinerary_planning import (
    PLANNING_PROFILE_VERSION,
    derive_age_band,
    destination_label,
    interest_terms,
    similarity_signature,
)
from src.models.experience import Experience
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.models.itinerary_participant import ItineraryParticipant
from src.models.itinerary_planning_profile import ItineraryPlanningProfile
from src.repositories.experience_repository import ExperienceRepository
from src.repositories.itinerary_repository import ItineraryRepository
from src.schemas.itinerary import ComposeItineraryRequest
from src.schemas.ranking import RankedExperienceItem
from src.services.discovery_pipeline import DiscoveryPipelineService
from src.services.experience_composer import ComposedItem, ExperienceComposerService
from src.services.itinerary_narrator import ItineraryNarratorService
from src.services.itinerary_routes import ItineraryRouteService
from src.services.itinerary_similarity import build_normalized_profile
from src.services.itinerary_validator import ItineraryValidatorService, ValidationIssue

logger = logging.getLogger(__name__)

_DEFAULT_TZ = "Asia/Kolkata"


@dataclass
class ComposeOutcome:
    valid: bool
    itinerary: Itinerary | None = None
    reason_code: str | None = None
    message: str | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    candidate_count: int = 0
    feasible_count: int = 0


async def _get_ranked_feasible_candidates(
    *,
    session: AsyncSession,
    settings: Settings,
    embedding_adapter: EmbeddingAdapter | None,
    routing_adapter: RoutingAdapter,
    traveler_id: str,
    request: ComposeItineraryRequest,
) -> tuple[list[RankedExperienceItem], int, int]:
    """Runs the Phase 6+7 pipeline exactly once and returns only FEASIBLE,
    ranked candidates. Returns (ranked_items, candidate_count, feasible_count)."""
    from src.schemas.feasibility import TravelerConstraints

    pipeline = DiscoveryPipelineService(session, settings, embedding_adapter, routing_adapter)
    # available_date is passed (filters out day-of-week closures), but
    # available_start/available_end are NOT: FeasibilityService's
    # opening-hours/availability checks require full CONTAINMENT of
    # whatever window is supplied (correct for verifying one specific
    # visit), and default an omitted start/end to the full 00:00-23:59
    # day — which would wrongly require every candidate to be open/
    # bookable across the traveler's *entire* day, when only whatever
    # specific slot the composer eventually schedules it into matters.
    # ItineraryValidatorService re-runs the full precise check against
    # each item's actual planned start/end after composition — that is
    # the mandatory, authoritative gate for per-slot time fit.
    constraints = TravelerConstraints(
        budget_max=request.max_budget,
        party_size=request.effective_party_size,
        available_date=request.itinerary_date,
        origin_lat=request.origin_lat,
        origin_lng=request.origin_lng,
        travel_mode=request.travel_mode,
        accessibility_requirements=request.accessibility_requirements,
    )
    category_slug = request.category_slugs[0] if request.category_slugs else None
    result, ranked_items = await pipeline.run_with_ranking(
        traveler_id=traveler_id,
        raw_query=request.query,
        interests=request.interests or None,
        category_slug=category_slug,
        city=request.city,
        locality=request.locality,
        constraints=constraints,
        limit=settings.composer_max_candidates,
        travel_profile=request.travel_mode,
    )
    return ranked_items, result.candidate_count, result.feasible_count


async def compose_and_persist_itinerary(
    *,
    session: AsyncSession,
    settings: Settings,
    routing_adapter: RoutingAdapter,
    embedding_adapter: EmbeddingAdapter | None,
    ai_adapter: AIAdapter,
    traveler_id: str,
    request: ComposeItineraryRequest,
    ranked_candidates: list[RankedExperienceItem] | None = None,
) -> ComposeOutcome:
    started = time_module.monotonic()
    logger.info(
        "event=itinerary_generation_started personalized=%s group_size=%s has_start_location=%s",
        request.planning is not None, request.effective_party_size, request.origin_lat is not None,
    )
    outcome = await _compose_and_persist(
        session=session,
        settings=settings,
        routing_adapter=routing_adapter,
        embedding_adapter=embedding_adapter,
        ai_adapter=ai_adapter,
        traveler_id=traveler_id,
        request=request,
        ranked_candidates=ranked_candidates,
    )
    logger.info(
        "event=itinerary_generation_completed valid=%s reason_code=%s items=%d duration_ms=%d",
        outcome.valid, outcome.reason_code,
        len(outcome.itinerary.items) if outcome.itinerary is not None else 0,
        int((time_module.monotonic() - started) * 1000),
    )
    return outcome


async def _compose_and_persist(
    *,
    session: AsyncSession,
    settings: Settings,
    routing_adapter: RoutingAdapter,
    embedding_adapter: EmbeddingAdapter | None,
    ai_adapter: AIAdapter,
    traveler_id: str,
    request: ComposeItineraryRequest,
    ranked_candidates: list[RankedExperienceItem] | None,
) -> ComposeOutcome:
    if ranked_candidates is None:
        ranked_candidates, candidate_count, feasible_count = await _get_ranked_feasible_candidates(
            session=session,
            settings=settings,
            embedding_adapter=embedding_adapter,
            routing_adapter=routing_adapter,
            traveler_id=traveler_id,
            request=request,
        )
    else:
        candidate_count = len(ranked_candidates)
        feasible_count = len(ranked_candidates)

    if not ranked_candidates:
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="No feasible experiences were found for the given constraints.",
            candidate_count=candidate_count,
            feasible_count=feasible_count,
        )

    composer = ExperienceComposerService(settings, routing_adapter)
    exp_repo = ExperienceRepository(session)
    validator = ItineraryValidatorService(routing_adapter)
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(_DEFAULT_TZ)
    requested_start = datetime.combine(request.itinerary_date, request.start_time, tzinfo=tz)
    requested_end = datetime.combine(request.itinerary_date, request.end_time, tzinfo=tz)

    # The composer's greedy/local-improvement stages check time window,
    # travel time, and budget, but not a candidate's precise opening-hours
    # /availability fit at its specific proposed slot (that data isn't on
    # the flat RankedExperienceItem candidates it works from). The
    # mandatory post-composition validator re-checks each item against
    # real Experience data at its actual planned start/end and is the
    # authoritative, precise gate. When it rejects a specific item as no
    # longer feasible at its assigned slot, exclude that one experience
    # and recompose from the remaining pool — bounded, deterministic,
    # never silently accepting an invalid plan (docs Section 20 step 20).
    excluded_ids: set[str] = set()
    composition = None
    validation = None
    attempts = 0
    max_attempts = max(1, settings.composer_max_validation_retries)

    while attempts < max_attempts:
        attempts += 1
        pool = [c for c in ranked_candidates if c.id not in excluded_ids]
        if not pool:
            break

        composition = await composer.compose(
            candidates=pool,
            itinerary_date=request.itinerary_date,
            start_time_of_day=request.start_time,
            end_time_of_day=request.end_time,
            max_experiences=request.max_experiences,
            max_budget=request.max_budget,
            travel_mode=request.travel_mode,
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
        )

        if not composition.items:
            break

        experiences_by_id = {}
        for item in composition.items:
            exp = await exp_repo.get_by_id(item.experience.id)
            if exp is not None:
                experiences_by_id[item.experience.id] = exp

        validation = await validator.validate(
            items=composition.items,
            experiences_by_id=experiences_by_id,
            requested_start=requested_start,
            requested_end=requested_end,
            max_budget=request.max_budget,
            max_experiences=request.max_experiences,
            party_size=request.effective_party_size,
            travel_mode=request.travel_mode,
        )

        if validation.valid:
            break

        newly_excluded = {
            str(issue.evidence["experience_id"])
            for issue in validation.issues
            if issue.code == FeasibilityReasonCode.EXPERIENCE_NOT_FEASIBLE and "experience_id" in issue.evidence
        }
        if not newly_excluded or newly_excluded <= excluded_ids:
            # Nothing new to exclude (a non-per-item issue, e.g. budget/
            # count) — retrying with the same pool would repeat forever.
            break
        excluded_ids |= newly_excluded

    if composition is None or not composition.items:
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="No combination of feasible experiences fit the requested time window and constraints.",
            candidate_count=candidate_count,
            feasible_count=feasible_count,
        )

    if validation is None or not validation.valid:
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="The composed itinerary failed validation.",
            issues=validation.issues if validation else [],
            candidate_count=candidate_count,
            feasible_count=feasible_count,
        )

    # Route legs for the FINAL, validated sequence (start location -> stop
    # 1 -> ... -> stop N). Built on unattached item rows so the snapshot
    # is persisted in the same transaction as the itinerary itself.
    item_rows = [
        ItineraryItem(
            id=str(uuid.uuid4()),
            experience_id=composed.experience.id,
            sequence_order=composed.sequence_order,
            planned_start=composed.planned_start,
            planned_end=composed.planned_end,
            duration_minutes=composed.duration_minutes,
            travel_from_previous_minutes=composed.travel_from_previous_minutes,
            travel_from_previous_distance_km=composed.travel_from_previous_distance_km,
            travel_mode=composed.travel_mode,
            buffer_before_minutes=composed.buffer_before_minutes,
            buffer_after_minutes=composed.buffer_after_minutes,
            estimated_cost=composed.estimated_cost,
            source_rank_position=composed.source_rank_position,
            source_ranking_score=composed.source_ranking_score,
        )
        for composed in composition.items
    ]
    # Same 4-dp rounding the planning profile persists, so a later replan
    # re-derives an identical first-leg waypoint key (no needless re-route).
    start_location = (
        (round(request.origin_lat, 4), round(request.origin_lng, 4))
        if request.origin_lat is not None and request.origin_lng is not None
        else None
    )
    await ItineraryRouteService(routing_adapter).refresh_item_legs(
        items=item_rows,
        coordinates_by_item_id={
            row.id: (composed.experience.location.latitude, composed.experience.location.longitude)
            for row, composed in zip(item_rows, composition.items, strict=True)
        },
        start_location=start_location,
        travel_mode=request.travel_mode,
    )
    # Keep the narrator's facts consistent with the persisted legs.
    for row, composed in zip(item_rows, composition.items, strict=True):
        composed.travel_from_previous_minutes = row.travel_from_previous_minutes
        composed.travel_from_previous_distance_km = row.travel_from_previous_distance_km
    composition.total_travel_minutes = sum(r.travel_from_previous_minutes or 0.0 for r in item_rows)

    narrator = ItineraryNarratorService(ai_adapter, settings)
    outcome_narration = await narrator.narrate(
        items=composition.items,
        itinerary_date_str=request.itinerary_date.isoformat(),
        currency="INR",
        total_cost=composition.estimated_total_cost,
        booking_statuses={},
    )

    itinerary = Itinerary(
        traveler_id=traveler_id,
        title=outcome_narration.narrative.title,
        itinerary_date=request.itinerary_date,
        start_time=request.start_time,
        end_time=request.end_time,
        status="VALIDATED",
        source="COMPOSER",
        total_duration_minutes=composition.total_duration_minutes,
        total_travel_minutes=composition.total_travel_minutes,
        estimated_total_cost=composition.estimated_total_cost,
        currency="INR",
        narrative_title=outcome_narration.narrative.title,
        narrative_summary=outcome_narration.narrative.summary,
        narrative_closing_message=outcome_narration.narrative.closing_message,
        ranking_model_version=settings.ranking_model_version,
        narrative_model_version=outcome_narration.model_version,
        generated_at=datetime.now(tz),
        is_discoverable=request.planning.is_discoverable if request.planning is not None else False,
    )
    ItineraryRepository(session).add(itinerary)
    await session.flush()

    narrative_by_id = {n.experience_id: n.text for n in outcome_narration.narrative.item_narratives}
    for item_row in item_rows:
        item_row.itinerary_id = itinerary.id
        item_row.narrative_text = narrative_by_id.get(item_row.experience_id)
        session.add(item_row)

    session.add(_build_planning_profile(itinerary.id, request))
    if request.planning is not None:
        for participant in request.planning.participants:
            session.add(
                ItineraryParticipant(
                    itinerary_id=itinerary.id,
                    sequence=participant.sequence,
                    age_years=participant.age_years,
                    age_band=derive_age_band(participant.age_years),  # derived, never client-supplied
                    gender=participant.gender,
                )
            )

    await session.commit()
    await session.refresh(itinerary, attribute_names=["items", "participants", "planning_profile"])

    return ComposeOutcome(
        valid=True,
        itinerary=itinerary,
        candidate_count=candidate_count,
        feasible_count=feasible_count,
    )


def _build_planning_profile(itinerary_id: str, request: ComposeItineraryRequest) -> ItineraryPlanningProfile:
    """Normalized snapshot used later by ItinerarySimilarityService. Uses
    the exact same normalization as the similarity query side
    (build_normalized_profile + interest_terms)."""
    normalized = build_normalized_profile(
        city=request.city,
        locality=request.locality,
        itinerary_date=request.itinerary_date,
        interests=interest_terms(request.interests, request.query),
        category_slugs=request.category_slugs,
        max_budget=request.max_budget,
        pace=request.pace,
        accessibility_requirements=list(request.accessibility_requirements),
        planning=request.planning,
        party_size=request.party_size,
    )
    group = normalized.group
    signature = similarity_signature(
        {
            "destination": normalized.destination_key,
            "group_size": group.group_size,
            "age_bands": group.age_band_distribution,
            "interests": list(normalized.interests),
            "budget_max": normalized.budget_max,
            "pace": normalized.pace,
            "accessibility": list(normalized.accessibility),
            "trip_month": normalized.trip_month,
            "duration_days": normalized.duration_days,
            "version": PLANNING_PROFILE_VERSION,
        }
    )
    has_start = request.origin_lat is not None and request.origin_lng is not None
    return ItineraryPlanningProfile(
        itinerary_id=itinerary_id,
        destination_key=normalized.destination_key,
        destination_label=destination_label(request.city, request.locality),
        group_size=group.group_size,
        children_count=group.children_count,
        teens_count=group.teens_count,
        adults_count=group.adults_count,
        seniors_count=group.seniors_count,
        age_band_distribution=dict(group.age_band_distribution),
        interests=list(normalized.interests),
        budget_max=normalized.budget_max,
        pace=normalized.pace,
        accessibility_requirements=list(normalized.accessibility),
        travel_mode=request.travel_mode,
        trip_month=normalized.trip_month,
        # ~11 m precision is plenty for a city-scale route start; no need
        # to persist the browser's full-precision fix.
        start_location_lat=round(request.origin_lat, 4) if has_start and request.origin_lat is not None else None,
        start_location_lng=round(request.origin_lng, 4) if has_start and request.origin_lng is not None else None,
        start_location_label=request.planning.start_location_label if request.planning is not None else None,
        similarity_signature=signature,
        profile_version=PLANNING_PROFILE_VERSION,
    )


def _ranked_stub_for_validation(
    *, experience: Experience, sequence_order: int, ranking_model_version: str
) -> RankedExperienceItem:
    """Builds the minimal RankedExperienceItem shape ItineraryValidatorService
    needs (it only reads .id/.title/.category via ComposedItem.experience,
    plus what the composer already computed) from a canonical Experience row
    that was NOT part of a Phase 7 ranked candidate set (manual add path).
    ranking_score/semantic_relevance are 0.0 — this is never fed back into
    the composer's aggregate-score objective, only used for schedule
    display and re-validation."""
    return RankedExperienceItem.model_validate(
        {
            "id": experience.id,
            "title": experience.title,
            "short_description": experience.short_description,
            "category": experience.category,
            "location": experience.location,
            "provider": experience.provider,
            "currency": experience.currency,
            "price": experience.price,
            "minimum_price": experience.minimum_price,
            "maximum_price": experience.maximum_price,
            "price_type": experience.price_type,
            "is_price_estimated": experience.is_price_estimated,
            "duration_minutes": experience.duration_minutes,
            "duration_is_estimated": experience.duration_is_estimated,
            "status": experience.status,
            "verification_status": experience.verification_status,
            "is_synthetic": experience.is_synthetic,
            "is_enriched": experience.is_enriched,
            "rank": sequence_order,
            "ranking_score": 0.0,
            "ranking_model_version": ranking_model_version,
            "semantic_relevance": 0.0,
            "personalized": False,
        },
        from_attributes=True,
    )


async def add_item_to_itinerary(
    *,
    session: AsyncSession,
    settings: Settings,
    routing_adapter: RoutingAdapter,
    itinerary: Itinerary,
    experience_id: str,
    planned_start: datetime | None,
    travel_mode: str,
) -> ComposeOutcome:
    """Adds one experience to an existing itinerary, re-running the
    validator over the full resulting item set before persisting — never
    appends without re-validation."""
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    exp_repo = ExperienceRepository(session)
    experience = await exp_repo.get_by_id(experience_id)
    if experience is None:
        return ComposeOutcome(valid=False, reason_code="ITINERARY_NOT_FOUND", message="Experience not found.")
    if experience.duration_minutes is None:
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="Experience has no known duration; cannot schedule it.",
        )

    tz = ZoneInfo(_DEFAULT_TZ)
    ranking_model_version = itinerary.ranking_model_version or "weighted-v1"
    existing_items = sorted(itinerary.items, key=lambda i: i.sequence_order)
    if planned_start is None:
        planned_start = (
            existing_items[-1].planned_end
            if existing_items
            else datetime.combine(itinerary.itinerary_date, itinerary.start_time, tzinfo=tz)
        )
    planned_end = planned_start + timedelta(minutes=experience.duration_minutes)

    experiences_by_id = {experience.id: experience}
    composed_existing: list[ComposedItem] = []
    for item in existing_items:
        loaded = await exp_repo.get_by_id(item.experience_id)
        if loaded is not None:
            experiences_by_id[item.experience_id] = loaded
            composed_existing.append(
                ComposedItem(
                    experience=_ranked_stub_for_validation(
                        experience=loaded, sequence_order=item.sequence_order,
                        ranking_model_version=ranking_model_version,
                    ),
                    sequence_order=item.sequence_order,
                    planned_start=item.planned_start,
                    planned_end=item.planned_end,
                    duration_minutes=item.duration_minutes,
                    travel_from_previous_minutes=item.travel_from_previous_minutes,
                    travel_from_previous_distance_km=item.travel_from_previous_distance_km,
                    travel_mode=item.travel_mode,
                    buffer_before_minutes=item.buffer_before_minutes,
                    buffer_after_minutes=item.buffer_after_minutes,
                    estimated_cost=item.estimated_cost,
                    source_rank_position=item.source_rank_position or 0,
                    source_ranking_score=item.source_ranking_score or 0.0,
                )
            )

    price = experience.price if experience.price is not None else experience.maximum_price
    new_sequence = len(existing_items) + 1
    new_composed = ComposedItem(
        experience=_ranked_stub_for_validation(
            experience=experience, sequence_order=new_sequence, ranking_model_version=ranking_model_version
        ),
        sequence_order=new_sequence,
        planned_start=planned_start,
        planned_end=planned_end,
        duration_minutes=experience.duration_minutes,
        travel_from_previous_minutes=None,
        travel_from_previous_distance_km=None,
        travel_mode=travel_mode,
        buffer_before_minutes=settings.composer_min_buffer_minutes,
        buffer_after_minutes=0,
        estimated_cost=price,
        source_rank_position=None,
        source_ranking_score=None,
    )

    validator = ItineraryValidatorService(routing_adapter)
    requested_start = datetime.combine(itinerary.itinerary_date, itinerary.start_time, tzinfo=tz)
    requested_end = datetime.combine(itinerary.itinerary_date, itinerary.end_time, tzinfo=tz)
    validation = await validator.validate(
        items=composed_existing + [new_composed],
        experiences_by_id=experiences_by_id,
        requested_start=requested_start,
        requested_end=requested_end,
        max_budget=None,
        max_experiences=None,
        # The group the itinerary was planned for still has to fit.
        party_size=itinerary.planning_profile.group_size if itinerary.planning_profile is not None else None,
        travel_mode=travel_mode,
    )
    if not validation.valid:
        return ComposeOutcome(valid=False, reason_code="COMPOSITION_TIME_CONFLICT", issues=validation.issues)

    new_item = ItineraryItem(
        itinerary_id=itinerary.id,
        experience_id=experience.id,
        sequence_order=new_sequence,
        planned_start=planned_start,
        planned_end=planned_end,
        duration_minutes=experience.duration_minutes,
        travel_from_previous_minutes=None,
        travel_from_previous_distance_km=None,
        travel_mode=travel_mode,
        buffer_before_minutes=settings.composer_min_buffer_minutes,
        buffer_after_minutes=0,
        estimated_cost=price,
        source_rank_position=None,
        source_ranking_score=None,
    )
    session.add(new_item)
    await session.flush()
    # Legs whose waypoint pair is unchanged and already routed are reused;
    # in practice only the new stop's arriving leg is routed.
    await ItineraryRouteService(routing_adapter).refresh_persisted_itinerary(
        itinerary=itinerary,
        ordered_items=[*existing_items, new_item],
        experiences_by_id=experiences_by_id,
        default_travel_mode=travel_mode,
    )
    await session.commit()
    await session.refresh(itinerary, attribute_names=["items", "participants", "planning_profile"])
    return ComposeOutcome(valid=True, itinerary=itinerary)


__all__ = ["ComposeOutcome", "add_item_to_itinerary", "compose_and_persist_itinerary"]
