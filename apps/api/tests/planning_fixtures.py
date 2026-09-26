"""TEST FIXTURES ONLY — personalized planning / similarity / route tests.

Everything here is synthetic test data used exclusively by the pytest
suite (in-memory SQLite). None of it is ever seeded into the dev or
production database, and none of the coordinates/geometry below are
shipped as runtime itinerary data.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import update

from src.adapters.errors import AdapterNoResultError, AdapterUnavailableError
from src.adapters.routing import MatrixEntry, MockRoutingAdapter, RouteResult
from src.core.geo import haversine_km
from src.models import Experience
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.models.itinerary_planning_profile import ItineraryPlanningProfile

FIXTURE_DATE = "2026-10-12"  # a Monday inside the discovery_dataset availability window


def participants(*ages: int, genders: list[str | None] | None = None) -> list[dict[str, Any]]:
    genders = genders or ["prefer_not_to_say"] * len(ages)
    return [
        {"sequence": i + 1, "age_years": age, "gender": genders[i]}
        for i, age in enumerate(ages)
    ]


def planning(*ages: int, genders: list[str | None] | None = None, **extra: Any) -> dict[str, Any]:
    return {"group_size": len(ages), "participants": participants(*ages, genders=genders), **extra}


def compose_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": "food",
        "itinerary_date": FIXTURE_DATE,
        "start_time": "09:00:00",
        "end_time": "20:00:00",
        "max_experiences": 3,
        "travel_mode": "driving",
        "city": "Mumbai",
    }
    payload.update(overrides)
    return payload


def similar_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "city": "Mumbai",
        "itinerary_date": FIXTURE_DATE,
        "interests": ["food"],
        "pace": "balanced",
        "planning": planning(21, 22, 24, 26),
    }
    payload.update(overrides)
    return payload


def set_capacity(session_factory, experience_ids: list[str], capacity: int | None) -> None:
    """Gives fixture experiences an authoritative capacity (the
    discovery_dataset fixture has none, which the existing feasibility
    engine correctly treats as UNKNOWN for any party size)."""

    async def _run() -> None:
        async with session_factory() as session:
            await session.execute(
                update(Experience)
                .where(Experience.id.in_(experience_ids))
                .values(capacity=capacity, maximum_group_size=capacity)
            )
            await session.commit()

    asyncio.run(_run())


def insert_historical_itinerary(
    session_factory,
    *,
    traveler_id: str,
    destination_key: str | None = "mumbai",
    destination_label: str | None = "Mumbai",
    group_size: int = 4,
    adults: int = 4,
    children: int = 0,
    teens: int = 0,
    seniors: int = 0,
    interests: list[str] | None = None,
    budget_max: float | None = None,
    pace: str = "balanced",
    accessibility: list[str] | None = None,
    trip_month: int = 10,
    is_discoverable: bool = False,
    status: str = "VALIDATED",
    created_offset_minutes: int = 0,
    experience_id: str | None = None,
) -> str:
    """Inserts a previously-generated itinerary + planning profile row
    directly (test fixture for similarity tests)."""

    async def _run() -> str:
        async with session_factory() as session:
            itinerary = Itinerary(
                id=str(uuid.uuid4()),
                traveler_id=traveler_id,
                title="Fixture itinerary",
                itinerary_date=date(2026, trip_month, 12),
                start_time=time(9, 0),
                end_time=time(18, 0),
                status=status,
                source="COMPOSER",
                is_discoverable=is_discoverable,
                narrative_summary="PRIVATE NOTE fixture narrative",
                created_at=datetime(2026, 9, 1, tzinfo=UTC) + timedelta(minutes=created_offset_minutes),
            )
            session.add(itinerary)
            await session.flush()
            distribution: dict[str, int] = {}
            if adults:
                distribution["25_34"] = adults
            if children:
                distribution["6_12"] = children
            if teens:
                distribution["13_17"] = teens
            if seniors:
                distribution["65_PLUS"] = seniors
            session.add(
                ItineraryPlanningProfile(
                    itinerary_id=itinerary.id,
                    destination_key=destination_key,
                    destination_label=destination_label,
                    group_size=group_size,
                    children_count=children,
                    teens_count=teens,
                    adults_count=adults,
                    seniors_count=seniors,
                    age_band_distribution=distribution,
                    interests=sorted(interests if interests is not None else ["food"]),
                    budget_max=budget_max,
                    pace=pace,
                    accessibility_requirements=accessibility or [],
                    travel_mode="driving",
                    trip_month=trip_month,
                    similarity_signature="fixture",
                    profile_version="fixture",
                )
            )
            if experience_id is not None:
                session.add(
                    ItineraryItem(
                        itinerary_id=itinerary.id,
                        experience_id=experience_id,
                        sequence_order=1,
                        planned_start=datetime(2026, trip_month, 12, 10, 0),
                        planned_end=datetime(2026, trip_month, 12, 11, 0),
                        duration_minutes=60,
                        travel_from_previous_minutes=9.0,
                        travel_from_previous_distance_km=2.1,
                        route_status="ROUTED",
                        route_source="osrm",
                    )
                )
            await session.commit()
            return itinerary.id

    return asyncio.run(_run())


# ─── Routing adapter fixtures ────────────────────────────────────────────


def fixture_linestring(origin: tuple[float, float], destination: tuple[float, float]) -> dict[str, Any]:
    """A deterministic fake 'road' polyline (3 vertices, bent through a
    midpoint offset) — TEST FIXTURE geometry, lng/lat order like OSRM."""
    mid_lat = (origin[0] + destination[0]) / 2 + 0.001
    mid_lng = (origin[1] + destination[1]) / 2 - 0.001
    return {
        "type": "LineString",
        "coordinates": [[origin[1], origin[0]], [mid_lng, mid_lat], [destination[1], destination[0]]],
    }


class FakeOSRMRoutingAdapter:
    """Behaves like a successful OSRM adapter (source='osrm', GeoJSON
    geometry when requested). Records every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[float, float], tuple[float, float], bool]] = []

    async def get_route(self, origin, destination, *, profile, include_geometry=False) -> RouteResult:
        self.calls.append((origin, destination, include_geometry))
        distance = round(haversine_km(origin[0], origin[1], destination[0], destination[1]) * 1.3, 3)
        return RouteResult(
            distance_km=distance,
            duration_minutes=round(distance / 20 * 60, 2),
            geometry=fixture_linestring(origin, destination) if include_geometry else None,
            source="osrm",
        )

    async def get_travel_time_matrix(self, origin, destinations, *, profile) -> list[MatrixEntry]:
        return await MockRoutingAdapter().get_travel_time_matrix(origin, destinations, profile=profile)


class RaisingRoutingAdapter:
    """get_route always raises the given exception (NoRoute/timeout/etc.)."""

    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.calls = 0

    async def get_route(self, origin, destination, *, profile, include_geometry=False) -> RouteResult:
        self.calls += 1
        raise self.exc

    async def get_travel_time_matrix(self, origin, destinations, *, profile) -> list[MatrixEntry]:
        raise self.exc


class MalformedRoutingAdapter:
    """Returns a RouteResult with nonsense values (simulates a provider
    payload that parsed but is not a usable route)."""

    async def get_route(self, origin, destination, *, profile, include_geometry=False) -> RouteResult:
        return RouteResult(distance_km=float("nan"), duration_minutes=-5.0, geometry={"type": "Point"}, source="osrm")

    async def get_travel_time_matrix(self, origin, destinations, *, profile) -> list[MatrixEntry]:
        return []


NO_ROUTE = AdapterNoResultError("OSRM: NoRoute — fixture")
TIMEOUT = AdapterUnavailableError("OSRM request timed out (fixture)")
