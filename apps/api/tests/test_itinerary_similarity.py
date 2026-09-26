"""ItinerarySimilarityService + POST /itineraries/similar tests (ADR-056):
deterministic scoring, eligibility, privacy (private itineraries never
exposed as examples, no owner/participant leakage), no persistence side
effects, pagination/ordering, and a gender-fairness regression guard."""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import date

import pytest
from sqlalchemy import func, select

from src.core.itinerary_planning import SIMILARITY_THRESHOLD, SIMILARITY_WEIGHTS, GroupSignals
from src.models.itinerary import Itinerary
from src.models.itinerary_participant import ItineraryParticipant
from src.models.itinerary_planning_profile import ItineraryPlanningProfile
from src.schemas.itinerary import ItineraryPlanningContext
from src.services.itinerary_similarity import (
    NormalizedTripProfile,
    build_normalized_profile,
    score_profiles,
)
from tests.conftest import auth_header, register_traveler
from tests.planning_fixtures import (
    compose_payload,
    insert_historical_itinerary,
    planning,
    set_capacity,
    similar_payload,
)

SIMILAR = "/api/v1/itineraries/similar"


def _profile(**overrides) -> NormalizedTripProfile:
    base = dict(
        destination_key="mumbai",
        group=GroupSignals(group_size=4, adults_count=4, age_band_distribution={"25_34": 4}),
        interests=("food",),
        budget_max=2000.0,
        pace="balanced",
        accessibility=(),
        trip_month=10,
    )
    base.update(overrides)
    return NormalizedTripProfile(**base)


def _count(session_factory, model) -> int:
    async def _run() -> int:
        async with session_factory() as session:
            return (await session.execute(select(func.count()).select_from(model))).scalar_one()

    return asyncio.run(_run())


# ─── Pure scoring ─────────────────────────────────────────────────────────


def test_weights_are_normalized_and_have_no_gender_dimension() -> None:
    assert sum(SIMILARITY_WEIGHTS.values()) == pytest.approx(1.0)
    assert not any("gender" in name for name in SIMILARITY_WEIGHTS)
    assert "gender" not in {f.name for f in dataclasses.fields(NormalizedTripProfile)}
    assert "gender" not in {f.name for f in dataclasses.fields(GroupSignals)}


def test_exact_profile_scores_one() -> None:
    result = score_profiles(_profile(), _profile())
    assert result.score == 1.0
    assert set(result.matched_dimensions) == set(SIMILARITY_WEIGHTS)


def test_same_destination_only_is_below_threshold() -> None:
    other = _profile(
        group=GroupSignals(group_size=12, seniors_count=12, age_band_distribution={"65_PLUS": 12}),
        interests=("nightlife",), budget_max=20000.0, pace="packed", trip_month=4,
    )
    result = score_profiles(_profile(), other)
    assert result.score < SIMILARITY_THRESHOLD
    assert "destination" in result.matched_dimensions


def test_different_destination_scores_lower() -> None:
    same = score_profiles(_profile(), _profile())
    different = score_profiles(_profile(), _profile(destination_key="goa"))
    assert different.score < same.score
    assert different.components["destination"] == 0.0


def test_same_city_different_locality_is_partial_match() -> None:
    result = score_profiles(_profile(destination_key="mumbai|fort"), _profile(destination_key="mumbai|bandra"))
    assert 0 < result.components["destination"] < 1


def test_same_group_profile_matches_by_distribution_not_exact_ages() -> None:
    a = _profile(group=GroupSignals(group_size=4, adults_count=4, age_band_distribution={"18_24": 3, "25_34": 1}))
    b = _profile(group=GroupSignals(group_size=4, adults_count=4, age_band_distribution={"25_34": 2, "35_49": 2}))
    assert score_profiles(a, b).components["group_profile"] == 1.0
    family = _profile(group=GroupSignals(group_size=4, adults_count=2, children_count=2))
    assert score_profiles(a, family).components["group_profile"] < 1.0


def test_similar_interests_score_by_overlap() -> None:
    a = _profile(interests=("food", "heritage"))
    assert score_profiles(a, _profile(interests=("food",))).components["interests"] == 0.5
    assert score_profiles(a, _profile(interests=("nightlife",))).components["interests"] == 0.0


