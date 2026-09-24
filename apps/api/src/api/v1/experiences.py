from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.embedding import EmbeddingAdapter
from src.adapters.errors import AdapterError
from src.adapters.routing import OSRMRoutingAdapter, RoutingAdapter
from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.core.deps import CurrentProvider, CurrentUser
from src.core.embedding import get_embedding_adapter
from src.core.errors import ApiError
from src.core.location import get_routing_adapter
from src.models.experience import Experience
from src.models.provider import Provider
from src.repositories.experience_repository import ExperienceRepository
from src.schemas.experience import ExperienceDetail, ExperienceListResponse, ExperienceSummary
from src.schemas.experience_write import ExperienceCreateRequest, ExperienceUpdateRequest
from src.schemas.semantic_search import (
    ExcludedReasonSummary,
    SemanticSearchItem,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from src.services import experience as experience_service
from src.services.discovery import DiscoveryQuery, ExperienceDiscoveryService
from src.services.discovery_pipeline import DiscoveryPipelineService

router = APIRouter(prefix="/experiences", tags=["experiences"])

SortParam = Literal["relevance", "distance", "price", "duration", "newest"]


@router.get("", response_model=ExperienceListResponse)
async def list_experiences(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    routing: Annotated[RoutingAdapter, Depends(get_routing_adapter)],
    q: Annotated[str | None, Query(max_length=200, description="Keyword search")] = None,
    category: Annotated[str | None, Query(description="Category slug filter")] = None,
    city: Annotated[str | None, Query()] = None,
    locality: Annotated[str | None, Query()] = None,
    provider: Annotated[str | None, Query(description="Provider id filter")] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    min_duration_minutes: Annotated[int | None, Query(ge=0)] = None,
    max_duration_minutes: Annotated[int | None, Query(ge=0)] = None,
    source_type: Annotated[str | None, Query()] = None,
    is_synthetic: Annotated[bool | None, Query()] = None,
    status: Annotated[str, Query(description="Experience status filter")] = "active",
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    radius_km: Annotated[float | None, Query(gt=0)] = None,
    sort: Annotated[SortParam, Query()] = "relevance",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ExperienceListResponse:
    repository = ExperienceRepository(session)
    service = ExperienceDiscoveryService(repository, settings)

    try:
        result = await service.search(
            DiscoveryQuery(
                q=q, category_slug=category, city=city, locality=locality, provider_id=provider,
                min_price=min_price, max_price=max_price,
                min_duration_minutes=min_duration_minutes, max_duration_minutes=max_duration_minutes,
                source_type=source_type, is_synthetic=is_synthetic, status=status,
                lat=lat, lng=lng, radius_km=radius_km, sort=sort, limit=limit, offset=offset,
            )
        )
    except ValueError as exc:
        raise ApiError(str(exc), status_code=422) from exc

    summaries = [ExperienceSummary.model_validate(item.experience) for item in result.items]
    for summary, item in zip(summaries, result.items, strict=True):
        summary.distance_km = item.distance_km

    # Travel-time enrichment is applied only to the returned page (never
    # the whole catalog) and only when a travel origin was given — see
    # docs/DECISIONS.md ADR-023. OSRM failures degrade to "unavailable"
    # per item rather than breaking the whole discovery response.
    if lat is not None and lng is not None and summaries:
        destinations = [
            (s.id, item.experience.location.latitude, item.experience.location.longitude)
            for s, item in zip(summaries, result.items, strict=True)
        ][: settings.osrm_max_matrix_destinations]
        try:
            entries = await routing.get_travel_time_matrix(
                (lat, lng), destinations, profile=settings.osrm_profile
            )
            source = "osrm" if isinstance(routing, OSRMRoutingAdapter) else "haversine_estimate"
            by_id = {e.id: e for e in entries}
            for summary in summaries:
                entry = by_id.get(summary.id)
                if entry is not None and entry.duration_minutes is not None:
                    summary.travel_time_minutes = entry.duration_minutes
                    summary.travel_time_source = source
        except AdapterError:
            pass  # travel time is an enhancement; discovery must still succeed

    return ExperienceListResponse(items=summaries, total=result.total, limit=limit, offset=offset)


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    payload: SemanticSearchRequest,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    embedding_adapter: Annotated[EmbeddingAdapter, Depends(get_embedding_adapter)],
    routing: Annotated[RoutingAdapter, Depends(get_routing_adapter)],
) -> SemanticSearchResponse:
    """Semantic retrieval -> deterministic feasibility gate (Phase 6).
    Only FEASIBLE candidates are ever returned in `items` — see
    DiscoveryPipelineService. retrieval_mode is always honestly reported
    (never claims pgvector/semantic retrieval happened when it fell back
    to keyword search)."""
    pipeline = DiscoveryPipelineService(session, settings, embedding_adapter, routing)
    try:
        result = await pipeline.run(
            raw_query=payload.query,
            interests=payload.interests or None,
            category_slug=payload.category_slug,
            city=payload.city,
            locality=payload.locality,
            location_text=payload.location_text,
            constraints=payload.constraints,
            limit=payload.limit,
            travel_profile=settings.osrm_profile,
        )
    except ValueError as exc:
        raise ApiError(str(exc), status_code=422) from exc

    experience_repo = ExperienceRepository(session)
    items: list[SemanticSearchItem] = []
    for pipeline_item in result.items:
        experience = await experience_repo.get_by_id(pipeline_item.experience_id)
        if experience is None:
            continue
        items.append(
            SemanticSearchItem(
                experience=ExperienceSummary.model_validate(experience),
                semantic_similarity=pipeline_item.similarity,
            )
        )

    return SemanticSearchResponse(
        items=items,
        retrieval_mode=result.retrieval_mode,
        candidate_count=result.candidate_count,
        feasible_count=result.feasible_count,
        excluded_count=result.excluded_count,
        excluded_summary=ExcludedReasonSummary(
            reason_counts=result.excluded_summary.reason_counts,
            sample=result.excluded_summary.sample,
        ),
    )


@router.post("", response_model=ExperienceDetail, status_code=201)
async def create_experience(
    payload: ExperienceCreateRequest,
    provider: CurrentProvider,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExperienceDetail:
    experience = await experience_service.create_experience(session, provider, payload)
    return ExperienceDetail.model_validate(experience)


@router.get("/{experience_id}", response_model=ExperienceDetail)
async def get_experience(
    experience_id: str, session: Annotated[AsyncSession, Depends(get_session)]
) -> ExperienceDetail:
    repository = ExperienceRepository(session)
    experience = await repository.get_by_id(experience_id)
    if experience is None:
        raise ApiError("Experience not found", status_code=404)
    return ExperienceDetail.model_validate(experience)


async def _get_owned_or_404(session: AsyncSession, experience_id: str, provider: Provider) -> Experience:
    repository = ExperienceRepository(session)
    experience = await repository.get_owned_by_id(experience_id, provider.id)
    if experience is None:
        # Deliberately identical to "does not exist" — do not disclose
        # that the experience exists but belongs to another provider.
        raise ApiError("Experience not found", status_code=404)
    return experience


@router.patch("/{experience_id}", response_model=ExperienceDetail)
async def update_experience(
    experience_id: str,
    payload: ExperienceUpdateRequest,
    provider: CurrentProvider,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExperienceDetail:
    experience = await _get_owned_or_404(session, experience_id, provider)
    updated = await experience_service.update_experience(session, experience, payload)
    return ExperienceDetail.model_validate(updated)


@router.delete("/{experience_id}", response_model=ExperienceDetail)
async def deactivate_experience(
    experience_id: str,
    provider: CurrentProvider,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExperienceDetail:
    experience = await _get_owned_or_404(session, experience_id, provider)
    deactivated = await experience_service.deactivate_experience(session, experience)
    return ExperienceDetail.model_validate(deactivated)
