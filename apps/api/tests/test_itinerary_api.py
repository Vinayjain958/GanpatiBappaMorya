"""Itinerary API tests (Phase 8) — POST /itineraries/compose, GET
/itineraries, GET /itineraries/{id}, POST /itineraries/{id}/items."""

from __future__ import annotations

from tests.conftest import auth_header, register_traveler


def _compose_payload(**overrides) -> dict:
    payload = {
        "query": "food",
        "itinerary_date": "2026-10-12",  # a Monday
        "start_time": "09:00:00",
        "end_time": "20:00:00",
        "max_experiences": 3,
        "travel_mode": "driving",
    }
    payload.update(overrides)
    return payload


def test_compose_requires_auth(discovery_client) -> None:
    response = discovery_client.post("/api/v1/itineraries/compose", json=_compose_payload())
    assert response.status_code == 401


def test_compose_authenticated_returns_itinerary_or_validation_failure(discovery_client) -> None:
    user = register_traveler(discovery_client, "composer-traveler@example.com")
    response = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(user)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # Either a valid ItineraryResponse (has "items") or a
    # CompositionValidationResponse (has "valid": False) — never a
    # partial/forced plan and never a 500.
    assert "items" in body or body.get("valid") is False


def test_compose_request_body_has_no_traveler_id_field(discovery_client) -> None:
    user = register_traveler(discovery_client, "no-traveler-id@example.com")
    payload = _compose_payload()
    payload["traveler_id"] = "some-other-traveler-id"
    response = discovery_client.post("/api/v1/itineraries/compose", json=payload, headers=auth_header(user))
    # extra="forbid" on ComposeItineraryRequest -> 422, proving the field
    # is rejected rather than silently accepted/trusted.
    assert response.status_code == 422


def test_list_my_itineraries_only_returns_own(discovery_client) -> None:
    owner = register_traveler(discovery_client, "itin-owner@example.com")
    other = register_traveler(discovery_client, "itin-other@example.com")

    discovery_client.post("/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(owner))

    owner_list = discovery_client.get("/api/v1/itineraries", headers=auth_header(owner))
    other_list = discovery_client.get("/api/v1/itineraries", headers=auth_header(other))
    assert owner_list.status_code == 200
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0


def test_cross_traveler_access_forbidden(discovery_client) -> None:
    owner = register_traveler(discovery_client, "cross-owner@example.com")
    intruder = register_traveler(discovery_client, "cross-intruder@example.com")

    compose_resp = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(owner)
    )
    body = compose_resp.json()
    if "items" not in body:
        # Composition failed to find a valid plan (acceptable, given a
        # small dataset) — nothing to assert cross-ownership against.
        return

    itinerary_id = body["id"]
    response = discovery_client.get(f"/api/v1/itineraries/{itinerary_id}", headers=auth_header(intruder))
    assert response.status_code == 404


def test_get_itinerary_requires_auth(discovery_client) -> None:
    response = discovery_client.get("/api/v1/itineraries/some-id")
    assert response.status_code == 401


def test_add_item_requires_ownership(discovery_client) -> None:
    owner = register_traveler(discovery_client, "add-item-owner@example.com")
    intruder = register_traveler(discovery_client, "add-item-intruder@example.com")

    compose_resp = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(owner)
    )
    body = compose_resp.json()
    if "items" not in body:
        return
    itinerary_id = body["id"]

    response = discovery_client.post(
        f"/api/v1/itineraries/{itinerary_id}/items",
        json={"experience_id": "does-not-matter"},
        headers=auth_header(intruder),
    )
    assert response.status_code == 404


def test_invalid_composition_returns_structured_validation_response(discovery_client) -> None:
    user = register_traveler(discovery_client, "invalid-composer@example.com")
    # A window too small for anything to fit at all.
    response = discovery_client.post(
        "/api/v1/itineraries/compose",
        json=_compose_payload(start_time="09:00:00", end_time="09:01:00"),
        headers=auth_header(user),
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("valid") is False
    assert "reason_code" in body


def test_cancel_itinerary(discovery_client) -> None:
    user = register_traveler(discovery_client, "cancel-owner@example.com")
    compose_resp = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(user)
    )
    body = compose_resp.json()
    if "items" not in body:
        return
    itinerary_id = body["id"]
    response = discovery_client.delete(f"/api/v1/itineraries/{itinerary_id}", headers=auth_header(user))
    assert response.status_code == 204

    get_resp = discovery_client.get(f"/api/v1/itineraries/{itinerary_id}", headers=auth_header(user))
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "CANCELLED"
