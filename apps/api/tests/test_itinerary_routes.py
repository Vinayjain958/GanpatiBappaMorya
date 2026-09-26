"""ItineraryRouteService / build_map_data tests (ADR-056).

Service-level: route leg calculation, truthful failure handling (NoRoute,
timeout, malformed response, adapter exception), totals aggregation,
source preservation, key-based reuse and stale-geometry removal.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.adapters.routing import MockRoutingAdapter, OSRMRoutingAdapter
from src.core.config import Settings
from src.services.itinerary_routes import (
    ESTIMATED,
    NOT_APPLICABLE,
    ROUTED,
    UNAVAILABLE,
    ItineraryRouteService,
    StopView,
    build_map_data,
    waypoint_key,
)
from tests.planning_fixtures import (
    NO_ROUTE,
    TIMEOUT,
    FakeOSRMRoutingAdapter,
    MalformedRoutingAdapter,
    RaisingRoutingAdapter,
    fixture_linestring,
)

START = (18.9300, 72.8300)
A = (18.9400, 72.8350)
B = (18.9600, 72.8400)
C = (18.9800, 72.8450)


@dataclass
class FakeItem:
    """Duck-typed ItineraryItem for service-level tests."""

    id: str
    sequence_order: int
    experience_id: str = "exp"
    travel_from_previous_minutes: float | None = None
    travel_from_previous_distance_km: float | None = None
    travel_mode: str | None = None
    route_status: str | None = None
    route_source: str | None = None
    route_geometry: dict[str, Any] | None = None
    route_waypoint_key: str | None = None
    route_calculated_at: datetime | None = None


def _items(n: int) -> list[FakeItem]:
    return [FakeItem(id=f"item-{i}", sequence_order=i) for i in range(1, n + 1)]


def _refresh(adapter, items, coords, start=START, force=False):
    return asyncio.run(
        ItineraryRouteService(adapter).refresh_item_legs(
            items=items, coordinates_by_item_id=coords, start_location=start, travel_mode="driving", force=force
        )
    )


def test_single_leg_from_start_location_osrm_geometry_preserved() -> None:
    adapter = FakeOSRMRoutingAdapter()
    items = _items(1)
    stats = _refresh(adapter, items, {"item-1": A})
    item = items[0]
    assert stats.computed == 1 and stats.failed == 0
    assert item.route_status == ROUTED
    assert item.route_source == "osrm"
    # The exact geometry the adapter returned is persisted — not rebuilt.
    assert item.route_geometry == fixture_linestring(START, A)
    assert item.route_waypoint_key == waypoint_key(START, A, "driving")
    assert adapter.calls[0][2] is True  # include_geometry requested
    assert item.travel_from_previous_distance_km is not None and item.travel_from_previous_distance_km > 0


def test_multiple_legs_chain_previous_stop_to_next() -> None:
    adapter = FakeOSRMRoutingAdapter()
    items = _items(3)
    _refresh(adapter, items, {"item-1": A, "item-2": B, "item-3": C})
    assert [call[:2] for call in adapter.calls] == [(START, A), (A, B), (B, C)]
    assert all(i.route_status == ROUTED for i in items)


def test_first_stop_without_start_location_is_not_applicable() -> None:
    adapter = FakeOSRMRoutingAdapter()
    items = _items(2)
    _refresh(adapter, items, {"item-1": A, "item-2": B}, start=None)
    assert items[0].route_status == NOT_APPLICABLE
    assert items[0].route_geometry is None
    assert items[1].route_status == ROUTED
    assert len(adapter.calls) == 1


def test_haversine_estimate_is_labelled_and_never_given_geometry() -> None:
    items = _items(2)
    _refresh(MockRoutingAdapter(), items, {"item-1": A, "item-2": B})
    for item in items:
        assert item.route_status == ESTIMATED
        assert item.route_source == "haversine_estimate"
        assert item.route_geometry is None  # a straight line is not a route


def test_no_route_is_unavailable_with_no_fabricated_values() -> None:
    items = _items(1)
    stats = _refresh(RaisingRoutingAdapter(NO_ROUTE), items, {"item-1": A})
    assert stats.failed == 1
    assert items[0].route_status == UNAVAILABLE
    assert items[0].route_geometry is None
    assert items[0].route_source is None
    assert items[0].travel_from_previous_minutes is None


def test_timeout_is_unavailable() -> None:
    items = _items(1)
    _refresh(RaisingRoutingAdapter(TIMEOUT), items, {"item-1": A})
    assert items[0].route_status == UNAVAILABLE


def test_unexpected_adapter_exception_is_unavailable_not_a_crash() -> None:
    items = _items(1)
    _refresh(RaisingRoutingAdapter(RuntimeError("boom")), items, {"item-1": A})
    assert items[0].route_status == UNAVAILABLE


def test_malformed_route_values_are_rejected() -> None:
    items = _items(1)
    _refresh(MalformedRoutingAdapter(), items, {"item-1": A})
    assert items[0].route_status == UNAVAILABLE
    assert items[0].route_geometry is None


def test_osrm_adapter_raises_typed_error_on_malformed_payload(monkeypatch) -> None:
    adapter = OSRMRoutingAdapter(Settings(osrm_min_interval_seconds=0))

    async def fake_request(path, params):
        return {"code": "Ok", "routes": [{"geometry": {"type": "LineString", "coordinates": []}}]}

    monkeypatch.setattr(adapter, "_request", fake_request)
    items = _items(1)
    _refresh(adapter, items, {"item-1": A})
    assert items[0].route_status == UNAVAILABLE


def test_unchanged_legs_are_reused_not_rerouted() -> None:
    adapter = FakeOSRMRoutingAdapter()
    items = _items(2)
    _refresh(adapter, items, {"item-1": A, "item-2": B})
    first_calls = len(adapter.calls)
    stats = _refresh(adapter, items, {"item-1": A, "item-2": B})
    assert stats.reused == 2 and stats.computed == 0
    assert len(adapter.calls) == first_calls


def test_changed_waypoints_reroute_and_drop_stale_geometry() -> None:
    adapter = FakeOSRMRoutingAdapter()
    items = _items(2)
    _refresh(adapter, items, {"item-1": A, "item-2": B})
    old_geometry = items[1].route_geometry

    # Stop 1 replaced by a stop at C: both legs' waypoint pairs changed.
    _refresh(adapter, items, {"item-1": C, "item-2": B})
    assert items[1].route_geometry != old_geometry
    assert items[1].route_waypoint_key == waypoint_key(C, B, "driving")

    # Now routing fails for the changed leg: the old geometry AND the old
    # (different-pair) distance/time must not survive.
    _refresh(RaisingRoutingAdapter(NO_ROUTE), items, {"item-1": A, "item-2": C})
    assert items[1].route_status == UNAVAILABLE
    assert items[1].route_geometry is None
    assert items[1].travel_from_previous_minutes is None
    assert items[1].travel_from_previous_distance_km is None


def _stop(seq: int, status: str | None, *, km: float | None, mins: float | None, source: str | None, geometry=None):
    return StopView(
        item_id=f"item-{seq}", sequence=seq, title=f"Stop {seq}", lat=18.9 + seq / 100, lng=72.8,
        route_status=status, route_source=source, route_geometry=geometry,
        distance_km=km, duration_minutes=mins, travel_mode="driving", calculated_at=None,
    )


def test_summary_totals_are_backend_aggregated_from_usable_legs() -> None:
    geometry = {"type": "LineString", "coordinates": [[72.8, 18.9], [72.81, 18.91]]}
    data = build_map_data(
        stops=[
            _stop(1, ROUTED, km=2.0, mins=10.0, source="osrm", geometry=geometry),
            _stop(2, ROUTED, km=3.5, mins=12.5, source="osrm", geometry=geometry),
        ],
        start_location=None,
    )
    assert data.summary.total_distance_meters == 5500.0
    assert data.summary.total_duration_seconds == 1350.0
    assert data.summary.routing_source == "osrm"
    assert data.summary.status == "COMPLETE"
    assert data.summary.stop_count == 2
    assert data.summary.day_count == 1
    assert data.legs[0].geometry == geometry


def test_summary_marks_mixed_sources_and_partial_availability() -> None:
    data = build_map_data(
        stops=[
            _stop(1, NOT_APPLICABLE, km=None, mins=None, source=None),
            _stop(2, ROUTED, km=2.0, mins=10.0, source="osrm", geometry=None),
            _stop(3, ESTIMATED, km=1.0, mins=2.4, source="haversine_estimate"),
            _stop(4, UNAVAILABLE, km=9.9, mins=99.0, source=None),
        ],
        start_location=None,
    )
    assert [leg.to_sequence for leg in data.legs] == [2, 3, 4]
    assert data.summary.routing_source == "mixed"
    assert data.summary.routing_sources == ["haversine_estimate", "osrm"]
    assert data.summary.status == "PARTIAL"
    # The UNAVAILABLE leg's stored scheduling numbers are never reported.
    assert data.summary.total_distance_meters == 3000.0
    unavailable = data.legs[2]
    assert unavailable.distance_meters is None and unavailable.duration_seconds is None
    assert unavailable.geometry is None
    # An estimate never carries geometry even if some were stored.
    assert data.legs[1].geometry is None


def test_legacy_items_without_snapshot_report_route_unavailable() -> None:
    data = build_map_data(
        stops=[_stop(1, None, km=None, mins=None, source=None), _stop(2, None, km=2.0, mins=8.0, source=None)],
        start_location=None,
    )
    assert data.summary.status == "UNAVAILABLE"
    assert data.summary.total_distance_meters is None
    assert all(leg.status == UNAVAILABLE for leg in data.legs)


def test_no_legs_status() -> None:
    data = build_map_data(stops=[_stop(1, NOT_APPLICABLE, km=None, mins=None, source=None)], start_location=None)
    assert data.summary.status == "NO_LEGS"
    assert data.legs == []
