from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import ExperienceCategory


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ExperienceCategory]:
        query = select(ExperienceCategory).order_by(ExperienceCategory.sort_order)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> ExperienceCategory | None:
        query = select(ExperienceCategory).where(ExperienceCategory.slug == slug)
        result = await self._session.execute(query)
        return result.scalars().one_or_none()

    async def get_by_id(self, category_id: str) -> ExperienceCategory | None:
        return await self._session.get(ExperienceCategory, category_id)
