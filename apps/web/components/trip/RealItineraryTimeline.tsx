"use client";

import { Clock, Lock, MapPin, Radio, Wallet } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { BookingRequestButton } from "@/components/trip/BookingRequestButton";
import { useItineraryUpdates } from "@/hooks/useItineraryUpdates";
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
 *
 * Phase 9 adds a live-plan indicator, last-updated time, and revision
 * ("what changed") display driven by useItineraryUpdates — this
 * component never computes replanning/weather impact/reordering itself,
 * it only renders what the backend already decided and published.
 */
export function RealItineraryTimeline({ itinerary }: { itinerary: ApiItinerary }) {
  const items = orderedItems(itinerary);
  const updates = useItineraryUpdates(itinerary.id);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">{itinerary.title}</h2>
          <p className="text-sm text-ink-muted">{itinerarySummaryLine(itinerary)}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {updates.status === "connected" || updates.status === "replanning" ? (
            <Badge tone="accent">
              <Radio className="mr-1 inline size-3" aria-hidden="true" />
              Live plan
            </Badge>
          ) : null}
          <Badge tone={itinerary.status === "CANCELLED" ? "danger" : "accent"}>
            {itineraryStatusLabel(itinerary.status)}
          </Badge>
        </div>
      </div>

      {updates.replanInProgress ? (
        <p className="rounded-lg border border-line bg-surface-sunken px-3 py-2 text-sm text-ink-muted" role="status">
          Updating your itinerary based on changing conditions…
        </p>
      ) : null}

      {updates.requiresAction ? (
        <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900" role="alert">
          One of your locked items was affected by a change and needs your review — it was not changed automatically.
        </p>
      ) : null}

      {!updates.replanInProgress && updates.lastChangeSummary ? (
        <div className="rounded-lg border border-line bg-surface-sunken px-3 py-2 text-sm text-ink-muted">
          <p className="font-medium text-ink">Your itinerary was updated because conditions changed.</p>
          {(updates.lastChangeSummary.removed_items?.length ?? 0) > 0 ||
          (updates.lastChangeSummary.added_items?.length ?? 0) > 0 ? (
            <p className="mt-1 text-xs">
              {updates.lastChangeSummary.removed_items?.length
                ? `${updates.lastChangeSummary.removed_items.length} item(s) removed. `
                : ""}
              {updates.lastChangeSummary.added_items?.length
                ? `${updates.lastChangeSummary.added_items.length} item(s) added.`
                : ""}
            </p>
          ) : null}
        </div>
      ) : null}

      {updates.lastUpdatedAt ? (
        <p className="text-xs text-ink-subtle">Last updated {updates.lastUpdatedAt.toLocaleTimeString()}</p>
      ) : itinerary.context_last_updated_at ? (
        <p className="text-xs text-ink-subtle">
          Context last checked {new Date(itinerary.context_last_updated_at).toLocaleTimeString()}
        </p>
      ) : null}

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
                      <p className="flex items-center gap-1.5 font-semibold text-ink">
                        {item.title ?? "Experience"}
                        {item.is_locked ? (
                          <Lock className="size-3.5 text-ink-subtle" aria-label="Locked — will not be auto-replaced" />
                        ) : null}
                      </p>
                      <p className="text-xs text-ink-subtle">{item.category_name}</p>
                      {item.item_state === "AFFECTED" ? (
                        <p className="text-xs font-medium text-amber-700">Needs your review</p>
                      ) : null}
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
