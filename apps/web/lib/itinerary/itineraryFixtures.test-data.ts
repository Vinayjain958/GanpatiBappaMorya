/**
 * TEST FIXTURES ONLY — used by the Vitest suites. Never imported by
 * runtime code; these coordinates/geometry are not real itinerary data.
 */
import type { ApiItinerary, ApiItineraryMapData, ApiRouteLeg } from "@/types/api";

export const fixtureLine: GeoJSON.LineString = {
  type: "LineString",
  coordinates: [
    [72.83, 18.93],
    [72.832, 18.935],
    [72.835, 18.94],
  ],
};

export function fixtureLeg(overrides: Partial<ApiRouteLeg> = {}): ApiRouteLeg {
  return {
    to_item_id: "item-1",
    to_sequence: 1,
    from_sequence: null,
    day_index: 0,
    origin: { lat: 18.93, lng: 72.83, label: "Fixture Hotel" },
    destination: { lat: 18.94, lng: 72.835, label: "Stop A" },
    status: "ROUTED",
    distance_meters: 2100,
    duration_seconds: 540,
    geometry: fixtureLine,
    routing_source: "osrm",
    travel_mode: "driving",
    calculated_at: "2026-09-26T10:00:00Z",
    ...overrides,
  };
}

export function fixtureRoute(overrides: Partial<ApiItineraryMapData> = {}): ApiItineraryMapData {
  return {
    start_location: { lat: 18.93, lng: 72.83, label: "Fixture Hotel" },
    stops: [
      { item_id: "item-1", sequence: 1, day_index: 0, title: "Stop A", lat: 18.94, lng: 72.835 },
      { item_id: "item-2", sequence: 2, day_index: 0, title: "Stop B", lat: 18.95, lng: 72.84 },
    ],
    legs: [
      fixtureLeg(),
      fixtureLeg({
        to_item_id: "item-2",
        to_sequence: 2,
        from_sequence: 1,
        distance_meters: 6600,
        duration_seconds: 1500,
      }),
    ],
    summary: {
      status: "COMPLETE",
      total_distance_meters: 8700,
      total_duration_seconds: 2040,
      routing_source: "osrm",
      routing_sources: ["osrm"],
      leg_count: 2,
      routed_leg_count: 2,
      estimated_leg_count: 0,
      unavailable_leg_count: 0,
      stop_count: 2,
      day_count: 1,
    },
    ...overrides,
  };
}

export function fixtureItinerary(overrides: Partial<ApiItinerary> = {}): ApiItinerary {
  const item = (id: string, seq: number, title: string) => ({
    id,
    experience_id: `exp-${seq}`,
    sequence_order: seq,
    planned_start: `2026-10-12T0${8 + seq}:00:00+05:30`,
    planned_end: `2026-10-12T0${8 + seq}:45:00+05:30`,
    duration_minutes: 45,
    travel_from_previous_minutes: 9,
    travel_from_previous_distance_km: 2.1,
    travel_mode: "driving",
    buffer_before_minutes: 10,
    buffer_after_minutes: 0,
    estimated_cost: 300,
    source_rank_position: seq,
    source_ranking_score: 0.8,
    narrative_text: null,
    title,
    short_description: null,
    category_name: "Food & Drink",
    location_place_name: title,
    location_latitude: 18.93 + seq / 100,
    location_longitude: 72.83,
    is_locked: false,
    item_state: "ACTIVE",
    route_status: "ROUTED" as const,
    route_source: "osrm",
  });
  return {
    id: "itin-1",
    traveler_id: "trav-1",
    title: "Fixture day",
    itinerary_date: "2026-10-12",
    start_time: "09:00:00",
    end_time: "18:00:00",
    status: "VALIDATED",
    source: "COMPOSER",
    total_duration_minutes: 90,
    total_travel_minutes: 34,
    estimated_total_cost: 600,
    currency: "INR",
    narrative_title: null,
    narrative_summary: null,
    narrative_closing_message: null,
    ranking_model_version: "weighted-v1",
    narrative_model_version: "template-fallback-v1",
    generated_at: "2026-09-26T10:00:00Z",
    created_at: "2026-09-26T10:00:00Z",
    updated_at: "2026-09-26T10:00:00Z",
    items: [item("item-1", 1, "Stop A"), item("item-2", 2, "Stop B")],
    version: 1,
    replanning_status: "STABLE",
    context_last_updated_at: null,
    is_discoverable: false,
    planning_profile: {
      destination_label: "Mumbai",
      start_date: "2026-10-12",
      end_date: "2026-10-12",
      duration_days: 1,
      group_size: 4,
      children_count: 0,
      teens_count: 0,
      adults_count: 4,
      seniors_count: 0,
      age_band_distribution: { "18_24": 3, "25_34": 1 },
      interests: ["food"],
      budget_max: null,
      pace: "balanced",
      accessibility_requirements: [],
      travel_mode: "driving",
      start_location_label: "Fixture Hotel",
      start_location_lat: 18.93,
      start_location_lng: 72.83,
    },
    participants: [
      { sequence: 1, age_years: 21, age_band: "18_24", gender: "female" },
      { sequence: 2, age_years: 22, age_band: "18_24", gender: "male" },
      { sequence: 3, age_years: 24, age_band: "18_24", gender: null },
      { sequence: 4, age_years: 26, age_band: "25_34", gender: "prefer_not_to_say" },
    ],
    route: fixtureRoute(),
    ...overrides,
  };
}
