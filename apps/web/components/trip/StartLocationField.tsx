"use client";

import { useEffect, useRef, useState } from "react";
import { Crosshair, MapPin, Search, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useLocationSearch } from "@/hooks/useLocationSearch";
import { useUserLocation } from "@/hooks/useUserLocation";
import { reverseGeocode } from "@/lib/api/location";
import type { StartLocationValue } from "@/lib/trip/planningForm";

/**
 * Starting point for the route's first leg. Primary path: search a hotel
 * or place through the backend geocoder (Nominatim adapter — explicit
 * submit only, no type-ahead). Secondary path: "Use current location",
 * which requests browser geolocation ONLY on that click (never on load),
 * then labels the fix through the backend reverse geocoder. Coordinates
 * are only ever sent to our own API.
 */
export function StartLocationField({
  value,
  onChange,
  disabled,
  controlClassName,
}: {
  value: StartLocationValue | null;
  onChange: (value: StartLocationValue | null) => void;
  disabled: boolean;
  controlClassName: string;
}) {
  const [query, setQuery] = useState("");
  const { status: searchStatus, results, search, clear } = useLocationSearch();
  const { status: geoStatus, coordinate, error: geoError, request } = useUserLocation();
  const handledCoordinate = useRef<{ lat: number; lng: number } | null>(null);

  // Label a freshly obtained browser fix via the backend reverse geocoder.
  useEffect(() => {
    if (!coordinate || handledCoordinate.current === coordinate) return;
    handledCoordinate.current = coordinate;
    const controller = new AbortController();
    reverseGeocode(coordinate, controller.signal)
      .then((response) => response.items[0]?.display_name ?? "Current location")
      .catch(() => "Current location")
      .then((label) => {
        if (!controller.signal.aborted) onChange({ ...coordinate, label, source: "browser" });
      });
    return () => controller.abort();
  }, [coordinate, onChange]);

  function runSearch() {
    if (query.trim()) void search(query);
  }

  if (value) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2.5 text-sm">
        <MapPin className="size-4 shrink-0 text-accent" aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate text-ink" title={value.label}>
          {value.label}
        </span>
        <button
          type="button"
          onClick={() => onChange(null)}
          disabled={disabled}
          className="rounded-full p-1 text-ink-subtle hover:bg-surface-sunken"
          aria-label="Clear starting point"
        >
          <X className="size-4" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          className={controlClassName}
          value={query}
          disabled={disabled}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault(); // don't submit the whole trip form
              runSearch();
            }
          }}
          placeholder="Search for hotel / location"
          aria-label="Search for a starting point"
        />
        <Button type="button" variant="outline" size="sm" className="h-auto shrink-0" onClick={runSearch} disabled={disabled} loading={searchStatus === "loading"}>
          <Search className="size-4" aria-hidden="true" />
          <span className="sr-only sm:not-sr-only">Search</span>
        </Button>
      </div>

      {searchStatus === "success" && results.length === 0 ? (
        <p className="text-xs text-ink-subtle">No places found — try a different name.</p>
      ) : null}
      {searchStatus === "error" ? (
        <p className="text-xs text-danger">Location search is unavailable right now.</p>
      ) : null}
      {results.length ? (
        <ul className="max-h-48 space-y-1 overflow-y-auto rounded-xl border border-line bg-surface p-1" aria-label="Starting point results">
          {results.slice(0, 5).map((result) => (
            <li key={`${result.lat},${result.lng},${result.display_name}`}>
              <button
                type="button"
                className="w-full rounded-lg px-2.5 py-2 text-left text-xs text-ink hover:bg-surface-sunken"
                onClick={() => {
                  onChange({ lat: result.lat, lng: result.lng, label: result.display_name, source: "search" });
                  clear();
                  setQuery("");
                }}
              >
                {result.display_name}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      <button
        type="button"
        onClick={request}
        disabled={disabled || geoStatus === "loading"}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-accent hover:underline disabled:opacity-60"
      >
        <Crosshair className="size-3.5" aria-hidden="true" />
        {geoStatus === "loading" ? "Getting your location…" : "Use current location"}
      </button>
      {geoStatus === "denied" ? (
        <p className="text-xs text-warning">Location permission was denied — search for your starting point instead.</p>
      ) : null}
      {geoStatus === "error" ? (
        <p className="text-xs text-warning">
          Couldn&apos;t get your location{geoError ? ` (${geoError})` : ""} — search for your starting point instead.
        </p>
      ) : null}
    </div>
  );
}
