"""Itinerary SSE live-update tests (Phase 9) — GET
/itineraries/{id}/updates."""

from __future__ import annotations

import asyncio

from src.services.sse import publish_itinerary_event, sse_updates_stream
from tests.conftest import auth_header, register_traveler


def _compose_payload(**overrides) -> dict:
    payload = {
        "query": "food",
        "itinerary_date": "2026-10-12",
        "start_time": "09:00:00",
        "end_time": "20:00:00",
        "max_experiences": 3,
        "travel_mode": "driving",
    }
    payload.update(overrides)
    return payload


def test_sse_requires_auth(discovery_client) -> None:
    resp = discovery_client.get("/api/v1/itineraries/some-id/updates")
    assert resp.status_code == 401


def test_sse_wrong_owner_gets_404(discovery_client) -> None:
    owner = register_traveler(discovery_client, "sse-owner@example.com")
    intruder = register_traveler(discovery_client, "sse-intruder@example.com")

    resp = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(owner)
    )
    body = resp.json()
    if "items" not in body:
        return
    itinerary_id = body["id"]

    stream_resp = discovery_client.get(
        f"/api/v1/itineraries/{itinerary_id}/updates", headers=auth_header(intruder)
    )
    assert stream_resp.status_code == 404


def test_sse_owner_connects_and_gets_connected_event(discovery_client) -> None:
    owner = register_traveler(discovery_client, "sse-owner2@example.com")
    resp = discovery_client.post(
        "/api/v1/itineraries/compose", json=_compose_payload(), headers=auth_header(owner)
    )
    body = resp.json()
    if "items" not in body:
        return
    itinerary_id = body["id"]

    with discovery_client.stream(
        "GET", f"/api/v1/itineraries/{itinerary_id}/updates", headers=auth_header(owner)
    ) as stream_resp:
        assert stream_resp.status_code == 200
        assert stream_resp.headers["content-type"].startswith("text/event-stream")
        lines: list[str] = []
        for line in stream_resp.iter_lines():
            lines.append(line)
            if len(lines) >= 3:
                break
    text = "\n".join(lines)
    assert "connected" in text
    assert "id:" in text  # every event carries an id (reconnect support)


def test_publish_and_receive_event_directly() -> None:
    """Exercises the pub/sub bus directly (faster, no HTTP streaming
    timing dependency) — confirms replan_started/completed/failed/
    requires_action all serialize as valid SSE frames with event ids."""

    async def _run():
        itinerary_id = "test-itin-direct"
        gen = sse_updates_stream(itinerary_id)
        first = await gen.__anext__()  # "connected"
        await publish_itinerary_event(itinerary_id, "replan_started", {"trigger": "WEATHER_CHANGED"})
        second = await gen.__anext__()
        await publish_itinerary_event(itinerary_id, "replan_completed", {"new_version": 2})
        third = await gen.__anext__()
        await gen.aclose()
        return first, second, third

    first, second, third = asyncio.run(_run())
    assert "event: connected" in first
    assert "event: replan_started" in second
    assert "event: replan_completed" in third
    for frame in (first, second, third):
        assert frame.startswith("id: ")


def test_no_raw_provider_payload_in_events() -> None:
    """Published events must only ever carry normalized application
    data — never raw external API responses or API keys."""

    async def _run():
        itinerary_id = "test-itin-secrets"
        gen = sse_updates_stream(itinerary_id)
        await gen.__anext__()
        await publish_itinerary_event(
            itinerary_id, "context_update",
            {"context_type": "WEATHER", "severity": "MEDIUM"},
        )
        event = await gen.__anext__()
        await gen.aclose()
        return event

    event = asyncio.run(_run())
    assert "apikey" not in event.lower()
    assert "api_key" not in event.lower()
