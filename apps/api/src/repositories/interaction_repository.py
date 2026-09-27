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
        **kwargs: object,
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

    async def get_saved_experience_ids(self, traveler_id: str) -> list[str]:
        """Currently-saved experience ids for a traveler, derived from the
        interaction log rather than a separate saved-state table: an
        experience counts as saved when its most recent SAVE/UNSAVE event
        for this traveler is a SAVE. Two travelers' save state is always
        independent — everything here is scoped by traveler_id.

        `created_at` has only second-level precision on SQLite (this
        project's dev/test database — see TimestampMixin), so a rapid
        SAVE-then-UNSAVE within the same second can share one timestamp.
        This orders by `created_at` and folds rows into a dict in query
        order, so equal-timestamp rows resolve via each backend's own
        stable tie-break for an otherwise-unordered `ORDER BY` key
        (SQLite: physical insertion order; PostgreSQL: unspecified by the
        SQL standard, though empirically also insertion order in practice
        for a simple heap scan). A genuinely guaranteed tie-break would
        need a monotonic sequence column and a migration — not worth it
        for an edge case (two clicks on the same experience within the
        same second) whose worst case is a stale bookmark state that
        self-corrects on the next real save/unsave."""
        query = (
            select(TravelerInteraction.id, TravelerInteraction.experience_id, TravelerInteraction.event_type)
            .where(
                TravelerInteraction.traveler_id == traveler_id,
                TravelerInteraction.event_type.in_(("SAVE", "UNSAVE")),
            )
            .order_by(TravelerInteraction.created_at.asc())
        )

        result = await self.session.execute(query)
        latest_by_experience: dict[str, str] = {}
        for _interaction_id, experience_id, event_type in result.all():
            latest_by_experience[experience_id] = event_type

        return [
            experience_id
            for experience_id, event_type in latest_by_experience.items()
            if event_type == "SAVE"
        ]
