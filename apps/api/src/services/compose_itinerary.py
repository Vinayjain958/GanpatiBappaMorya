"""Orchestrates the full Phase 8 pipeline for one compose request:

RETRIEVAL -> FEASIBILITY -> RANKING -> COMPOSITION -> POST-COMPOSITION
VALIDATION -> NARRATIVE -> persist.

This module — not the route handler — owns the ordering invariant so it
can be reused identically by both POST /itineraries/compose and the
compose_experience Gemini tool (src/services/ai_tools.py), which must
never re-run the Phase 6/7 pipeline redundantly when a valid ranked
candidate context is already available (see execute_compose_experience).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_type, datetime, time as time_type

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.ai import AIAdapter
from src.adapters.embedding import EmbeddingAdapter
from src.adapters.routing import RoutingAdapter
from src.core.config import Settings
from src.core.feasibility_reasons import FeasibilityReasonCode
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.repositories.experience_repository import ExperienceRepository
from src.repositories.itinerary_repository import ItineraryRepository
from src.schemas.itinerary import ComposeItineraryRequest
from src.schemas.ranking import RankedExperienceItem
from src.services.discovery_pipeline import DiscoveryPipelineService
from src.services.experience_composer import ComposedItem, ExperienceComposerService
from src.services.itinerary_narrator import ItineraryNarratorService
from src.services.itinerary_validator import ItineraryValidatorService, ValidationIssue

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
    constraints = TravelerConstraints(
        budget_max=request.max_budget,
        party_size=request.party_size,
        available_date=request.itinerary_date,
        available_start=request.start_time,
        available_end=request.end_time,
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
    composition = await composer.compose(
        candidates=ranked_candidates,
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
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="No combination of feasible experiences fit the requested time window and constraints.",
            candidate_count=candidate_count,
            feasible_count=feasible_count,
        )

    exp_repo = ExperienceRepository(session)
    experiences_by_id = {}
    for item in composition.items:
        exp = await exp_repo.get_by_id(item.experience.id)
        if exp is not None:
            experiences_by_id[item.experience.id] = exp

    validator = ItineraryValidatorService(routing_adapter)
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(_DEFAULT_TZ)
    requested_start = datetime.combine(request.itinerary_date, request.start_time, tzinfo=tz)
    requested_end = datetime.combine(request.itinerary_date, request.end_time, tzinfo=tz)

    validation = await validator.validate(
        items=composition.items,
        experiences_by_id=experiences_by_id,
        requested_start=requested_start,
        requested_end=requested_end,
        max_budget=request.max_budget,
        max_experiences=request.max_experiences,
        party_size=request.party_size,
        travel_mode=request.travel_mode,
    )

    if not validation.valid:
        return ComposeOutcome(
            valid=False,
            reason_code="COMPOSITION_NO_VALID_PLAN",
            message="The composed itinerary failed validation.",
            issues=validation.issues,
            candidate_count=candidate_count,
            feasible_count=feasible_count,
        )

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
    )
    ItineraryRepository(session).add(itinerary)
    await session.flush()

    narrative_by_id = {n.experience_id: n.text for n in outcome_narration.narrative.item_narratives}
    for composed in composition.items:
        item = ItineraryItem(
            itinerary_id=itinerary.id,
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
            narrative_text=narrative_by_id.get(composed.experience.id),
        )
        session.add(item)

    await session.commit()
    await session.refresh(itinerary, attribute_names=["items"])

    return ComposeOutcome(
        valid=True,
        itinerary=itinerary,
        candidate_count=candidate_count,
        feasible_count=feasible_count,
    )


def _ranked_stub_for_validation(
    *, experience, sequence_order: int, ranking_model_version: str
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
        party_size=None,
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
    await session.commit()
    await session.refresh(itinerary, attribute_names=["items"])
    return ComposeOutcome(valid=True, itinerary=itinerary)


__all__ = ["ComposeOutcome", "add_item_to_itinerary", "compose_and_persist_itinerary"]
