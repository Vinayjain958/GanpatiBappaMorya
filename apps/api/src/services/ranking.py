from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.models.affinity import TravelerAffinity
from src.models.preference import TravelerPreference
from src.repositories.affinity_repository import AffinityRepository
from src.repositories.interaction_repository import InteractionRepository
from src.repositories.preference_repository import PreferenceRepository
from src.schemas.conversation import TravelerContext
from src.schemas.ranking import RankedExperienceItem
from src.services.discovery_pipeline import PipelineItem

logger = logging.getLogger(__name__)


@dataclass
class TravelerRankingProfile:
    traveler_id: str
    preference: TravelerPreference | None
    affinities: dict[tuple[str, str], TravelerAffinity]
    recently_seen_experience_ids: set[str]


class RankerProtocol(Protocol):
    def rank(
        self,
        candidates: list[PipelineItem],
        traveler_profile: TravelerRankingProfile,
        context: TravelerContext,
        settings: Settings,
    ) -> list[RankedExperienceItem]: ...


class WeightedPersonalizedRanker:
    def rank(
        self,
        candidates: list[PipelineItem],
        traveler_profile: TravelerRankingProfile,
        context: TravelerContext,
        settings: Settings,
    ) -> list[RankedExperienceItem]:
        
        ranked_items = []
        for candidate in candidates:
            # Base Semantic Relevance
            semantic_relevance = candidate.similarity if candidate.similarity is not None else 0.5
            
            # Affinity Score
            affinity = traveler_profile.affinities.get(("category", candidate.experience.category.slug))
            affinity_score = affinity.score if affinity else 0.0
            
            # Preference Match
            preference_match = 0.0
            if traveler_profile.preference and traveler_profile.preference.preferred_category_slugs:
                if candidate.experience.category.slug in traveler_profile.preference.preferred_category_slugs:
                    preference_match = 1.0
                    
            # Budget Fit
            budget_fit = 1.0
            # Assuming context has budget in some form. 
            # In Phase 6, constraints are in constraints.budget_max
            # For simplicity we do a binary or soft budget fit based on heuristics
            if getattr(context, "constraints", None) and getattr(context.constraints, "budget_max", None):
                b_max = context.constraints.budget_max
                if getattr(candidate.experience, "price_type", None) == "fixed":
                    price_min = getattr(candidate.experience, "price_min", 0)
                    if price_min > b_max:
                        budget_fit = 0.0
            
            # Duration Fit
            duration_fit = 1.0
            
            # Distance Fit
            distance_fit = 1.0
            
            # Novelty
            novelty = 0.0 if candidate.experience_id in traveler_profile.recently_seen_experience_ids else 1.0
            
            # Calculate final score
            ranking_score = (
                settings.ranking_weight_semantic * semantic_relevance +
                settings.ranking_weight_affinity * affinity_score +
                settings.ranking_weight_preference * preference_match +
                settings.ranking_weight_budget * budget_fit +
                settings.ranking_weight_duration * duration_fit +
                settings.ranking_weight_distance * distance_fit +
                settings.ranking_weight_novelty * novelty
            )
            
            # Identify match signals
            match_signals = []
            if preference_match > 0:
                match_signals.append("Matches your preferences")
            if affinity_score > 0.5:
                match_signals.append("High affinity category")
            if novelty == 1.0 and affinity_score > 0.0:
                match_signals.append("New for you")
                
            is_personalized = bool(traveler_profile.preference or traveler_profile.affinities)
                
            # Create dict matching schema ExperienceSummary
            # and append extra fields
            exp_dict = {
                "id": candidate.experience.id,
                "title": candidate.experience.title,
                "category": candidate.experience.category,
                "location": candidate.experience.location,
                "provider": candidate.experience.provider,
                "slug": candidate.experience.slug,
                "status": getattr(candidate.experience, "status", "active"),
                "verification_status": getattr(candidate.experience, "verification_status", "verified"),
                "price_type": getattr(candidate.experience, "price_type", "unknown"),
                "price_currency": getattr(candidate.experience, "price_currency", None),
                "price_min": getattr(candidate.experience, "price_min", None),
                "price_max": getattr(candidate.experience, "price_max", None),
                "duration_estimated_minutes": getattr(candidate.experience, "duration_estimated_minutes", None),
                "images": getattr(candidate.experience, "images", []),
                "is_synthetic": getattr(candidate.experience, "is_synthetic", True),
                "is_enriched": getattr(candidate.experience, "is_enriched", False),
            }
                
            ranked_item = RankedExperienceItem(
                **exp_dict,
                rank=0, # Set later after sort
                ranking_score=ranking_score,
                ranking_model_version=settings.ranking_model_version,
                semantic_relevance=semantic_relevance,
                personalized=is_personalized,
                match_signals=match_signals
            )
            ranked_items.append(ranked_item)
            
        ranked_items.sort(key=lambda x: x.id) # 3. id asc
        ranked_items.sort(key=lambda x: x.semantic_relevance, reverse=True) # 2. semantic desc
        ranked_items.sort(key=lambda x: x.ranking_score, reverse=True) # 1. score desc
        
        for i, item in enumerate(ranked_items):
            item.rank = i + 1
            
        return ranked_items


class PersonalizedRankingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ranker = WeightedPersonalizedRanker()

    async def rank(
        self,
        traveler_id: str,
        pipeline_items: list[PipelineItem],
        context: TravelerContext | None,
        session: AsyncSession,
    ) -> list[RankedExperienceItem]:
        if not traveler_id:
            raise ValueError("traveler_id is required")
            
        if not context:
            context = TravelerContext()
            
        pref_repo = PreferenceRepository(session)
        preference = await pref_repo.get_by_traveler_id(traveler_id)
        
        aff_repo = AffinityRepository(session)
        affinities_list = await aff_repo.get_by_traveler_id(traveler_id)
        affinities_dict = {
            (aff.dimension_type, aff.dimension_key): aff 
            for aff in affinities_list
        }
        
        inter_repo = InteractionRepository(session)
        recent_interactions = await inter_repo.get_recent_for_traveler(
            traveler_id, 
            event_types=["VIEW", "SAVE", "COMPLETE"], 
            limit=50
        )
        recently_seen = {i.experience_id for i in recent_interactions}
        
        profile = TravelerRankingProfile(
            traveler_id=traveler_id,
            preference=preference,
            affinities=affinities_dict,
            recently_seen_experience_ids=recently_seen
        )
        
        return self.ranker.rank(
            candidates=pipeline_items,
            traveler_profile=profile,
            context=context,
            settings=self.settings
        )
