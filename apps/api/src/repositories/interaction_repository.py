from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interaction import TravelerInteraction


class InteractionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_client_event_id(self, traveler_id: str, client_event_id: str) -> TravelerInteraction | None:
        stmt = select(TravelerInteraction).where(
            TravelerInteraction.traveler_id == traveler_id,
            TravelerInteraction.client_event_id == client_event_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_recent_for_traveler(self, traveler_id: str, event_types: list[str], limit: int = 100) -> list[TravelerInteraction]:
        stmt = select(TravelerInteraction).where(
            TravelerInteraction.traveler_id == traveler_id,
            TravelerInteraction.event_type.in_(event_types)
        ).order_by(TravelerInteraction.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        traveler_id: str,
        experience_id: str,
        event_type: str,
        client_event_id: str,
        **kwargs,
    ) -> TravelerInteraction:
        # Idempotency check first
        existing = await self.get_by_client_event_id(traveler_id, client_event_id)
        if existing:
            return existing
            
        interaction = TravelerInteraction(
            traveler_id=traveler_id,
            experience_id=experience_id,
            event_type=event_type,
            client_event_id=client_event_id,
            **kwargs,
        )
        self.session.add(interaction)
        await self.session.flush()
        return interaction
