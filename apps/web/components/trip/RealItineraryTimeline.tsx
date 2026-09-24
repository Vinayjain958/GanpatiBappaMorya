"use client";

import { Clock, MapPin, Wallet } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { BookingRequestButton } from "@/components/trip/BookingRequestButton";
import {
  formatCost,
  formatItemTimeRange,
  itinerarySummaryLine,
  itineraryStatusLabel,
  orderedItems,
  travelGapLabel,
} from "@/lib/itinerary/itineraryDisplay";
import type { ApiItinerary } from "@/types/api";

/**
 * Renders a backend-composed itinerary exactly as returned — never
 * reorders items, never recomputes feasibility/cost/travel time
 * client-side. This is the Phase 8 real-data counterpart to the Phase 1
 * mock-data ItineraryTimeline (components/trip/ItineraryTimeline.tsx),
 * which stays in place for the existing demo route.
 */
export function RealItineraryTimeline({ itinerary }: { itinerary: ApiItinerary }) {
  const items = orderedItems(itinerary);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">{itinerary.title}</h2>
          <p className="text-sm text-ink-muted">{itinerarySummaryLine(itinerary)}</p>
        </div>
        <Badge tone={itinerary.status === "CANCELLED" ? "danger" : "accent"}>
          {itineraryStatusLabel(itinerary.status)}
        </Badge>
      </div>

      {itinerary.narrative_summary ? (
        <p className="rounded-lg bg-surface-sunken px-3 py-2 text-sm text-ink-muted">
          {itinerary.narrative_summary}
        </p>
      ) : null}

      <ol className="space-y-3" aria-label={`Itinerary for ${itinerary.title}`}>
        {items.map((item) => {
          const gap = travelGapLabel(item);
          return (
            <li key={item.id}>
              {gap ? (
                <p className="ml-16 pb-1 text-xs text-ink-subtle" data-testid="travel-gap">
                  {gap}
                </p>
              ) : null}
              <div className="flex gap-4 rounded-xl border border-line bg-surface p-4">
                <div className="w-16 shrink-0 text-sm font-semibold text-ink">{formatItemTimeRange(item)}</div>
                <div className="flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-ink">{item.title ?? "Experience"}</p>
                      <p className="text-xs text-ink-subtle">{item.category_name}</p>
                    </div>
                    <BookingRequestButton itineraryId={itinerary.id} itineraryItemId={item.id} />
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="size-3.5" aria-hidden="true" />
                      {item.location_place_name ?? "Location unavailable"}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="size-3.5" aria-hidden="true" />
                      {item.duration_minutes} min
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Wallet className="size-3.5" aria-hidden="true" />
                      {formatCost(item.estimated_cost, itinerary.currency)}
                    </span>
                  </div>
                  {item.narrative_text ? (
                    <p className="text-xs text-ink-muted">{item.narrative_text}</p>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
