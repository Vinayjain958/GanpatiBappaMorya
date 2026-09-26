"""ItineraryRouteService — persisted route-leg snapshots (ADR-056).

Runs AFTER composition + validation have produced the final ordered
sequence of stops (never before — feasibility stays authoritative and
the map is only a factual representation of an already-decided plan).
Builds the waypoint list

    start location (if any) -> item 1 -> item 2 -> ... -> item N

and stores the leg ARRIVING at each item on that ItineraryItem row
(route_status/route_source/route_geometry/route_waypoint_key/
route_calculated_at; distance/duration stay in the existing
travel_from_previous_distance_km/minutes columns — no duplicate storage).

Routing always goes through the injected RoutingAdapter (OSRM, or the
MockRoutingAdapter's explicitly-labelled haversine estimate) — there is
no second OSRM client. Truthfulness rules:
  - OSRM success           -> ROUTED, real distance/duration, real GeoJSON
                              geometry (as returned; never synthesized)
  - haversine estimate     -> ESTIMATED, labelled, NEVER given geometry
                              (a straight line is not a route)
  - NoRoute / timeout /
    provider error /
    malformed response /
    unexpected exception   -> UNAVAILABLE: no distance/time/geometry is
                              claimed for that leg
A route failure never invalidates an otherwise-valid itinerary — routing
is not a hard feasibility condition in this domain; the composer/
validator already decided feasibility.

Re-routing is key-based: each leg remembers the (mode, from, to) it was
computed for. refresh_item_legs() recomputes only legs whose key changed
(or that previously failed), so an unchanged itinerary is never re-routed
and a replan never keeps stale geometry.
"""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from src.adapters.errors import AdapterError
from src.adapters.routing import RoutingAdapter
from src.schemas.itinerary import (
    ItineraryMapData,
    MapStop,
    RouteLegResponse,
    RoutePoint,
    RouteSummaryResponse,
)

logger = logging.getLogger(__name__)

ROUTED = "ROUTED"
ESTIMATED = "ESTIMATED"
UNAVAILABLE = "UNAVAILABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"

_USABLE = frozenset({ROUTED, ESTIMATED})

LatLng = tuple[float, float]


class RoutableItem(Protocol):
    """The ItineraryItem columns this service reads/writes."""

    id: str
    sequence_order: int
    travel_from_previous_minutes: float | None
    travel_from_previous_distance_km: float | None
    travel_mode: str | None
    route_status: str | None
    route_source: str | None
    route_geometry: dict[str, Any] | None
    route_waypoint_key: str | None
    route_calculated_at: datetime | None


@dataclass(frozen=True)
class LegResult:
    status: str
    source: str | None = None
    distance_km: float | None = None
    duration_minutes: float | None = None
    geometry: dict[str, Any] | None = None
    failure_reason: str | None = None


@dataclass
class RouteRefreshStats:
    computed: int = 0
    reused: int = 0
    failed: int = 0


def waypoint_key(origin: LatLng, destination: LatLng, travel_mode: str) -> str:
    return (
        f"{travel_mode}:{origin[0]:.5f},{origin[1]:.5f}>"
        f"{destination[0]:.5f},{destination[1]:.5f}"
    )


def _valid_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _valid_linestring(geometry: object) -> bool:
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
        return False
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return False
    return all(
        isinstance(c, (list, tuple))
        and len(c) >= 2
        and _valid_number(abs(c[0]))
        and _valid_number(abs(c[1]))
        for c in coords
    )


