"use client";

import { useCallback, useEffect, useState } from "react";
import { Users } from "lucide-react";
import { ItineraryRouteMap } from "@/components/trip/ItineraryRouteMap";
import { RealItineraryTimeline, timelineItemDomId } from "@/components/trip/RealItineraryTimeline";
import { useItineraryUpdates } from "@/hooks/useItineraryUpdates";
import { getItinerary } from "@/lib/api/itineraries";
import type { ApiItinerary } from "@/types/api";

const AGE_BAND_LABELS: Record<string, string> = {
  "0_5": "0–5",
  "6_12": "6–12",
  "13_17": "13–17",
  "18_24": "18–24",
  "25_34": "25–34",
  "35_49": "35–49",
  "50_64": "50–64",
  "65_PLUS": "65+",
};

function groupSummary(itinerary: ApiItinerary): string | null {
  const profile = itinerary.planning_profile;
  if (!profile) return null;
  const travelers = `${profile.group_size} ${profile.group_size === 1 ? "traveler" : "travelers"}`;
  const bands = Object.entries(profile.age_band_distribution)
    .map(([band, count]) => `${AGE_BAND_LABELS[band] ?? band} ×${count}`)
    .join(", ");
  return bands ? `${travelers} · ages ${bands}` : travelers;
}

/**
 * Timeline | map for one saved itinerary. Selection is plain React state
 * shared by both panes (click a timeline stop -> map centers/highlights;
 * click a map stop -> timeline scrolls to and highlights it). Opens ONE
 * SSE stream and, when the backend reports a completed replan, re-reads
 * the persisted itinerary so timeline, map and route totals all update
 * together from the same server response.
 */
export function ItineraryDetailView({ itinerary: initial }: { itinerary: ApiItinerary }) {
  const [itinerary, setItinerary] = useState(initial);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const updates = useItineraryUpdates(initial.id);
  const lastEvent = updates.lastEvent;

  useEffect(() => {
    if (lastEvent?.type !== "replan_completed") return;
    const controller = new AbortController();
    getItinerary(initial.id, controller.signal)
      .then((fresh) => setItinerary(fresh))
      .catch(() => {
        /* keep showing the last good snapshot; the banner already reported the change */
      });
    return () => controller.abort();
  }, [lastEvent, initial.id]);

  const selectFromTimeline = useCallback((itemId: string) => {
    setSelectedItemId(itemId);
  }, []);

  const selectFromMap = useCallback((itemId: string) => {
    setSelectedItemId(itemId);
    const element = document.getElementById(timelineItemDomId(itemId));
    if (element) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      element.scrollIntoView({ block: "nearest", behavior: reduced ? "auto" : "smooth" });
    }
  }, []);

  const group = groupSummary(itinerary);

  return (
    <div className="space-y-4">
      {group ? (
        <p className="inline-flex items-center gap-2 rounded-full bg-pastel-sky/40 px-3 py-1.5 text-xs text-ink-muted">
          <Users className="size-3.5 text-accent" aria-hidden="true" />
          {group}
        </p>
      ) : null}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,460px)] xl:items-start xl:gap-6">
        <div className="min-w-0">
          <RealItineraryTimeline
            itinerary={itinerary}
            updates={updates}
            selectedItemId={selectedItemId}
            onSelectItem={selectFromTimeline}
          />
        </div>
        <aside className="min-w-0 xl:sticky xl:top-6">
          <ItineraryRouteMap
            itinerary={itinerary}
            selectedItemId={selectedItemId}
            onSelectItem={selectFromMap}
          />
        </aside>
      </div>
    </div>
  );
}
