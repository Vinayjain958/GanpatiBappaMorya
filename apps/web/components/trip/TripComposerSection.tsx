"use client";

import { useState } from "react";
import { ItineraryComposerForm } from "@/components/trip/ItineraryComposerForm";
import { RealItineraryTimeline } from "@/components/trip/RealItineraryTimeline";
import type { ApiItinerary } from "@/types/api";

/**
 * Client-side composer entry point for the trips page. Auth is already
 * enforced by the parent RequireRole wrapper — an anonymous visitor never
 * reaches this component, and no compose API call is attempted before
 * that check passes.
 */
export function TripComposerSection() {
  const [composed, setComposed] = useState<ApiItinerary | null>(null);

  if (composed) {
    return (
      <div className="space-y-3">
        <RealItineraryTimeline itinerary={composed} />
        <button
          type="button"
          className="text-sm font-medium text-accent"
          onClick={() => setComposed(null)}
        >
          &larr; Compose another itinerary
        </button>
      </div>
    );
  }

  return <ItineraryComposerForm onComposed={setComposed} />;
}
