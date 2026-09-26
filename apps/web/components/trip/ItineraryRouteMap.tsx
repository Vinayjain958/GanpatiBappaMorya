"use client";

import { useMemo } from "react";
import { MapSurface } from "@/components/common/MapSurface";
import {
  filterRouteByDay,
  formatDistanceMeters,
  formatDurationSeconds,
  legsToFeatureCollection,
  routeBounds,
  routeSummaryDisplay,
  stopAccessibleLabel,
  stopsToFeatureCollection,
} from "@/lib/itinerary/itineraryMapData";
import { cn } from "@/lib/utils/cn";
import type { ApiItinerary } from "@/types/api";

/**
 * Renders an itinerary's persisted route snapshot on the shared
 * MapSurface. Pure presentation: every number shown here is a backend
 * value (totals included); legs without real backend geometry are never
 * drawn as lines. All route information is also available as text in
 * the summary card and the stop list below the map (the map is never the
 * only way to get it).
 */
export function ItineraryRouteMap({
  itinerary,
  selectedItemId,
  onSelectItem,
}: {
  itinerary: ApiItinerary;
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
}) {
  // Single-day itineraries: the only day is index 0, so "all" is exact.
  const route = useMemo(
    () => (itinerary.route ? filterRouteByDay(itinerary.route, "all") : null),
    [itinerary.route],
  );
  const summary = routeSummaryDisplay(route);
  const stops = useMemo(() => stopsToFeatureCollection(route, selectedItemId), [route, selectedItemId]);
  const legs = useMemo(() => legsToFeatureCollection(route, selectedItemId), [route, selectedItemId]);
  const bounds = useMemo(() => routeBounds(route), [route]);
  const selectedStop = route?.stops.find((s) => s.item_id === selectedItemId && s.lat != null && s.lng != null);
  const center = selectedStop ? { lat: selectedStop.lat as number, lng: selectedStop.lng as number } : undefined;
  const origin = route?.start_location
    ? { lat: route.start_location.lat, lng: route.start_location.lng }
    : null;

  return (
    <section aria-labelledby="route-map-heading" className="space-y-3">
      <div className="rounded-2xl border border-line bg-surface-raised p-4 shadow-soft">
        <h2 id="route-map-heading" className="text-sm font-semibold uppercase tracking-[0.14em] text-accent">
          Route
        </h2>
        {summary.state === "available" || summary.state === "partial" ? (
          <dl className="mt-3 grid grid-cols-3 gap-3 text-sm">
            <div>
              <dt className="text-xs text-ink-subtle">Total distance</dt>
              <dd className="font-semibold text-ink">{summary.distance}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-subtle">{summary.isEstimate ? "Est. travel time" : "Travel time"}</dt>
              <dd className="font-semibold text-ink">{summary.duration}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-subtle">Stops</dt>
              <dd className="font-semibold text-ink">{summary.stops}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-2 text-sm font-medium text-ink" role="status">
            {summary.headline}
          </p>
        )}
        {summary.state === "partial" && summary.headline ? (
          <p className="mt-2 text-xs text-warning" role="status">
            {summary.headline}
          </p>
        ) : null}
        {summary.source ? (
          <p className="mt-2 text-xs text-ink-subtle">
            Source: {summary.source}
            {summary.isEstimate ? " — straight-line estimates are not drawn as roads" : ""}
          </p>
        ) : null}
        {route?.start_location?.label ? (
          <p className="mt-1 text-xs text-ink-subtle">Starting point: {route.start_location.label}</p>
        ) : null}
      </div>

      <MapSurface
        className="h-80 sm:h-[420px]"
        label={`Route map for ${itinerary.title} with ${summary.stops} numbered stops`}
        stops={stops}
        routeLegs={legs}
        origin={origin}
        onSelectStop={onSelectItem}
        fitBounds={bounds}
        center={center}
      />

      {route && route.stops.length ? (
        <ol className="space-y-1.5" aria-label="Stops on the map">
          {route.stops.map((stop) => {
            const leg = route.legs.find((l) => l.to_item_id === stop.item_id);
            const selected = stop.item_id === selectedItemId;
            let legText: string | null = null;
            if (leg) {
              legText =
                leg.distance_meters != null && leg.duration_seconds != null && leg.status !== "UNAVAILABLE"
                  ? `${leg.status === "ESTIMATED" ? "~" : ""}${formatDistanceMeters(leg.distance_meters)} · ${formatDurationSeconds(leg.duration_seconds)}`
                  : "Route unavailable";
            }
            return (
              <li key={stop.item_id}>
                <button
                  type="button"
                  onClick={() => onSelectItem(stop.item_id)}
                  aria-pressed={selected}
                  aria-label={stopAccessibleLabel(stop.sequence, stop.title)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                    selected ? "border-highlight bg-highlight-soft" : "border-line bg-surface hover:bg-surface-sunken",
                  )}
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-ink">
                    {stop.sequence}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-ink">{stop.title ?? "Unnamed stop"}</span>
                  {legText ? <span className="shrink-0 text-xs text-ink-subtle">{legText}</span> : null}
                </button>
              </li>
            );
          })}
        </ol>
      ) : null}
    </section>
  );
}
