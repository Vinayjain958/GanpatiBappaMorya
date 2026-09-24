"""Gemini tools: `search_experiences` (Phase 5) and `check_feasibility`
(Phase 6) — see docs/AI_CONTEXT.md and docs/DECISIONS.md ADR-034/ADR-044.

Each `*_DECLARATION` dict is the single source of truth for that tool's
schema, shared by the adapter (Live token `live_connect_constraints`
locking) and the tool-execution route — declared once, never duplicated.

`execute_search_experiences` is the ONLY implementation of the search
tool: a thin wrapper around the Phase 4 ExperienceDiscoveryService — its
argument schema carries no hard constraints (budget/time/capacity/etc.),
so it is deliberately unchanged in Phase 6. Feasibility verification for
a specific candidate is a separate, explicit second tool call
(check_feasibility) — this keeps "find candidates" and "verify this one
candidate" as two clearly separated steps for the model to reason about,
matching the target pipeline (retrieval -> feasibility, not conflated).

`execute_check_feasibility` is the ONLY implementation of the feasibility
tool. It loads the REAL experience from the database by experience_id and
runs the same FeasibilityService used by POST /api/v1/feasibility/check —
Gemini supplies only an experience_id and constraint context; it can
never inject a fabricated price/hours/capacity value, because
CheckFeasibilityArgs has no such fields and FeasibilityService only ever
reads them from the loaded Experience row.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.routing import RoutingAdapter
from src.core.category_map import CATEGORY_SLUGS
from src.core.config import Settings
from src.core.errors import ApiError
from src.repositories.experience_repository import ExperienceRepository
from src.schemas.conversation import CheckFeasibilityArgs, SearchExperiencesArgs, SearchExperiencesResult
from src.schemas.experience import ExperienceSummary
from src.schemas.feasibility import FeasibilityVerdict, TravelerConstraints
from src.services.discovery_pipeline import DiscoveryPipelineService
from src.services.feasibility import FeasibilityService

SEARCH_EXPERIENCES_DECLARATION: dict[str, object] = {
    "name": "search_experiences",
    "description": (
        "Search LocaLens's real catalog of local experiences. Returns only "
        "actual catalog records — never invent an experience that this "
        "tool did not return. Call this once enough information is known "
        "(e.g. an interest or location) rather than repeatedly asking the "
        "user for details that are not required."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "q": {"type": "STRING", "description": "Free-text keyword search (interest, food type, activity)."},
            "category_slug": {"type": "STRING", "description": "A LocaLens category slug, if confidently known."},
            "city": {"type": "STRING"},
            "locality": {"type": "STRING", "description": "Neighborhood/area name, e.g. 'Fort', 'Bandra'."},
            "min_price": {"type": "NUMBER"},
            "max_price": {"type": "NUMBER"},
            "min_duration_minutes": {"type": "INTEGER"},
            "max_duration_minutes": {"type": "INTEGER"},
            "sort": {
                "type": "STRING",
                "enum": ["relevance", "distance", "price", "duration", "newest"],
            },
            "limit": {"type": "INTEGER", "description": "Max results, 1-10. Defaults to 5."},
        },
    },
}


async def execute_search_experiences(
    session: AsyncSession, 
    settings: Settings, 
    args: SearchExperiencesArgs,
    traveler_id: str | None = None,
    context: TravelerContext | None = None,
    routing_adapter: RoutingAdapter | None = None,
    embedding_adapter: Any | None = None,
) -> SearchExperiencesResult:
    category_slug = args.category_slug if args.category_slug in CATEGORY_SLUGS else None

    # Fallbacks in case adapters aren't injected here yet
    if not routing_adapter:
        from src.core.location import get_routing_adapter
        routing_adapter = get_routing_adapter(settings)
        
    if not embedding_adapter:
        from src.core.embedding import get_embedding_adapter
        embedding_adapter = get_embedding_adapter(settings)

    pipeline = DiscoveryPipelineService(session, settings, embedding_adapter, routing_adapter)
    
    constraints = TravelerConstraints(
        budget_max=args.max_price,
        budget_min=args.min_price,
    )
    if args.max_duration_minutes:
        constraints.available_duration_minutes = args.max_duration_minutes
        
    if traveler_id:
        result, ranked_items = await pipeline.run_with_ranking(
            traveler_id=traveler_id,
            raw_query=args.q,
            category_slug=category_slug,
            city=args.city,
            locality=args.locality,
            constraints=constraints,
            limit=args.limit,
            context=context,
        )
        summaries = [item for item in ranked_items]
        total = result.candidate_count
    else:
        result = await pipeline.run(
            raw_query=args.q,
            category_slug=category_slug,
            city=args.city,
            locality=args.locality,
            constraints=constraints,
            limit=args.limit,
        )
        # Use PipelineItem experiences
        summaries = [ExperienceSummary.model_validate(item.experience) for item in result.items]
        total = result.candidate_count

    return SearchExperiencesResult(items=summaries, total=total, truncated=total > len(summaries))


CHECK_FEASIBILITY_DECLARATION: dict[str, object] = {
    "name": "check_feasibility",
    "description": (
        "Deterministically verify whether a specific LocaLens catalog "
        "experience is feasible given traveler constraints (budget, "
        "available time, party size, travel time/distance, accessibility). "
        "This is NOT an LLM judgment — it queries real stored data and "
        "returns FEASIBLE, INFEASIBLE, or UNKNOWN with explicit reasons. "
        "Only call this with an experience_id previously returned by "
        "search_experiences. Never invent a price, opening hours, "
        "capacity, or availability value yourself — this tool is the only "
        "source of truth for feasibility. If the result is UNKNOWN, tell "
        "the traveler the information isn't available — never say it is "
        "'probably okay'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "experience_id": {"type": "STRING", "description": "An experience id from search_experiences results."},
            "budget_max": {"type": "NUMBER"},
            "available_duration_minutes": {"type": "INTEGER"},
            "party_size": {"type": "INTEGER"},
            "max_travel_time_minutes": {"type": "NUMBER"},
            "max_distance_km": {"type": "NUMBER"},
            "origin_lat": {"type": "NUMBER"},
            "origin_lng": {"type": "NUMBER"},
            "accessibility_requirements": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": ["wheelchair_accessible", "step_free"]},
            },
        },
        "required": ["experience_id"],
    },
}


async def execute_check_feasibility(
    session: AsyncSession,
    routing_adapter: RoutingAdapter,
    settings: Settings,
    args: CheckFeasibilityArgs,
) -> FeasibilityVerdict:
    experience = await ExperienceRepository(session).get_by_id(args.experience_id)
    if experience is None:
        raise ApiError(f"Experience '{args.experience_id}' not found", status_code=404)

    constraints = TravelerConstraints(
        budget_max=args.budget_max,
        available_duration_minutes=args.available_duration_minutes,
        party_size=args.party_size,
        max_travel_time_minutes=args.max_travel_time_minutes,
        max_distance_km=args.max_distance_km,
        origin_lat=args.origin_lat,
        origin_lng=args.origin_lng,
        accessibility_requirements=args.accessibility_requirements,
    )
    service = FeasibilityService(routing_adapter)
    return await service.evaluate(experience, constraints, travel_profile=settings.osrm_profile)


__all__ = [
    "CHECK_FEASIBILITY_DECLARATION",
    "SEARCH_EXPERIENCES_DECLARATION",
    "execute_check_feasibility",
    "execute_search_experiences",
]