class ItineraryRouteService:
    def __init__(self, routing_adapter: RoutingAdapter) -> None:
        self._routing = routing_adapter

    async def compute_leg(self, origin: LatLng, destination: LatLng, travel_mode: str) -> LegResult:
        try:
            route = await self._routing.get_route(
                origin, destination, profile=travel_mode, include_geometry=True
            )
        except AdapterError as exc:
            # AdapterNoResultError (OSRM NoRoute) / AdapterUnavailableError
            # (timeout, HTTP error, malformed JSON) — both subclass AdapterError.
            return LegResult(status=UNAVAILABLE, failure_reason=type(exc).__name__)
        except ValueError as exc:  # disallowed routing profile
            return LegResult(status=UNAVAILABLE, failure_reason=f"ValueError: {exc}")
        except Exception as exc:  # noqa: BLE001 — malformed provider payload (KeyError/TypeError) or adapter bug
            return LegResult(status=UNAVAILABLE, failure_reason=type(exc).__name__)

        if not (_valid_number(route.distance_km) and _valid_number(route.duration_minutes)):
            return LegResult(status=UNAVAILABLE, failure_reason="malformed_route_values")

        if route.source == "osrm":
            geometry = route.geometry if _valid_linestring(route.geometry) else None
            return LegResult(
                status=ROUTED,
                source="osrm",
                distance_km=float(route.distance_km),
                duration_minutes=float(route.duration_minutes),
                geometry=geometry,
            )
        # Any non-OSRM source (today: MockRoutingAdapter's
        # "haversine_estimate") is an estimate — labelled as such, and
        # never drawn as a road route.
        return LegResult(
            status=ESTIMATED,
            source=route.source,
            distance_km=float(route.distance_km),
            duration_minutes=float(route.duration_minutes),
            geometry=None,
        )

    async def refresh_item_legs(
        self,
        *,
        items: Sequence[RoutableItem],
        coordinates_by_item_id: dict[str, LatLng | None],
        start_location: LatLng | None,
        travel_mode: str,
        itinerary_id: str | None = None,
        force: bool = False,
        now: datetime | None = None,
    ) -> RouteRefreshStats:
        """Brings every item's arriving-leg snapshot up to date for the
        current order. `items` must already be in final sequence order."""
        now = now or datetime.now(UTC)
        stats = RouteRefreshStats()
        started = time.monotonic()
        logger.info(
            "event=route_calculation_started itinerary_id=%s stops=%d has_start=%s mode=%s",
            itinerary_id, len(items), start_location is not None, travel_mode,
        )

        previous: LatLng | None = start_location
        for item in items:
            destination = coordinates_by_item_id.get(item.id)
            if destination is None:
                # No stored coordinates for this stop — nothing to route to.
                self._apply(item, LegResult(status=UNAVAILABLE, failure_reason="no_coordinates"), None, now)
                stats.failed += 1
                previous = None
                continue
            if previous is None:
                self._apply(item, LegResult(status=NOT_APPLICABLE), None, now)
                previous = destination
                continue

            key = waypoint_key(previous, destination, travel_mode)
            if not force and item.route_waypoint_key == key and item.route_status in _USABLE:
                stats.reused += 1
            else:
                result = await self.compute_leg(previous, destination, travel_mode)
                if result.status == UNAVAILABLE:
                    stats.failed += 1
                    logger.warning(
                        "event=route_calculation_failed itinerary_id=%s sequence=%d reason=%s",
                        itinerary_id, item.sequence_order, result.failure_reason,
                    )
                else:
                    stats.computed += 1
                self._apply(item, result, key, now, travel_mode=travel_mode)
            previous = destination

        logger.info(
            "event=route_calculation_completed itinerary_id=%s computed=%d reused=%d failed=%d duration_ms=%d",
            itinerary_id, stats.computed, stats.reused, stats.failed, int((time.monotonic() - started) * 1000),
        )
        return stats

    async def refresh_persisted_itinerary(
        self,
        *,
        itinerary: Any,
        ordered_items: list[Any],
        experiences_by_id: dict[str, Any],
        default_travel_mode: str,
    ) -> RouteRefreshStats:
        """Re-derives legs for an already-persisted itinerary after its
        items changed (replan / manual add). Start location + travel mode
        come from the itinerary's planning profile when it has one. Only
        legs whose waypoint pair changed are re-routed. Also re-totals
        Itinerary.total_travel_minutes from the refreshed legs."""
        profile = getattr(itinerary, "planning_profile", None)
        start: LatLng | None = None
        travel_mode = default_travel_mode
        if profile is not None:
            if profile.start_location_lat is not None and profile.start_location_lng is not None:
                start = (profile.start_location_lat, profile.start_location_lng)
            travel_mode = profile.travel_mode or default_travel_mode

        coordinates: dict[str, LatLng | None] = {}
        for item in ordered_items:
            experience = experiences_by_id.get(item.experience_id)
            location = getattr(experience, "location", None)
            coordinates[item.id] = (
                (location.latitude, location.longitude)
                if location is not None and location.latitude is not None and location.longitude is not None
                else None
            )

        stats = await self.refresh_item_legs(
            items=ordered_items,
            coordinates_by_item_id=coordinates,
            start_location=start,
            travel_mode=travel_mode,
            itinerary_id=getattr(itinerary, "id", None),
        )
        itinerary.total_travel_minutes = sum(i.travel_from_previous_minutes or 0.0 for i in ordered_items)
        return stats

    @staticmethod
    def _apply(
        item: RoutableItem,
        result: LegResult,
        key: str | None,
        now: datetime,
        *,
        travel_mode: str | None = None,
    ) -> None:
        previous_key = item.route_waypoint_key
        item.route_status = result.status
        item.route_source = result.source
        item.route_geometry = result.geometry
        item.route_waypoint_key = key
        item.route_calculated_at = now

        if result.status in _USABLE:
            item.travel_from_previous_distance_km = round(result.distance_km or 0.0, 3)
            item.travel_from_previous_minutes = round(result.duration_minutes or 0.0, 2)
            if travel_mode:
                item.travel_mode = travel_mode
        elif result.status == UNAVAILABLE and previous_key is not None and previous_key != key:
            # The waypoints changed (e.g. after a replan) and the new leg
            # couldn't be routed: the old distance/time described a
            # different pair of stops — drop them rather than keep a
            # stale number. (A fresh compose has no previous key, so the
            # composer's own scheduling values for this exact pair stay.)
            item.travel_from_previous_distance_km = None
            item.travel_from_previous_minutes = None


