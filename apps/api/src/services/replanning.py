"""ReplanningService — dynamic itinerary replanning engine (Phase 9).

Implements the exact 13-step algorithm from the Phase 9 spec:
  1. Load current itinerary, verify ownership, lock revision (via
     Itinerary.version optimistic-locking check).
  2. Determine current time; separate items into completed/in_progress/
     past/future_locked/future_flexible.
  3. Preserve completed and explicitly-locked-future items.
  4. Evaluate context against remaining items (ContextImpactService).
  5. If no material impact -> NO_CHANGE.
  6. Remove/reject only invalid future_flexible items.
  7. Derive remaining time window/budget/constraints.
  8. Run ONE Phase 6 retrieval/feasibility pass (DiscoveryPipelineService).
  9. Run Phase 7 ranking (PersonalizedRankingService, via
     DiscoveryPipelineService.run_with_ranking — never a second ranking
     engine).
  10. Run Phase 8 composition (ExperienceComposerService) for the
      remaining segment.
  11. Merge preserved + newly composed items.
  12. Run full itinerary validation (ItineraryValidatorService); on
      invalid, REPLAN_FAILED, preserving the previous valid revision.
  13. On valid -> new revision/version, Gemini narrative (facts-only,
      template fallback), persist, return.

Never creates a second ranking engine, discovery pipeline, or Gemini
client — reuses the exact Phase 6/7/8 services via
compose_itinerary.py's helpers and DiscoveryPipelineService directly.
traveler_id is always server-derived by the caller (the API route),
never accepted from Gemini or the request body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.ai import AIAdapter
from src.adapters.embedding import EmbeddingAdapter
from src.adapters.routing import RoutingAdapter
from src.core.config import Settings
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.models.itinerary_revision import ItineraryRevision
from src.repositories.experience_repository import ExperienceRepository
from src.repositories.itinerary_repository import ItineraryRepository
from src.schemas.feasibility import TravelerConstraints
from src.schemas.ranking import RankedExperienceItem
from src.services.context_impact import ContextImpactResult, ImpactSeverity
from src.services.discovery_pipeline import DiscoveryPipelineService
from src.services.experience_composer import ComposedItem, ExperienceComposerService
from src.services.itinerary_narrator import ItineraryNarratorService
from src.services.itinerary_validator import ItineraryValidatorService
from src.services.sse import publish_itinerary_event

_DEFAULT_TZ = "Asia/Kolkata"


class ReplanStatus:
    NO_CHANGE = "NO_CHANGE"
    REPLANNED = "REPLANNED"
    REPLAN_FAILED = "REPLAN_FAILED"
    REQUIRES_USER_ACTION = "REQUIRES_USER_ACTION"
    CONFLICT = "CONFLICT"


@dataclass
class ReplanChangeSet:
    added_items: list[str] = field(default_factory=list)
    removed_items: list[str] = field(default_factory=list)
    moved_items: list[str] = field(default_factory=list)
    unchanged_items: list[str] = field(default_factory=list)
    affected_items: list[str] = field(default_factory=list)


@dataclass
class ReplanOutcome:
    status: str
    itinerary: Itinerary | None = None
    previous_version: int | None = None
    new_version: int | None = None
    trigger: str | None = None
    changes: ReplanChangeSet = field(default_factory=ReplanChangeSet)
    context_summary: str = ""
    validation_issues: list[str] = field(default_factory=list)
    reason_code: str | None = None
    message: str | None = None
    generated_at: datetime | None = None


class ReplanningService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        routing_adapter: RoutingAdapter,
        embedding_adapter: EmbeddingAdapter | None,
        ai_adapter: AIAdapter,
    ) -> None:
        self._session = session
        self._settings = settings
        self._routing = routing_adapter
        self._embedding = embedding_adapter
        self._ai = ai_adapter

    async def replan_itinerary(
        self,
        *,
        itinerary_id: str,
        traveler_id: str,
        trigger: str,
        impact: ContextImpactResult | None = None,
        expected_version: int | None = None,
        idempotency_key: str | None = None,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> ReplanOutcome:
        # Step 1: load + verify ownership + lock revision (optimistic).
        repo = ItineraryRepository(self._session)
        itinerary = await repo.get_owned_by_id(itinerary_id, traveler_id)
        if itinerary is None:
            return ReplanOutcome(status=ReplanStatus.CONFLICT, reason_code="ITINERARY_NOT_FOUND")

        if idempotency_key:
            existing = await self._find_by_idempotency_key(itinerary_id, idempotency_key)
            if existing is not None:
                return await self._outcome_from_existing_revision(itinerary, existing)

        if expected_version is not None and expected_version != itinerary.version:
            return ReplanOutcome(
                status=ReplanStatus.CONFLICT,
                reason_code="ITINERARY_VERSION_CONFLICT",
                message=f"Expected version {expected_version}, current version is {itinerary.version}.",
                previous_version=itinerary.version,
            )

        tz = ZoneInfo(_DEFAULT_TZ)
        now = now or datetime.now(tz)

        # Step 2/3: partition items.
        items = sorted(itinerary.items, key=lambda i: i.sequence_order)
        exp_repo = ExperienceRepository(self._session)
        experiences_by_id = {}
        for item in items:
            exp = await exp_repo.get_by_id(item.experience_id)
            if exp is not None:
                experiences_by_id[item.experience_id] = exp

        preserved: list[ItineraryItem] = []
        flexible: list[ItineraryItem] = []
        for item in items:
            if item.planned_end <= now:
                preserved.append(item)  # completed/past — immutable
            elif item.planned_start <= now < item.planned_end:
                preserved.append(item)  # in progress — immutable
            elif item.is_locked:
                preserved.append(item)  # future, locked
            else:
                flexible.append(item)

        # Step 4/5: impact assessment.
        if impact is None or not impact.affected:
            return ReplanOutcome(
                status=ReplanStatus.NO_CHANGE,
                itinerary=itinerary,
                previous_version=itinerary.version,
                new_version=itinerary.version,
                trigger=trigger,
                context_summary=(impact.explanation if impact else "No context change supplied."),
                generated_at=now,
            )

        # A locked item flagged as affected requires manual traveler
        # action — never silently replaced.
        locked_affected = [
            item for item in preserved
            if item.is_locked and item.id in impact.affected_itinerary_item_ids and item.planned_start > now
        ]
        if locked_affected:
            for item in locked_affected:
                item.item_state = "AFFECTED"
            itinerary.replanning_status = "REQUIRES_USER_ACTION"
            await self._session.commit()
            await publish_itinerary_event(
                itinerary_id, "requires_action",
                {"affected_items": [i.id for i in locked_affected], "reason": impact.explanation},
            )
            return ReplanOutcome(
                status=ReplanStatus.REQUIRES_USER_ACTION,
                itinerary=itinerary,
                previous_version=itinerary.version,
                new_version=itinerary.version,
                trigger=trigger,
                changes=ReplanChangeSet(affected_items=[i.id for i in locked_affected]),
                context_summary=impact.explanation,
                generated_at=now,
            )

        # Step 6: remove/reject only invalid future_flexible items.
        affected_flexible_ids = {
            item.id for item in flexible if item.id in impact.affected_itinerary_item_ids
        }
        kept_flexible = [item for item in flexible if item.id not in affected_flexible_ids]
        removed_ids = list(affected_flexible_ids)

        if not removed_ids:
            # Impact affected only preserved/locked items already handled
            # above, or nothing schedulable — nothing further to replan.
            return ReplanOutcome(
                status=ReplanStatus.NO_CHANGE,
                itinerary=itinerary,
                previous_version=itinerary.version,
                new_version=itinerary.version,
                trigger=trigger,
                context_summary=impact.explanation,
                generated_at=now,
            )

        # Step 7: derive remaining window/budget/constraints.
        window_end = tz_combine(itinerary.itinerary_date, itinerary.end_time, tz)
        remaining_start = max(now, tz_combine(itinerary.itinerary_date, itinerary.start_time, tz))
        if kept_flexible or preserved:
            last_end = max([i.planned_end for i in preserved + kept_flexible] or [remaining_start])
            remaining_start = max(remaining_start, last_end)
        remaining_budget = None
        if itinerary.estimated_total_cost is not None:
            spent = sum((i.estimated_cost or 0.0) for i in preserved + kept_flexible)
            remaining_budget = max(0.0, itinerary.estimated_total_cost - spent)

        exclude_ids = {i.experience_id for i in preserved + kept_flexible}

        itinerary.replanning_status = "REPLANNING"
        await self._session.commit()
        await publish_itinerary_event(
            itinerary_id, "replan_started", {"trigger": trigger, "reason": impact.explanation}
        )

        # Step 8+9: ONE Phase 6+7 pass for replacement candidates.
        pipeline = DiscoveryPipelineService(self._session, self._settings, self._embedding, self._routing)
        constraints = TravelerConstraints(
            budget_max=remaining_budget,
            available_date=itinerary.itinerary_date,
            available_start=remaining_start.time(),
            available_end=itinerary.end_time,
        )
        _, ranked_items = await pipeline.run_with_ranking(
            traveler_id=traveler_id,
            raw_query=None,
            constraints=constraints,
            limit=self._settings.composer_max_candidates,
        )
        ranked_items = [c for c in ranked_items if c.id not in exclude_ids]

        # Step 10: composition for the remaining segment.
        origin_item = (preserved + kept_flexible)
        origin_item.sort(key=lambda i: i.planned_end)
        origin_lat = origin_lng = None
        if origin_item:
            last_exp = experiences_by_id.get(origin_item[-1].experience_id)
            if last_exp is not None:
                origin_lat, origin_lng = last_exp.location.latitude, last_exp.location.longitude

        composer = ExperienceComposerService(self._settings, self._routing)
        remaining_count = max(0, (itinerary.total_duration_minutes and len(items) or len(items)) - len(preserved) - len(kept_flexible))
        max_new = max(1, len(removed_ids))
        composition = await composer.compose(
            candidates=ranked_items,
            itinerary_date=itinerary.itinerary_date,
            start_time_of_day=remaining_start.time(),
            end_time_of_day=itinerary.end_time,
            max_experiences=max_new,
            max_budget=remaining_budget,
            travel_mode=self._settings.composer_default_travel_mode,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
        )

        if not composition.items:
            itinerary.replanning_status = "STABLE"
            await self._session.commit()
            await publish_itinerary_event(
                itinerary_id, "replan_failed",
                {"reason_code": "NO_FEASIBLE_REPLACEMENT", "trigger": trigger},
            )
            return ReplanOutcome(
                status=ReplanStatus.REPLAN_FAILED,
                itinerary=itinerary,
                previous_version=itinerary.version,
                new_version=itinerary.version,
                trigger=trigger,
                reason_code="NO_FEASIBLE_REPLACEMENT",
                message="No feasible replacement experiences were found for the affected slot(s).",
                context_summary=impact.explanation,
                generated_at=now,
            )

        # Step 11: merge preserved + kept_flexible + newly composed.
        merged_composed: list[ComposedItem] = []
        seq = 1
        for item in preserved + kept_flexible:
            exp = experiences_by_id.get(item.experience_id)
            if exp is None:
                continue
            merged_composed.append(_item_to_composed(item, exp, seq))
            seq += 1
        base_offset = seq - 1
        for c in composition.items:
            c.sequence_order = base_offset + c.sequence_order
            merged_composed.append(c)

        # Step 12: full validation.
        validator = ItineraryValidatorService(self._routing)
        all_exp_by_id = {**experiences_by_id}
        for c in composition.items:
            exp = await exp_repo.get_by_id(c.experience.id)
            if exp is not None:
                all_exp_by_id[c.experience.id] = exp

        requested_start = tz_combine(itinerary.itinerary_date, itinerary.start_time, tz)
        validation = await validator.validate(
            items=merged_composed,
            experiences_by_id=all_exp_by_id,
            requested_start=requested_start,
            requested_end=window_end,
            max_budget=itinerary.estimated_total_cost,
            max_experiences=None,
            party_size=None,
            travel_mode=self._settings.composer_default_travel_mode,
        )

        if not validation.valid:
            # Preserve the previous valid revision — never replace a
            # valid itinerary with a broken one.
            itinerary.replanning_status = "STABLE"
            await self._session.commit()
            await publish_itinerary_event(
                itinerary_id, "replan_failed",
                {"reason_code": "REPLAN_VALIDATION_FAILED", "trigger": trigger},
            )
            return ReplanOutcome(
                status=ReplanStatus.REPLAN_FAILED,
                itinerary=itinerary,
                previous_version=itinerary.version,
                new_version=itinerary.version,
                trigger=trigger,
                reason_code="REPLAN_VALIDATION_FAILED",
                message="The replanned itinerary failed post-composition validation.",
                validation_issues=[i.message for i in validation.issues],
                context_summary=impact.explanation,
                generated_at=now,
            )

        # Step 13: persist new revision, narrative, emit event.
        added_ids = [c.experience.id for c in composition.items]
        unchanged_ids = [i.experience_id for i in preserved + kept_flexible]

        narrator = ItineraryNarratorService(self._ai, self._settings)
        narration = await narrator.narrate(
            items=merged_composed,
            itinerary_date_str=itinerary.itinerary_date.isoformat(),
            currency=itinerary.currency,
            total_cost=sum(c.estimated_cost or 0.0 for c in merged_composed),
        )

        # Replace itinerary_items: delete removed flexible items, keep
        # preserved/kept, add newly composed ones.
        for item in items:
            if item.id in removed_ids:
                await self._session.delete(item)
        for i, item in enumerate(preserved + kept_flexible, start=1):
            item.sequence_order = i
        new_db_items: list[ItineraryItem] = []
        for c in composition.items:
            new_item = ItineraryItem(
                itinerary_id=itinerary.id,
                experience_id=c.experience.id,
                sequence_order=c.sequence_order,
                planned_start=c.planned_start,
                planned_end=c.planned_end,
                duration_minutes=c.duration_minutes,
                travel_from_previous_minutes=c.travel_from_previous_minutes,
                travel_from_previous_distance_km=c.travel_from_previous_distance_km,
                travel_mode=c.travel_mode,
                buffer_before_minutes=c.buffer_before_minutes,
                buffer_after_minutes=c.buffer_after_minutes,
                estimated_cost=c.estimated_cost,
                source_rank_position=c.source_rank_position,
                source_ranking_score=c.source_ranking_score,
                item_state="ACTIVE",
            )
            self._session.add(new_item)
            new_db_items.append(new_item)

        previous_version = itinerary.version
        itinerary.version = previous_version + 1
        itinerary.replanning_status = "STABLE"
        itinerary.context_last_updated_at = now
        itinerary.narrative_title = narration.narrative.title
        itinerary.narrative_summary = narration.narrative.summary
        itinerary.narrative_closing_message = narration.narrative.closing_message
        itinerary.narrative_model_version = narration.model_version
        itinerary.estimated_total_cost = sum(c.estimated_cost or 0.0 for c in merged_composed)
        itinerary.total_duration_minutes = sum(c.duration_minutes for c in merged_composed)
        itinerary.total_travel_minutes = sum(c.travel_from_previous_minutes or 0.0 for c in merged_composed)
        itinerary.generated_at = now

        revision = ItineraryRevision(
            itinerary_id=itinerary.id,
            version=itinerary.version,
            previous_revision_id=itinerary.current_revision_id,
            trigger=trigger,
            status=ReplanStatus.REPLANNED,
            changes={
                "added_items": added_ids,
                "removed_items": removed_ids,
                "moved_items": [],
                "unchanged_items": unchanged_ids,
                "affected_items": impact.affected_itinerary_item_ids,
            },
            reason=reason,
            idempotency_key=idempotency_key,
            generated_at=now,
        )
        self._session.add(revision)
        await self._session.flush()
        itinerary.current_revision_id = revision.id

        await self._session.commit()
        await self._session.refresh(itinerary, attribute_names=["items"])

        await publish_itinerary_event(
            itinerary_id, "replan_completed",
            {
                "trigger": trigger,
                "new_version": itinerary.version,
                "added_items": added_ids,
                "removed_items": removed_ids,
            },
        )

        return ReplanOutcome(
            status=ReplanStatus.REPLANNED,
            itinerary=itinerary,
            previous_version=previous_version,
            new_version=itinerary.version,
            trigger=trigger,
            changes=ReplanChangeSet(
                added_items=added_ids,
                removed_items=removed_ids,
                unchanged_items=unchanged_ids,
                affected_items=impact.affected_itinerary_item_ids,
            ),
            context_summary=impact.explanation,
            generated_at=now,
        )

    async def _find_by_idempotency_key(self, itinerary_id: str, key: str) -> ItineraryRevision | None:
        from sqlalchemy import select

        result = await self._session.execute(
            select(ItineraryRevision).where(
                ItineraryRevision.itinerary_id == itinerary_id,
                ItineraryRevision.idempotency_key == key,
            )
        )
        return result.scalars().one_or_none()

    async def _outcome_from_existing_revision(
        self, itinerary: Itinerary, revision: ItineraryRevision
    ) -> ReplanOutcome:
        changes = revision.changes or {}
        return ReplanOutcome(
            status=revision.status,
            itinerary=itinerary,
            previous_version=revision.version - 1 if revision.version > 1 else revision.version,
            new_version=revision.version,
            trigger=revision.trigger,
            changes=ReplanChangeSet(
                added_items=changes.get("added_items", []),
                removed_items=changes.get("removed_items", []),
                moved_items=changes.get("moved_items", []),
                unchanged_items=changes.get("unchanged_items", []),
                affected_items=changes.get("affected_items", []),
            ),
            context_summary="Idempotent replay of a previous replan request.",
            generated_at=revision.generated_at,
        )


def tz_combine(date_, time_, tz) -> datetime:
    return datetime.combine(date_, time_, tzinfo=tz)


def _item_to_composed(item: ItineraryItem, experience, sequence_order: int) -> ComposedItem:
    ranked_stub = RankedExperienceItem.model_validate(
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
            "ranking_score": item.source_ranking_score or 0.0,
            "ranking_model_version": "weighted-v1",
            "semantic_relevance": 0.0,
            "personalized": False,
        },
        from_attributes=True,
    )
    return ComposedItem(
        experience=ranked_stub,
        sequence_order=sequence_order,
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


__all__ = ["ReplanChangeSet", "ReplanOutcome", "ReplanStatus", "ReplanningService"]
