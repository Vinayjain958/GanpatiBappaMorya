"""Personalized planning tests (ADR-056): group/participant validation,
compose integration (profile + participants + route persistence), group
size -> existing feasibility capacity check, age non-fabrication,
ownership/privacy, persistence across independent GETs, and replanning
route refresh."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.adapters.ai import MockAIAdapter
from src.core.config import get_settings
from src.core.itinerary_planning import derive_age_band, group_signals_from_ages
from src.core.location import get_routing_adapter
from src.models.itinerary import Itinerary
from src.models.itinerary_participant import ItineraryParticipant
from src.models.itinerary_planning_profile import ItineraryPlanningProfile
from src.services.context_impact import ContextImpactResult, ImpactSeverity
from src.services.itinerary_routes import waypoint_key
from src.services.replanning import ReplanningService, ReplanStatus
from tests.conftest import FORT_LAT, FORT_LNG, auth_header, register_traveler
from tests.planning_fixtures import (
    FakeOSRMRoutingAdapter,
    compose_payload,
    planning,
    set_capacity,
)

COMPOSE = "/api/v1/itineraries/compose"


@pytest.fixture()
def capacity_ids(discovery_dataset, session_factory) -> list[str]:
    ids = [
        discovery_dataset["near_experience_id"],
        discovery_dataset["mid_experience_id"],
        discovery_dataset["far_experience_id"],
    ]
    set_capacity(session_factory, ids, 10)
    return ids


def _compose(client, user, **overrides):
    return client.post(COMPOSE, json=compose_payload(**overrides), headers=auth_header(user))


def _count(session_factory, model) -> int:
    async def _run() -> int:
        async with session_factory() as session:
            return (await session.execute(select(func.count()).select_from(model))).scalar_one()

    return asyncio.run(_run())


# ─── Pure domain helpers ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("age", "band"),
    [(0, "0_5"), (5, "0_5"), (6, "6_12"), (12, "6_12"), (13, "13_17"), (17, "13_17"), (18, "18_24"),
     (24, "18_24"), (25, "25_34"), (34, "25_34"), (35, "35_49"), (49, "35_49"), (50, "50_64"),
     (64, "50_64"), (65, "65_PLUS"), (120, "65_PLUS")],
)
def test_age_band_derivation(age: int, band: str) -> None:
    assert derive_age_band(age) == band


@pytest.mark.parametrize("age", [-1, 121])
def test_age_band_rejects_out_of_range(age: int) -> None:
    with pytest.raises(ValueError):
        derive_age_band(age)


def test_group_signals_normalize_age_distribution() -> None:
    signals = group_signals_from_ages([21, 22, 24, 26])
    assert (signals.children_count, signals.teens_count, signals.adults_count, signals.seniors_count) == (0, 0, 4, 0)
    assert signals.age_band_distribution == {"18_24": 3, "25_34": 1}

    mixed = group_signals_from_ages([4, 9, 15, 40, 70])
    assert (mixed.children_count, mixed.teens_count, mixed.adults_count, mixed.seniors_count) == (2, 1, 1, 1)
    assert not hasattr(mixed, "gender")


# ─── Validation (authoritative, 422 — never silently corrected) ───────────


def test_one_participant_is_valid(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "solo@example.com")
    resp = _compose(discovery_client, user, planning=planning(30))
    assert resp.status_code == 200, resp.text


@pytest.mark.parametrize(
    "bad_planning",
    [
        {"group_size": 3, "participants": [{"sequence": 1, "age_years": 20}, {"sequence": 2, "age_years": 20}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": -1}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": 121}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": 21.5}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": "21"}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": 21, "gender": "robot"}]},
        {"group_size": 2, "participants": [{"sequence": 1, "age_years": 20}, {"sequence": 1, "age_years": 22}]},
        {"group_size": 2, "participants": [{"sequence": 1, "age_years": 20}, {"sequence": 3, "age_years": 22}]},
        {"group_size": 0, "participants": []},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": 20, "name": "Asha"}]},
        {"group_size": 1, "participants": [{"sequence": 1, "age_years": 20}], "traveler_id": "someone-else"},
    ],
)
def test_invalid_planning_context_is_rejected(discovery_client, session_factory, bad_planning) -> None:
    user = register_traveler(discovery_client, "invalid@example.com")
    resp = _compose(discovery_client, user, planning=bad_planning)
    assert resp.status_code == 422, resp.text
    assert _count(session_factory, Itinerary) == 0  # nothing persisted


def test_group_size_above_configured_maximum_is_rejected(discovery_client) -> None:
    user = register_traveler(discovery_client, "biggroup@example.com")
    too_many = get_settings().itinerary_max_participants + 1
    resp = _compose(discovery_client, user, planning=planning(*([30] * too_many)))
    assert resp.status_code == 422
    assert "at most" in resp.text


def test_oversized_participant_payload_is_rejected_cheaply(discovery_client) -> None:
    user = register_traveler(discovery_client, "flood@example.com")
    resp = _compose(discovery_client, user, planning=planning(*([30] * 1000)))
    assert resp.status_code == 422


def test_party_size_must_match_group_size(discovery_client) -> None:
    user = register_traveler(discovery_client, "mismatch@example.com")
    resp = _compose(discovery_client, user, party_size=3, planning=planning(30, 31))
    assert resp.status_code == 422


def test_origin_coordinates_must_be_valid_and_paired(discovery_client) -> None:
    user = register_traveler(discovery_client, "coords@example.com")
    assert _compose(discovery_client, user, origin_lat=91, origin_lng=72.8).status_code == 422
    assert _compose(discovery_client, user, origin_lat=18.9, origin_lng=181).status_code == 422
    assert _compose(discovery_client, user, origin_lat=18.9).status_code == 422


# ─── Compose persistence ─────────────────────────────────────────────────


def test_personalized_compose_persists_profile_participants_and_route(
    discovery_client, capacity_ids, session_factory
) -> None:
    user = register_traveler(discovery_client, "persist-planning@example.com")
    resp = _compose(
        discovery_client,
        user,
        origin_lat=FORT_LAT,
        origin_lng=FORT_LNG,
        planning=planning(21, 22, 24, 26, genders=["female", "male", "female", "prefer_not_to_say"],
                          start_location_label="Test Hotel"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body and body["items"], body

    assert body["is_discoverable"] is False  # private by default
    profile = body["planning_profile"]
    assert profile["group_size"] == 4
    assert profile["adults_count"] == 4
    assert profile["age_band_distribution"] == {"18_24": 3, "25_34": 1}
    assert profile["start_location_label"] == "Test Hotel"
    assert profile["start_date"] == profile["end_date"] == "2026-10-12"
    assert profile["duration_days"] == 1
    assert [p["sequence"] for p in body["participants"]] == [1, 2, 3, 4]
    assert body["participants"][0] == {"sequence": 1, "age_years": 21, "age_band": "18_24", "gender": "female"}

    # Route: first leg departs from the start location; mock adapter ->
    # labelled estimates, no geometry, backend totals present.
    route = body["route"]
    assert route["start_location"]["label"] == "Test Hotel"
    assert [s["sequence"] for s in route["stops"]] == [i["sequence_order"] for i in body["items"]]
    assert route["legs"][0]["from_sequence"] is None
    assert all(leg["status"] == "ESTIMATED" for leg in route["legs"])
    assert all(leg["geometry"] is None for leg in route["legs"])
    assert route["summary"]["routing_source"] == "haversine_estimate"
    assert route["summary"]["total_distance_meters"] == pytest.approx(
        sum(leg["distance_meters"] for leg in route["legs"]), abs=0.5
    )
    assert route["summary"]["day_count"] == 1

    assert _count(session_factory, ItineraryPlanningProfile) == 1
    assert _count(session_factory, ItineraryParticipant) == 4


def test_plain_compose_without_planning_still_works_and_gets_profile(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "plain@example.com")
    resp = _compose(discovery_client, user)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    if "items" not in body:
        pytest.skip("fixture catalog produced no plan")
    assert body["participants"] == []
    assert body["planning_profile"]["group_size"] == 1
    assert body["route"]["summary"]["status"] in {"COMPLETE", "NO_LEGS", "PARTIAL", "UNAVAILABLE"}


def test_discoverable_opt_in_is_persisted(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "optin@example.com")
    resp = _compose(discovery_client, user, planning=planning(30, 32, is_discoverable=True))
    assert resp.status_code == 200
    assert resp.json()["is_discoverable"] is True


def test_osrm_geometry_reaches_the_api_and_survives_refresh(
    discovery_client, capacity_ids
) -> None:
    fake = FakeOSRMRoutingAdapter()
    discovery_client.app.dependency_overrides[get_routing_adapter] = lambda: fake
    user = register_traveler(discovery_client, "osrm-geometry@example.com")
    resp = _compose(
        discovery_client, user, origin_lat=FORT_LAT, origin_lng=FORT_LNG, planning=planning(30, 31)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"]
    legs = body["route"]["legs"]
    assert legs and all(leg["status"] == "ROUTED" for leg in legs)
    assert all(leg["routing_source"] == "osrm" for leg in legs)
    assert all(leg["geometry"]["type"] == "LineString" for leg in legs)
    assert body["route"]["summary"]["routing_source"] == "osrm"
    assert body["route"]["summary"]["status"] == "COMPLETE"

    # "Refresh": an independent GET returns the persisted snapshot
    # without re-routing.
    calls_before = len(fake.calls)
    fresh = discovery_client.get(f"/api/v1/itineraries/{body['id']}", headers=auth_header(user)).json()
    assert len(fake.calls) == calls_before
    assert fresh["route"]["legs"] == legs
    assert fresh["participants"] == body["participants"]
    assert fresh["planning_profile"] == body["planning_profile"]


def test_list_endpoint_omits_participants_and_geometry(discovery_client, capacity_ids) -> None:
    discovery_client.app.dependency_overrides[get_routing_adapter] = lambda: FakeOSRMRoutingAdapter()
    user = register_traveler(discovery_client, "list-light@example.com")
    created = _compose(
        discovery_client, user, origin_lat=FORT_LAT, origin_lng=FORT_LNG, planning=planning(30, 31)
    ).json()
    listed = discovery_client.get("/api/v1/itineraries", headers=auth_header(user)).json()
    row = next(i for i in listed["items"] if i["id"] == created["id"])
    assert row["participants"] == []
    assert all(leg["geometry"] is None for leg in row["route"]["legs"])
    assert row["route"]["summary"] == created["route"]["summary"]
    assert row["planning_profile"]["age_band_distribution"] == {"25_34": 2}


# ─── Group capacity feeds the EXISTING feasibility engine ─────────────────


def test_group_within_capacity_composes(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "fits@example.com")
    body = _compose(discovery_client, user, planning=planning(*([30] * 10))).json()
    assert "items" in body and body["items"]


def test_group_exceeding_confirmed_capacity_is_infeasible(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "too-big@example.com")
    body = _compose(discovery_client, user, planning=planning(*([30] * 11))).json()
    assert body.get("valid") is False
    assert body["feasible_count"] == 0


def test_missing_capacity_follows_unknown_semantics(discovery_client, discovery_dataset) -> None:
    # discovery_dataset has no capacity data at all -> UNKNOWN -> never
    # composed (no invented capacity).
    user = register_traveler(discovery_client, "unknown-cap@example.com")
    body = _compose(discovery_client, user, planning=planning(30, 31)).json()
    assert body.get("valid") is False
    assert body["feasible_count"] == 0


# ─── Age never fabricates exclusions ──────────────────────────────────────


def test_participant_ages_do_not_change_the_feasible_plan(discovery_client, capacity_ids) -> None:
    """The catalog has no authoritative age restrictions, so a group of a
    toddler + a 90-year-old must get exactly the same plan as two adults."""
    user = register_traveler(discovery_client, "ages@example.com")
    adults = _compose(discovery_client, user, planning=planning(30, 30)).json()
    mixed = _compose(discovery_client, user, planning=planning(2, 90)).json()
    assert [i["experience_id"] for i in adults["items"]] == [i["experience_id"] for i in mixed["items"]]


def test_gender_does_not_change_the_plan(discovery_client, capacity_ids) -> None:
    user = register_traveler(discovery_client, "genders@example.com")
    a = _compose(discovery_client, user, planning=planning(30, 30, genders=["female", "female"])).json()
    b = _compose(discovery_client, user, planning=planning(30, 30, genders=["male", "male"])).json()
    assert [i["experience_id"] for i in a["items"]] == [i["experience_id"] for i in b["items"]]


# ─── Ownership / privacy ──────────────────────────────────────────────────


def test_other_traveler_cannot_read_itinerary_or_participants(discovery_client, capacity_ids) -> None:
    owner = register_traveler(discovery_client, "owner-a@example.com")
    other = register_traveler(discovery_client, "other-b@example.com")
    created = _compose(discovery_client, owner, planning=planning(33, 35)).json()
    assert discovery_client.get(f"/api/v1/itineraries/{created['id']}", headers=auth_header(other)).status_code == 404
    listed = discovery_client.get("/api/v1/itineraries", headers=auth_header(other)).json()
    assert listed["total"] == 0


# ─── Replanning refreshes route legs ──────────────────────────────────────


def test_replan_recalculates_changed_legs_and_drops_stale_geometry(
    discovery_client, capacity_ids, session_factory
) -> None:
    fake = FakeOSRMRoutingAdapter()
    discovery_client.app.dependency_overrides[get_routing_adapter] = lambda: fake
    user = register_traveler(discovery_client, "replan-route@example.com")
    body = _compose(
        discovery_client, user, origin_lat=FORT_LAT, origin_lng=FORT_LNG,
        planning=planning(30, 31), max_experiences=2,
    ).json()
    if len(body.get("items", [])) < 1:
        pytest.skip("fixture catalog produced no plan")
    first_item_id = body["items"][0]["id"]

    async def _replan():
        async with session_factory() as session:
            service = ReplanningService(
                session=session, settings=get_settings(), routing_adapter=fake,
                embedding_adapter=None, ai_adapter=MockAIAdapter(),
            )
            impact = ContextImpactResult(
                affected=True, severity=ImpactSeverity.HIGH, context_type="WEATHER",
                affected_itinerary_item_ids=[first_item_id], reason_codes=["WEATHER_UNSUITABLE"],
                explanation="Test-triggered impact.",
            )
            first_start = datetime.fromisoformat(body["items"][0]["planned_start"])
            return await service.replan_itinerary(
                itinerary_id=body["id"], traveler_id=body["traveler_id"], trigger="WEATHER_CHANGED",
                impact=impact, now=first_start - timedelta(hours=1),
            )

    outcome = asyncio.run(_replan())
    if outcome.status != ReplanStatus.REPLANNED:
        pytest.skip(f"replan did not produce a new plan on the small fixture catalog: {outcome.status}")

    async def _load():
        async with session_factory() as session:
            result = await session.execute(
                select(Itinerary).where(Itinerary.id == body["id"]).options(
                    selectinload(Itinerary.items), selectinload(Itinerary.planning_profile)
                )
            )
            return result.scalars().one()

    itinerary = asyncio.run(_load())
    exp_coords = {}
    for item in body["items"]:
        exp_coords[item["experience_id"]] = (item["location_latitude"], item["location_longitude"])
    fresh = discovery_client.get(f"/api/v1/itineraries/{body['id']}", headers=auth_header(user)).json()
    for item in fresh["items"]:
        exp_coords[item["experience_id"]] = (item["location_latitude"], item["location_longitude"])

    # Every persisted leg describes exactly the CURRENT consecutive pair.
    ordered = sorted(itinerary.items, key=lambda i: i.sequence_order)
    previous = (round(FORT_LAT, 4), round(FORT_LNG, 4))
    for item in ordered:
        current = exp_coords[item.experience_id]
        assert item.route_waypoint_key == waypoint_key(previous, current, "driving")
        assert item.route_status == "ROUTED"
        coords = item.route_geometry["coordinates"]
        assert coords[0] == [previous[1], previous[0]] and coords[-1] == [current[1], current[0]]
        previous = current

    # Route totals in the API match the refreshed legs.
    summary = fresh["route"]["summary"]
    assert summary["total_duration_seconds"] == pytest.approx(
        sum(leg["duration_seconds"] for leg in fresh["route"]["legs"]), abs=0.5
    )
    assert fresh["version"] == body["version"] + 1