# ─── Read-side: build the API map payload from persisted snapshots ──────


@dataclass(frozen=True)
class StopView:
    item_id: str
    sequence: int
    title: str | None
    lat: float | None
    lng: float | None
    route_status: str | None
    route_source: str | None
    route_geometry: dict[str, Any] | None
    distance_km: float | None
    duration_minutes: float | None
    travel_mode: str | None
    calculated_at: datetime | None


def build_map_data(
    *,
    stops: list[StopView],
    start_location: RoutePoint | None,
) -> ItineraryMapData:
    """Pure: persisted snapshot -> ItineraryMapData. Never calls routing.
    Totals are computed here, deterministically, from usable legs only."""
    ordered = sorted(stops, key=lambda s: s.sequence)
    map_stops = [
        MapStop(item_id=s.item_id, sequence=s.sequence, title=s.title, lat=s.lat, lng=s.lng)
        for s in ordered
    ]

    legs: list[RouteLegResponse] = []
    prev: StopView | None = None
    for stop in ordered:
        # A pre-ADR-056 item has no route snapshot at all: report it as
        # UNAVAILABLE (route not calculated) rather than guess a source.
        status = stop.route_status or UNAVAILABLE
        if status == NOT_APPLICABLE:
            prev = stop
            continue
        origin: RoutePoint | None
        if prev is not None:
            origin = (
                RoutePoint(lat=prev.lat, lng=prev.lng, label=prev.title)
                if prev.lat is not None and prev.lng is not None
                else None
            )
        else:
            origin = start_location
        usable = status in _USABLE
        legs.append(
            RouteLegResponse(
                to_item_id=stop.item_id,
                to_sequence=stop.sequence,
                from_sequence=prev.sequence if prev is not None else None,
                origin=origin,
                destination=(
                    RoutePoint(lat=stop.lat, lng=stop.lng, label=stop.title)
                    if stop.lat is not None and stop.lng is not None
                    else None
                ),
                status=status,  # type: ignore[arg-type]
                distance_meters=(
                    round(stop.distance_km * 1000, 1) if usable and stop.distance_km is not None else None
                ),
                duration_seconds=(
                    round(stop.duration_minutes * 60, 1) if usable and stop.duration_minutes is not None else None
                ),
                geometry=stop.route_geometry if status == ROUTED else None,
                routing_source=stop.route_source if usable else None,
                travel_mode=stop.travel_mode if usable else None,
                # Always written in UTC by refresh_item_legs; SQLite drops
                # tzinfo on round-trip, so re-attach it for a stable contract.
                calculated_at=(
                    stop.calculated_at.replace(tzinfo=UTC)
                    if stop.calculated_at is not None and stop.calculated_at.tzinfo is None
                    else stop.calculated_at
                ),
            )
        )
        prev = stop

    return ItineraryMapData(
        start_location=start_location,
        stops=map_stops,
        legs=legs,
        summary=summarize_legs(legs, stop_count=len(map_stops)),
    )


def summarize_legs(legs: list[RouteLegResponse], *, stop_count: int) -> RouteSummaryResponse:
    usable = [
        leg for leg in legs
        if leg.status in _USABLE and leg.distance_meters is not None and leg.duration_seconds is not None
    ]
    routed = sum(1 for leg in legs if leg.status == ROUTED)
    estimated = sum(1 for leg in legs if leg.status == ESTIMATED)
    unavailable = sum(1 for leg in legs if leg.status == UNAVAILABLE)
    sources = sorted({leg.routing_source for leg in usable if leg.routing_source})

    if not legs:
        status = "NO_LEGS"
    elif not usable:
        status = "UNAVAILABLE"
    elif len(usable) == len(legs):
        status = "COMPLETE"
    else:
        status = "PARTIAL"

    routing_source: str | None
    if not sources:
        routing_source = None
    elif len(sources) == 1:
        routing_source = sources[0]
    else:
        routing_source = "mixed"

    return RouteSummaryResponse(
        status=status,  # type: ignore[arg-type]
        total_distance_meters=round(sum(leg.distance_meters or 0.0 for leg in usable), 1) if usable else None,
        total_duration_seconds=round(sum(leg.duration_seconds or 0.0 for leg in usable), 1) if usable else None,
        routing_source=routing_source,
        routing_sources=sources,
        leg_count=len(legs),
        routed_leg_count=routed,
        estimated_leg_count=estimated,
        unavailable_leg_count=unavailable,
        stop_count=stop_count,
        day_count=1,
    )


__all__ = [
    "ESTIMATED",
    "ItineraryRouteService",
    "LegResult",
    "NOT_APPLICABLE",
    "ROUTED",
    "RouteRefreshStats",
    "StopView",
    "UNAVAILABLE",
    "build_map_data",
    "summarize_legs",
    "waypoint_key",
]
