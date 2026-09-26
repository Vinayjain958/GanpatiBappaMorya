import { travelGapLabel } from "@/lib/itinerary/itineraryDisplay";
import type {
  ApiItinerary,
  ApiItineraryItem,
  ApiItineraryMapData,
  ApiRouteLeg,
} from "@/types/api";

/**
 * Pure adapters from the backend's persisted route snapshot
 * (ApiItinerary.route, ADR-056) to map-ready GeoJSON and display text.
 * No routing, no aggregation of totals (the backend computes those), no
 * straight-line fallbacks: a leg without backend geometry is simply not
 * drawn, and its text says so.
 */

export interface StopFeatureProperties {
  itemId: string;
  sequence: number;
  /** Visible marker text — the stop number, never a database id. */
  label: string;
  title: string;
  selected: boolean;
}

export interface RouteLegFeatureProperties {
  toItemId: string;
  toSequence: number;
  selected: boolean;
}

export type StopFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Point, StopFeatureProperties>;
export type RouteFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.LineString, RouteLegFeatureProperties>;

/** "all" or a 0-based day index. Itineraries are single-day in this phase,
 * so every stop/leg has day_index 0 and filtering is effectively identity;
 * kept so a future multi-day model only has to add days, not rewire UI. */
export type DayFilter = "all" | number;

export function filterRouteByDay(route: ApiItineraryMapData, day: DayFilter): ApiItineraryMapData {
  if (day === "all") return route;
  return {
    ...route,
    stops: route.stops.filter((s) => s.day_index === day),
    legs: route.legs.filter((l) => l.day_index === day),
  };
}

export function stopsToFeatureCollection(
  route: ApiItineraryMapData | null | undefined,
  selectedItemId: string | null = null,
): StopFeatureCollection {
  return {
    type: "FeatureCollection",
    features: (route?.stops ?? [])
      .filter((stop) => stop.lat != null && stop.lng != null)
      .map((stop) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [stop.lng as number, stop.lat as number] },
        properties: {
          itemId: stop.item_id,
          sequence: stop.sequence,
          label: String(stop.sequence),
          title: stop.title ?? `Stop ${stop.sequence}`,
          selected: stop.item_id === selectedItemId,
        },
      })),
  };
}

/** Only legs with real backend (OSRM) geometry become lines. */
export function legsToFeatureCollection(
  route: ApiItineraryMapData | null | undefined,
  selectedItemId: string | null = null,
): RouteFeatureCollection {
  return {
    type: "FeatureCollection",
    features: (route?.legs ?? [])
      .filter((leg): leg is ApiRouteLeg & { geometry: GeoJSON.LineString } =>
        leg.status === "ROUTED" && leg.geometry?.type === "LineString" && leg.geometry.coordinates.length >= 2,
      )
      .map((leg) => ({
        type: "Feature",
        geometry: leg.geometry,
        properties: {
          toItemId: leg.to_item_id,
          toSequence: leg.to_sequence,
          selected: leg.to_item_id === selectedItemId,
        },
      })),
  };
}

/** [[west, south], [east, north]] over stops, start and drawn geometry. */
export function routeBounds(
  route: ApiItineraryMapData | null | undefined,
): [[number, number], [number, number]] | null {
  if (!route) return null;
  const points: Array<[number, number]> = [];
  for (const stop of route.stops) {
    if (stop.lat != null && stop.lng != null) points.push([stop.lng, stop.lat]);
  }
  if (route.start_location) points.push([route.start_location.lng, route.start_location.lat]);
  for (const leg of route.legs) {
    if (leg.status === "ROUTED" && leg.geometry) {
      for (const [lng, lat] of leg.geometry.coordinates) points.push([lng, lat]);
    }
  }
  if (!points.length) return null;
  const lngs = points.map((p) => p[0]);
  const lats = points.map((p) => p[1]);
  return [
    [Math.min(...lngs), Math.min(...lats)],
    [Math.max(...lngs), Math.max(...lats)],
  ];
}

