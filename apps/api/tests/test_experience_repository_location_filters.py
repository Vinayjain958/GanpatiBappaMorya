"""Regression test: the composer UI has a single free-text "destination"
field that gets passed through as `ExperienceFilters.city` regardless of
whether the traveler typed a city ("Mumbai") or a locality/neighborhood
("Dadar"). city/locality matching must therefore be case-insensitive and,
when only `city` is supplied, must also match against `locality` — or a
correctly-spelled neighborhood search silently returns zero results
(see docs/DECISIONS.md for the bug this guards against).
"""

from __future__ import annotations

import asyncio

import pytest

from src.models.category import ExperienceCategory
from src.models.experience import Experience
from src.models.location import Location
from src.models.provider import Provider
from src.repositories.experience_repository import ExperienceFilters, ExperienceRepository


@pytest.fixture()
def dadar_dataset(session_factory) -> None:
    async def _seed() -> None:
        async with session_factory() as session:
            category = ExperienceCategory(slug="food-drink", name="Food & Drink", sort_order=1)
            session.add(category)
            await session.flush()

            location = Location(
                latitude=19.0176, longitude=72.8434, place_name="Test Place",
                city="Mumbai", locality="Dadar",
                source_type="overture_places", is_synthetic=False,
            )
            session.add(location)

            provider = Provider(
                business_name="Test Provider", verification_status="catalog_imported",
                source_type="overture_places", is_synthetic=False,
            )
            session.add(provider)
            await session.flush()

            experience = Experience(
                provider=provider, category=category, location=location,
                title="Dadar Street Food Crawl", short_description="A street food crawl.",
                full_description="Explore street food stalls in Dadar.",
                minimum_price=100, maximum_price=500, price_type="range",
                price_source="estimated", is_price_estimated=True,
                duration_minutes=60, duration_is_estimated=True,
                status="active", verification_status="catalog_imported",
                opening_hours_status="unavailable", source_type="overture_places",
                source_record_id="rec-dadar", is_synthetic=False, is_enriched=True,
            )
            session.add(experience)
            await session.commit()

    asyncio.run(_seed())


def test_city_filter_matches_locality_case_insensitively(session_factory, dadar_dataset):
    """A traveler typing the neighborhood name ("dadar") into the single
    destination field — sent through as `city` — must still find
    experiences located in that locality, regardless of case."""

    async def _run() -> list[Experience]:
        async with session_factory() as session:
            repo = ExperienceRepository(session)
            return await repo.search(ExperienceFilters(city="dadar"))

    results = asyncio.run(_run())
    assert len(results) == 1
    assert results[0].title == "Dadar Street Food Crawl"


def test_city_filter_matches_city_case_insensitively(session_factory, dadar_dataset):
    async def _run() -> list[Experience]:
        async with session_factory() as session:
            repo = ExperienceRepository(session)
            return await repo.search(ExperienceFilters(city="MUMBAI"))

    results = asyncio.run(_run())
    assert len(results) == 1


def test_city_filter_no_match_for_unrelated_destination(session_factory, dadar_dataset):
    async def _run() -> list[Experience]:
        async with session_factory() as session:
            repo = ExperienceRepository(session)
            return await repo.search(ExperienceFilters(city="Pune"))

    results = asyncio.run(_run())
    assert results == []


def test_explicit_city_and_locality_both_applied_case_insensitively(session_factory, dadar_dataset):
    async def _run() -> list[Experience]:
        async with session_factory() as session:
            repo = ExperienceRepository(session)
            return await repo.search(ExperienceFilters(city="mumbai", locality="dadar"))

    results = asyncio.run(_run())
    assert len(results) == 1


def test_explicit_city_and_locality_mismatch_excludes(session_factory, dadar_dataset):
    async def _run() -> list[Experience]:
        async with session_factory() as session:
            repo = ExperienceRepository(session)
            return await repo.search(ExperienceFilters(city="mumbai", locality="bandra"))

    results = asyncio.run(_run())
    assert results == []
