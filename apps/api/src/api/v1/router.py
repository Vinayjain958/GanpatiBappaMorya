from __future__ import annotations

from fastapi import APIRouter

from src.api.v1 import (
    auth,
    availability,
    categories,
    conversation,
    experiences,
    feasibility,
    health,
    location,
    providers,
    recommendations,
    feedback,
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(categories.router)
api_v1_router.include_router(providers.router)
api_v1_router.include_router(experiences.router)
api_v1_router.include_router(availability.router)
api_v1_router.include_router(location.router)
api_v1_router.include_router(conversation.router)
api_v1_router.include_router(feasibility.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(feedback.router)