export function formatDistanceMeters(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

export function formatDurationSeconds(seconds: number): string {
  const minutes = Math.max(1, Math.round(seconds / 60));
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

const SOURCE_LABELS: Record<string, string> = {
  osrm: "OSRM road routing",
  haversine_estimate: "Straight-line estimate",
  mixed: "Mixed: OSRM + estimates",
};

export function routingSourceLabel(source: string | null | undefined): string | null {
  if (!source) return null;
  return SOURCE_LABELS[source] ?? source;
}

export type RouteSummaryState = "available" | "partial" | "unavailable" | "none";

export interface RouteSummaryDisplay {
  state: RouteSummaryState;
  headline: string | null;
  distance: string | null;
  duration: string | null;
  stops: number;
  days: number;
  source: string | null;
  isEstimate: boolean;
}

/** Formats the backend's own totals — never re-aggregates legs. */
export function routeSummaryDisplay(route: ApiItineraryMapData | null | undefined): RouteSummaryDisplay {
  if (!route) {
    return { state: "unavailable", headline: "Route unavailable", distance: null, duration: null, stops: 0, days: 1, source: null, isEstimate: false };
  }
  const { summary } = route;
  const base = {
    stops: summary.stop_count,
    days: summary.day_count,
    source: routingSourceLabel(summary.routing_source),
    isEstimate: summary.routing_source !== "osrm" && summary.routing_source != null,
  };
  if (summary.status === "NO_LEGS") {
    return { ...base, state: "none", headline: "No travel legs — add a starting point to route from it", distance: null, duration: null };
  }
  if (summary.status === "UNAVAILABLE" || summary.total_distance_meters == null || summary.total_duration_seconds == null) {
    return { ...base, state: "unavailable", headline: "Route unavailable", distance: null, duration: null };
  }
  return {
    ...base,
    state: summary.status === "PARTIAL" ? "partial" : "available",
    headline:
      summary.status === "PARTIAL"
        ? `Route unavailable for ${summary.unavailable_leg_count} of ${summary.leg_count} legs — totals cover the rest`
        : null,
    distance: formatDistanceMeters(summary.total_distance_meters),
    duration: formatDurationSeconds(summary.total_duration_seconds),
  };
}

export function legForItem(itinerary: ApiItinerary, itemId: string): ApiRouteLeg | null {
  return itinerary.route?.legs.find((leg) => leg.to_item_id === itemId) ?? null;
}

/**
 * "Travel from previous stop" text for a timeline item. Uses the
 * persisted route leg when the itinerary has a route snapshot; falls back
 * to the legacy travel-gap label only for itineraries created before route
 * snapshots existed. Travel duration here is never the experience duration.
 */
export function travelFromPreviousLabel(itinerary: ApiItinerary, item: ApiItineraryItem): string | null {
  if (!itinerary.route) return travelGapLabel(item);
  const leg = legForItem(itinerary, item.id);
  if (!leg) return null; // first stop with no starting point: no leg to describe
  const from = leg.from_sequence == null ? "from your starting point" : "from previous stop";
  if (leg.status === "UNAVAILABLE" || leg.distance_meters == null || leg.duration_seconds == null) {
    return `Travel ${from}: route unavailable`;
  }
  const text = `${formatDistanceMeters(leg.distance_meters)} · ${formatDurationSeconds(leg.duration_seconds)}`;
  return leg.status === "ESTIMATED" ? `Travel ${from}: ~${text} (estimate)` : `Travel ${from}: ${text}`;
}

/** Accessible marker/list label, e.g. "Stop 2: Chhatrapati Shivaji Maharaj Vastu Sangrahalaya". */
export function stopAccessibleLabel(sequence: number, title: string | null | undefined): string {
  return `Stop ${sequence}: ${title ?? "Unnamed stop"}`;
}
