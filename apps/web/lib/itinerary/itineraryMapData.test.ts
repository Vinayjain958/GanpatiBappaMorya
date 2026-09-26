import { describe, expect, it } from "vitest";
import {
  filterRouteByDay,
  formatDistanceMeters,
  formatDurationSeconds,
  legsToFeatureCollection,
  routeBounds,
  routeSummaryDisplay,
  routingSourceLabel,
  stopAccessibleLabel,
  stopsToFeatureCollection,
  travelFromPreviousLabel,
} from "./itineraryMapData";
import { fixtureItinerary, fixtureLeg, fixtureRoute } from "./itineraryFixtures.test-data";

describe("stopsToFeatureCollection", () => {
  it("maps stops to numbered points labelled by sequence, never by id", () => {
    const fc = stopsToFeatureCollection(fixtureRoute(), "item-2");
    expect(fc.features).toHaveLength(2);
    expect(fc.features[0].geometry.coordinates).toEqual([72.835, 18.94]);
    expect(fc.features.map((f) => f.properties.label)).toEqual(["1", "2"]);
    expect(fc.features.map((f) => f.properties.selected)).toEqual([false, true]);
  });

  it("skips stops without coordinates instead of inventing a position", () => {
    const route = fixtureRoute({
      stops: [{ item_id: "x", sequence: 1, day_index: 0, title: "No coords", lat: null, lng: null }],
    });
    expect(stopsToFeatureCollection(route).features).toEqual([]);
    expect(stopsToFeatureCollection(null).features).toEqual([]);
  });
});

describe("legsToFeatureCollection", () => {
  it("draws only legs with real backend geometry", () => {
    const route = fixtureRoute({
      legs: [
        fixtureLeg(),
        fixtureLeg({ to_item_id: "item-2", to_sequence: 2, status: "ESTIMATED", geometry: null, routing_source: "haversine_estimate" }),
        fixtureLeg({ to_item_id: "item-3", to_sequence: 3, status: "UNAVAILABLE", geometry: null, distance_meters: null, duration_seconds: null }),
      ],
    });
    const fc = legsToFeatureCollection(route, "item-1");
    expect(fc.features).toHaveLength(1);
    expect(fc.features[0].geometry.type).toBe("LineString");
    expect(fc.features[0].properties).toEqual({ toItemId: "item-1", toSequence: 1, selected: true });
  });
});

describe("day filter (single-day phase)", () => {
  it("is identity for 'all' and for day 0", () => {
    const route = fixtureRoute();
    expect(filterRouteByDay(route, "all")).toBe(route);
    expect(filterRouteByDay(route, 0).stops).toHaveLength(2);
    expect(filterRouteByDay(route, 1).stops).toHaveLength(0);
  });
});

describe("routeSummaryDisplay", () => {
  it("formats backend totals without re-aggregating", () => {
    const view = routeSummaryDisplay(fixtureRoute());
    expect(view).toMatchObject({
      state: "available",
      distance: "8.7 km",
      duration: "34 min",
      stops: 2,
      days: 1,
      source: "OSRM road routing",
      isEstimate: false,
    });
  });

  it("reports 'Route unavailable' instead of fabricated totals", () => {
    const route = fixtureRoute({
      summary: { ...fixtureRoute().summary, status: "UNAVAILABLE", total_distance_meters: null, total_duration_seconds: null, routing_source: null, routing_sources: [] },
    });
    expect(routeSummaryDisplay(route)).toMatchObject({ state: "unavailable", headline: "Route unavailable", distance: null, duration: null });
    expect(routeSummaryDisplay(null).headline).toBe("Route unavailable");
  });

  it("flags partial routes and estimate sources honestly", () => {
    const route = fixtureRoute({
      summary: { ...fixtureRoute().summary, status: "PARTIAL", unavailable_leg_count: 1, routing_source: "haversine_estimate" },
    });
    const view = routeSummaryDisplay(route);
    expect(view.state).toBe("partial");
    expect(view.headline).toContain("1 of 2 legs");
    expect(view.isEstimate).toBe(true);
    expect(view.source).toBe("Straight-line estimate");
  });

  it("handles itineraries with no legs", () => {
    const route = fixtureRoute({ legs: [], summary: { ...fixtureRoute().summary, status: "NO_LEGS", leg_count: 0 } });
    expect(routeSummaryDisplay(route).state).toBe("none");
  });
});

describe("travelFromPreviousLabel", () => {
  it("uses the persisted leg (distance · time), distinct from experience duration", () => {
    const itinerary = fixtureItinerary();
    expect(travelFromPreviousLabel(itinerary, itinerary.items[0])).toBe("Travel from your starting point: 2.1 km · 9 min");
    expect(travelFromPreviousLabel(itinerary, itinerary.items[1])).toBe("Travel from previous stop: 6.6 km · 25 min");
  });

  it("labels estimates and never shows numbers for an unavailable leg", () => {
    const base = fixtureItinerary();
    const itinerary = fixtureItinerary({
      route: fixtureRoute({
        legs: [
          fixtureLeg({ status: "ESTIMATED", geometry: null, routing_source: "haversine_estimate" }),
          fixtureLeg({ to_item_id: "item-2", to_sequence: 2, from_sequence: 1, status: "UNAVAILABLE", geometry: null, distance_meters: null, duration_seconds: null }),
        ],
      }),
    });
    expect(travelFromPreviousLabel(itinerary, base.items[0])).toBe("Travel from your starting point: ~2.1 km · 9 min (estimate)");
    expect(travelFromPreviousLabel(itinerary, base.items[1])).toBe("Travel from previous stop: route unavailable");
  });

  it("falls back to the legacy gap label for pre-route-snapshot itineraries", () => {
    const itinerary = fixtureItinerary({ route: null });
    expect(travelFromPreviousLabel(itinerary, itinerary.items[1])).toBe("9 min travel");
  });
});

describe("helpers", () => {
  it("formats distances and durations", () => {
    expect(formatDistanceMeters(450)).toBe("450 m");
    expect(formatDistanceMeters(8700)).toBe("8.7 km");
    expect(formatDurationSeconds(2040)).toBe("34 min");
    expect(formatDurationSeconds(3900)).toBe("1 h 5 min");
  });

  it("labels routing sources without calling estimates OSRM", () => {
    expect(routingSourceLabel("osrm")).toBe("OSRM road routing");
    expect(routingSourceLabel("haversine_estimate")).not.toContain("OSRM");
    expect(routingSourceLabel(null)).toBeNull();
  });

  it("builds accessible stop labels", () => {
    expect(stopAccessibleLabel(2, "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya")).toBe(
      "Stop 2: Chhatrapati Shivaji Maharaj Vastu Sangrahalaya",
    );
  });

  it("computes bounds over stops, start and geometry", () => {
    const [[west, south], [east, north]] = routeBounds(fixtureRoute())!;
    expect(west).toBe(72.83);
    expect(south).toBe(18.93);
    expect(east).toBe(72.84);
    expect(north).toBe(18.95);
    expect(routeBounds(null)).toBeNull();
  });
});