def test_different_budget_and_pace_lower_the_score() -> None:
    base = score_profiles(_profile(), _profile()).score
    assert score_profiles(_profile(), _profile(budget_max=10000.0)).score < base
    assert score_profiles(_profile(), _profile(pace="packed")).score < base
    assert score_profiles(_profile(pace="relaxed"), _profile(pace="packed")).components["pace"] == 0.0
    assert score_profiles(_profile(pace="relaxed"), _profile(pace="balanced")).components["pace"] == 0.5


def test_accessibility_is_strong_only_when_requested() -> None:
    wanted = _profile(accessibility=("wheelchair_accessible",))
    assert score_profiles(wanted, _profile()).components["accessibility"] == 0.0
    assert score_profiles(_profile(), wanted).components["accessibility"] == 1.0


def test_scoring_is_deterministic() -> None:
    a, b = _profile(), _profile(budget_max=2500.0, trip_month=12)
    assert score_profiles(a, b) == score_profiles(a, b)


def test_gender_never_changes_the_normalized_profile_or_score() -> None:
    """Regression guard against accidental generic gender weighting."""

    def build(genders):
        ctx = ItineraryPlanningContext.model_validate(planning(21, 22, 24, 26, genders=genders))
        return build_normalized_profile(
            city="Mumbai", locality=None, itinerary_date=date(2026, 10, 12), interests=["food"],
            category_slugs=[], max_budget=None, pace="balanced", accessibility_requirements=[], planning=ctx,
        )

    female = build(["female"] * 4)
    male = build(["male"] * 4)
    undisclosed = build([None] * 4)
    assert female == male == undisclosed
    candidate = _profile()
    assert score_profiles(female, candidate) == score_profiles(male, candidate)


# ─── Endpoint ─────────────────────────────────────────────────────────────


@pytest.fixture()
def two_travelers(discovery_client):
    a = register_traveler(discovery_client, "similar-a@example.com")
    b = register_traveler(discovery_client, "similar-b@example.com")
    return a, b


def test_similar_requires_auth(discovery_client) -> None:
    assert discovery_client.post(SIMILAR, json=similar_payload()).status_code == 401


def test_similar_requires_destination_and_valid_group(discovery_client, two_travelers) -> None:
    _, b = two_travelers
    assert discovery_client.post(SIMILAR, json=similar_payload(city=None), headers=auth_header(b)).status_code == 422
    bad = similar_payload(planning={"group_size": 2, "participants": [{"sequence": 1, "age_years": 20}]})
    assert discovery_client.post(SIMILAR, json=bad, headers=auth_header(b)).status_code == 422
    assert discovery_client.post(SIMILAR, json=similar_payload(limit=500), headers=auth_header(b)).status_code == 422
    # Start-location coordinates are not accepted (not a similarity signal).
    assert discovery_client.post(
        SIMILAR, json=similar_payload(origin_lat=18.9), headers=auth_header(b)
    ).status_code == 422


def test_no_similar_itineraries_returns_zero(discovery_client, two_travelers) -> None:
    _, b = two_travelers
    body = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b)).json()
    assert body["similar_count"] == 0
    assert body["examples"] == []
    assert body["has_more"] is False


def test_similarity_search_never_persists_anything(discovery_client, two_travelers, session_factory) -> None:
    a, b = two_travelers
    insert_historical_itinerary(session_factory, traveler_id=a["traveler"]["id"])
    before = (_count(session_factory, Itinerary), _count(session_factory, ItineraryPlanningProfile),
              _count(session_factory, ItineraryParticipant))
    for _ in range(3):
        assert discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b)).status_code == 200
    after = (_count(session_factory, Itinerary), _count(session_factory, ItineraryPlanningProfile),
             _count(session_factory, ItineraryParticipant))
    assert before == after


def test_private_itinerary_counts_but_is_never_an_example(discovery_client, two_travelers, session_factory) -> None:
    a, b = two_travelers
    private_id = insert_historical_itinerary(session_factory, traveler_id=a["traveler"]["id"], is_discoverable=False)
    resp = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b))
    body = resp.json()
    assert body["similar_count"] == 1
    assert body["examples"] == []
    assert body["examples_total"] == 0
    raw = resp.text
    for forbidden in (private_id, a["traveler"]["id"], "similar-a@example.com", "PRIVATE NOTE", "Test Traveler"):
        assert forbidden not in raw


