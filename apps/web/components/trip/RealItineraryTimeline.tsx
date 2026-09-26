"use client";

import { Clock, Lock, MapPin, Radio, Wallet } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { BookingRequestButton } from "@/components/trip/BookingRequestButton";
import { useItineraryUpdates } from "@/hooks/useItineraryUpdates";
import type { ItineraryUpdatesState } from "@/hooks/useItineraryUpdates";
import {
  formatCost,
  formatItemTimeRange,
  itinerarySummaryLine,
  itineraryStatusLabel,
  orderedItems,
} from "@/lib/itinerary/itineraryDisplay";
import { stopAccessibleLabel, travelFromPreviousLabel } from "@/lib/itinerary/itineraryMapData";
import { cn } from "@/lib/utils/cn";
import type { ApiItinerary } from "@/types/api";

export function timelineItemDomId(itemId: string): string {
  return `itinerary-item-${itemId}`;
}

export function RealItineraryTimeline({
  itinerary,
  updates: sharedUpdates,
  selectedItemId = null,
  onSelectItem,
}: {
  itinerary: ApiItinerary;
  /** Pass the parent's SSE state to avoid opening a second stream. */
  updates?: ItineraryUpdatesState;
  selectedItemId?: string | null;
  /** When provided, each stop gets a keyboard-accessible "show on map" control. */
  onSelectItem?: (itemId: string) => void;
}) {
  const items = orderedItems(itinerary);
  // A null id makes the hook idle — only one SSE connection per itinerary.
  const ownUpdates = useItineraryUpdates(sharedUpdates ? null : itinerary.id);
  const updates = sharedUpdates ?? ownUpdates;

  return (
    <section className="space-y-5">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-soft">
        <div className="flex flex-col gap-4 border-b border-line bg-surface-raised p-5 sm:flex-row sm:items-start sm:justify-between sm:p-6">
          <div className="min-w-0">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent">
              Your schedule
            </p>
            <h2 className="text-xl font-semibold tracking-tight text-ink">{itinerary.title}</h2>
            <p className="mt-1 text-sm text-ink-muted">{itinerarySummaryLine(itinerary)}</p>
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

        <div className="space-y-4 p-4 sm:p-6">
          {updates.replanInProgress ? (
            <p
              className="rounded-2xl border border-accent/20 bg-accent-soft px-4 py-3 text-sm text-ink"
              role="status"
            >
              Updating your itinerary based on changing conditions…
            </p>
          ) : null}

          {updates.requiresAction ? (
            <p
              className="rounded-2xl border border-warning/30 bg-warning-soft px-4 py-3 text-sm text-warning"
              role="alert"
            >
              One of your locked items was affected by a change and needs your review — it was not changed
              automatically.
            </p>
          ) : null}

          {!updates.replanInProgress && updates.lastChangeSummary ? (
            <div className="rounded-2xl border border-line bg-surface-sunken px-4 py-3 text-sm text-ink-muted">
              <p className="font-medium text-ink">
                Your itinerary was updated because conditions changed.
              </p>
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
            <p className="text-xs text-ink-subtle">
              Last updated {updates.lastUpdatedAt.toLocaleTimeString()}
            </p>
          ) : itinerary.context_last_updated_at ? (
            <p className="text-xs text-ink-subtle">
              Context last checked{" "}
              {new Date(itinerary.context_last_updated_at).toLocaleTimeString()}
            </p>
          ) : null}

          {itinerary.narrative_summary ? (
            <p className="rounded-2xl bg-highlight-soft px-4 py-3 text-sm text-ink-muted">
              {itinerary.narrative_summary}
            </p>
          ) : null}

          <ol
            className="space-y-4"
            aria-label={`Itinerary for ${itinerary.title}`}
          >
            {items.map((item) => {
              const gap = travelFromPreviousLabel(itinerary, item);
              const selected = item.id === selectedItemId;

              return (
                <li key={item.id} id={timelineItemDomId(item.id)} className="scroll-mt-24">
                  {gap ? (
                    <p
                      className="mb-2 ml-[5.5rem] flex items-center gap-2 text-xs text-ink-subtle"
                      data-testid="travel-gap"
                    >
                      <span className="h-px w-5 bg-line-strong" aria-hidden="true" />
                      {gap}
                    </p>
                  ) : null}

                  <article
                    aria-current={selected ? "location" : undefined}
                    className={cn(
                      "grid grid-cols-[4.5rem_minmax(0,1fr)] gap-3 rounded-2xl border bg-surface p-3 transition-shadow sm:grid-cols-[5rem_minmax(0,1fr)] sm:gap-4 sm:p-4",
                      item.item_state === "AFFECTED" ? "border-warning/40" : "border-line",
                      selected && "border-highlight shadow-soft ring-2 ring-highlight/40",
                    )}
                  >
                    <div className="flex min-h-16 flex-col items-center justify-center gap-1.5 rounded-xl bg-highlight-soft px-2 py-3 text-center text-sm font-semibold leading-tight text-highlight">
                      {onSelectItem ? (
                        <button
                          type="button"
                          onClick={() => onSelectItem(item.id)}
                          aria-pressed={selected}
                          aria-label={`${stopAccessibleLabel(item.sequence_order, item.title)} — show on map`}
                          className="flex size-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                        >
                          {item.sequence_order}
                        </button>
                      ) : (
                        <Clock className="mb-1 size-4" aria-hidden="true" />
                      )}
                      {formatItemTimeRange(item)}
                    </div>

                    <div className="min-w-0 space-y-3">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <p className="flex flex-wrap items-center gap-1.5 font-semibold text-ink">
                            {item.title ?? "Experience"}
                            {item.is_locked ? (
                              <Lock
                                className="size-3.5 shrink-0 text-ink-subtle"
                                aria-label="Locked — will not be auto-replaced"
                              />
                            ) : null}
                          </p>

                          <p className="mt-1 text-xs text-ink-subtle">{item.category_name}</p>

                          {item.item_state === "AFFECTED" ? (
                            <p className="mt-1 text-xs font-medium text-warning">
                              Needs your review
                            </p>
                          ) : null}
                        </div>

                        <div className="shrink-0">
                          <BookingRequestButton
                            itineraryId={itinerary.id}
                            itineraryItemId={item.id}
                          />
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-ink-muted">
                        <span className="inline-flex items-center gap-1.5">
                          <MapPin className="size-3.5 shrink-0 text-accent" aria-hidden="true" />
                          {item.location_place_name ?? "Location unavailable"}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <Clock className="size-3.5 shrink-0 text-accent" aria-hidden="true" />
                          {/* Experience duration — distinct from the travel time above. */}
                          {item.duration_minutes} min visit
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                          <Wallet className="size-3.5 shrink-0 text-accent" aria-hidden="true" />
                          {formatCost(item.estimated_cost, itinerary.currency)}
                        </span>
                      </div>

                      {item.narrative_text ? (
                        <p className="text-xs leading-relaxed text-ink-muted">
                          {item.narrative_text}
                        </p>
                      ) : null}
                    </div>
                  </article>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}