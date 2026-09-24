from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.routing import RoutingAdapter
from src.core.config import Settings, get_settings
from src.core.db import get_session
from src.core.deps import require_traveler
from src.core.embedding import get_embedding_adapter
from src.core.location import get_routing_adapter
from src.models.user import User
from src.schemas.ranking import RecommendationRequest, RecommendationResponse
from src.services.discovery_pipeline import DiscoveryPipelineService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("", response_model=RecommendationResponse)
async def get_recommendations(
    payload: RecommendationRequest,
    user: Annotated[User, Depends(require_traveler)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    routing_adapter: Annotated[RoutingAdapter, Depends(get_routing_adapter)],
) -> RecommendationResponse:
    traveler_id = user.traveler.id
    embedding_adapter = get_embedding_adapter(settings)
    
    pipeline = DiscoveryPipelineService(session, settings, embedding_adapter, routing_adapter)
    
    result, ranked_items = await pipeline.run_with_ranking(
        traveler_id=traveler_id,
        raw_query=payload.query,
        interests=payload.interests,
        constraints=payload.constraints,
        limit=payload.top_k,
    )
    
    return RecommendationResponse(
        items=ranked_items,
        retrieval_mode=result.retrieval_mode,
        candidate_count=result.candidate_count,
        feasible_count=result.feasible_count,
        excluded_count=result.excluded_count,
        excluded_summary=result.excluded_summary,
        ranking_model_version=settings.ranking_model_version,
        personalized=any(item.personalized for item in ranked_items) if ranked_items else False
    )