def test_discoverable_example_exposes_only_safe_fields(
    discovery_client, two_travelers, session_factory, discovery_dataset
) -> None:
    a, b = two_travelers
    example_id = insert_historical_itinerary(
        session_factory, traveler_id=a["traveler"]["id"], is_discoverable=True,
        experience_id=discovery_dataset["near_experience_id"],
    )
    resp = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b))
    body = resp.json()
    assert body["similar_count"] == 1
    [example] = body["examples"]
    assert example["example_id"] == example_id
    assert set(example) == {
        "example_id", "destination_label", "duration_days", "group_size", "pace", "interests",
        "category_names", "stop_count", "total_distance_km", "total_travel_minutes",
        "similarity_score", "matched_dimensions",
    }
    assert example["group_size"] == 4
    assert example["stop_count"] == 1
    assert example["category_names"] == ["Food & Drink"]
    assert example["total_distance_km"] == 2.1
    raw = resp.text
    for forbidden in (a["traveler"]["id"], "similar-a@example.com", "PRIVATE NOTE", "age_years", "gender", "traveler"):
        assert forbidden not in raw


def test_own_cancelled_and_other_city_itineraries_are_ineligible(
    discovery_client, two_travelers, session_factory
) -> None:
    a, b = two_travelers
    insert_historical_itinerary(session_factory, traveler_id=b["traveler"]["id"], is_discoverable=True)  # own
    insert_historical_itinerary(
        session_factory, traveler_id=a["traveler"]["id"], status="CANCELLED", is_discoverable=True
    )
    insert_historical_itinerary(
        session_factory, traveler_id=a["traveler"]["id"], destination_key="goa", destination_label="Goa",
        is_discoverable=True,
    )
    body = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b)).json()
    assert body["similar_count"] == 0


def test_dissimilar_same_city_itinerary_is_not_counted(discovery_client, two_travelers, session_factory) -> None:
    a, b = two_travelers
    insert_historical_itinerary(
        session_factory, traveler_id=a["traveler"]["id"], group_size=12, adults=0, seniors=12,
        interests=["nightlife"], budget_max=50000, pace="packed", trip_month=4,
    )
    body = discovery_client.post(SIMILAR, json=similar_payload(max_budget=1000), headers=auth_header(b)).json()
    assert body["similar_count"] == 0


def test_multiple_matches_are_ordered_deterministically_and_paginated(
    discovery_client, two_travelers, session_factory
) -> None:
    a, b = two_travelers
    tid = a["traveler"]["id"]
    exact = insert_historical_itinerary(
        session_factory, traveler_id=tid, is_discoverable=True, created_offset_minutes=1
    )
    tie_newer = insert_historical_itinerary(
        session_factory, traveler_id=tid, is_discoverable=True, created_offset_minutes=5
    )
    weaker = insert_historical_itinerary(
        session_factory, traveler_id=tid, is_discoverable=True, pace="packed", created_offset_minutes=9,
    )
    insert_historical_itinerary(session_factory, traveler_id=tid, is_discoverable=False, created_offset_minutes=3)

    first = discovery_client.post(SIMILAR, json=similar_payload(limit=2), headers=auth_header(b)).json()
    assert first["similar_count"] == 4
    assert first["examples_total"] == 3
    # Equal scores -> newer first; the weaker (pace mismatch) is last.
    assert [e["example_id"] for e in first["examples"]] == [tie_newer, exact]
    assert first["has_more"] is True
    second = discovery_client.post(SIMILAR, json=similar_payload(limit=2, offset=2), headers=auth_header(b)).json()
    assert [e["example_id"] for e in second["examples"]] == [weaker]
    assert second["has_more"] is False

    again = discovery_client.post(SIMILAR, json=similar_payload(limit=2), headers=auth_header(b)).json()
    assert again == first  # same input + same snapshot -> identical response


def test_real_composed_itinerary_becomes_similar_for_another_traveler(
    discovery_client, two_travelers, session_factory, discovery_dataset
) -> None:
    a, b = two_travelers
    set_capacity(
        session_factory,
        [discovery_dataset["near_experience_id"], discovery_dataset["mid_experience_id"],
         discovery_dataset["far_experience_id"]],
        10,
    )
    composed = discovery_client.post(
        "/api/v1/itineraries/compose",
        json=compose_payload(planning=planning(21, 22, 24, 26, is_discoverable=True)),
        headers=auth_header(a),
    ).json()
    assert composed.get("items"), composed

    body = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(b)).json()
    assert body["similar_count"] == 1
    assert body["examples"][0]["example_id"] == composed["id"]
    # The owner doesn't see their own plan echoed back as "similar".
    own = discovery_client.post(SIMILAR, json=similar_payload(), headers=auth_header(a)).json()
    assert own["similar_count"] == 0
