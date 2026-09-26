from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.geo import bounding_box
from src.models.category import ExperienceCategory
from src.models.experience import Experience
from src.models.location import Location
from src.models.provider import Provider


@dataclass
class ExperienceFilters:
    q: str | None = None
    category_slug: str | None = None
    city: str | None = None
    locality: str | None = None
    provider_id: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    min_duration_minutes: int | None = None
    max_duration_minutes: int | None = None
    source_type: str | None = None
    is_synthetic: bool | None = None
    status: str | None = "active"
    # Bounding box pre-filter — exact radius/haversine narrowing happens
    # in the discovery service, never at the SQL layer (portable across
    # SQLite/PostgreSQL, no PostGIS — docs/DECISIONS.md ADR-023).
    min_lat: float | None = None
    max_lat: float | None = None
    min_lng: float | None = None
    max_lng: float | None = None


class ExperienceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[Experience]]:
        return select(Experience).options(
            selectinload(Experience.category),
            selectinload(Experience.location),
            selectinload(Experience.provider),
            selectinload(Experience.opening_hours),
            selectinload(Experience.availability_slots),
        )

    def _apply_filters(
        self, query: Select[tuple[Experience]], filters: ExperienceFilters
    ) -> Select[tuple[Experience]]:
        query = query.join(Experience.location).join(Experience.category).join(Experience.provider)

        if filters.status:
            query = query.where(Experience.status == filters.status)
        if filters.category_slug:
            query = query.where(ExperienceCategory.slug == filters.category_slug)
        if filters.city and filters.locality:
            # Both given explicitly (e.g. a saved/normalized profile) —
            # honor each independently, case-insensitively.
            query = query.where(func.lower(Location.city) == filters.city.lower())
            query = query.where(func.lower(Location.locality) == filters.locality.lower())
        elif filters.city:
            # The composer UI has a single free-text "destination" field
            # that callers pass through as `city` — travelers commonly type
            # a neighborhood/locality name (e.g. "Dadar") rather than the
            # city itself ("Mumbai"). Match either column, case-insensitive,
            # so those destinations resolve instead of silently returning
            # zero candidates.
            destination = filters.city.lower()
            query = query.where(
                or_(
                    func.lower(Location.city) == destination,
                    func.lower(Location.locality) == destination,
                )
            )
        elif filters.locality:
            query = query.where(func.lower(Location.locality) == filters.locality.lower())
        if filters.provider_id:
            query = query.where(Experience.provider_id == filters.provider_id)
        if filters.min_price is not None:
            query = query.where(
                or_(Experience.price >= filters.min_price, Experience.minimum_price >= filters.min_price)
            )
        if filters.max_price is not None:
            query = query.where(
                or_(Experience.price <= filters.max_price, Experience.maximum_price <= filters.max_price)
            )
        if filters.min_duration_minutes is not None:
            query = query.where(Experience.duration_minutes >= filters.min_duration_minutes)
        if filters.max_duration_minutes is not None:
            query = query.where(Experience.duration_minutes <= filters.max_duration_minutes)
        if filters.source_type:
            query = query.where(Experience.source_type == filters.source_type)
        if filters.is_synthetic is not None:
            query = query.where(Experience.is_synthetic == filters.is_synthetic)
        if filters.min_lat is not None:
            query = query.where(Location.latitude >= filters.min_lat)
        if filters.max_lat is not None:
            query = query.where(Location.latitude <= filters.max_lat)
        if filters.min_lng is not None:
            query = query.where(Location.longitude >= filters.min_lng)
        if filters.max_lng is not None:
            query = query.where(Location.longitude <= filters.max_lng)
        if filters.q:
            like = f"%{filters.q.lower()}%"
            query = query.where(
                or_(
                    func.lower(Experience.title).like(like),
                    func.lower(Experience.short_description).like(like),
                    func.lower(Experience.full_description).like(like),
                    func.lower(ExperienceCategory.name).like(like),
                    func.lower(Location.locality).like(like),
                    func.lower(Location.city).like(like),
                    func.lower(Provider.business_name).like(like),
                )
            )
        return query

    async def search(self, filters: ExperienceFilters, *, cap: int = 1000) -> list[Experience]:
        """Returns every row matching the given filters, up to `cap`, with
        no SQL-level ordering/pagination — the discovery service applies
        relevance/distance scoring, sorting, and pagination in Python once
        it has this bounded candidate set (see services/discovery.py)."""
        query = self._apply_filters(self._base_query(), filters).limit(cap)
        rows = (await self._session.execute(query)).scalars().unique().all()
        return list(rows)

    async def list_by_provider(
        self,
        provider_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Experience], int]:
        query = self._base_query().where(Experience.provider_id == provider_id)
        count_query = select(func.count(Experience.id)).where(Experience.provider_id == provider_id)

        if status:
            query = query.where(Experience.status == status)
            count_query = count_query.where(Experience.status == status)

        query = query.order_by(Experience.created_at.desc()).limit(limit).offset(offset)

        total = (await self._session.execute(count_query)).scalar_one()
        rows = (await self._session.execute(query)).scalars().unique().all()
        return list(rows), total

    async def get_by_id(self, experience_id: str) -> Experience | None:
        query = self._base_query().where(Experience.id == experience_id)
        result = await self._session.execute(query)
        return result.scalars().unique().one_or_none()

    async def get_owned_by_id(self, experience_id: str, provider_id: str) -> Experience | None:
        query = self._base_query().where(
            Experience.id == experience_id, Experience.provider_id == provider_id
        )
        result = await self._session.execute(query)
        return result.scalars().unique().one_or_none()

    def add(self, experience: Experience) -> None:
        self._session.add(experience)

    async def find_nearby_active(
        self, *, latitude: float, longitude: float, radius_km: float
    ) -> list[Experience]:
        """Active experiences within a bounding box around a point, for
        deterministic duplicate-candidate lookup (spec §24/§26 — no AI in
        the match decision). Exact Haversine narrowing and name/phone/
        website matching happen in the caller
        (services/contribution_duplicate.py), same split as `search()`'s
        bounding-box-then-Python pattern."""
        box = bounding_box(latitude, longitude, radius_km)
        query = (
            self._base_query()
            .join(Experience.location)
            .where(
                Experience.status == "active",
                Location.latitude >= box.min_lat,
                Location.latitude <= box.max_lat,
                Location.longitude >= box.min_lng,
                Location.longitude <= box.max_lng,
            )
        )
        rows = (await self._session.execute(query)).scalars().unique().all()
        return list(rows)
