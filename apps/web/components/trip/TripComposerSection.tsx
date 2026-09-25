"use client";

import { useCallback, useEffect, useState } from "react";
import { ItineraryComposerForm } from "@/components/trip/ItineraryComposerForm";
import { RealItineraryTimeline } from "@/components/trip/RealItineraryTimeline";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { listMyItineraries } from "@/lib/api/itineraries";
import { selectCurrentItinerary } from "@/lib/itinerary/itineraryDisplay";
import type { ApiItinerary } from "@/types/api";

type HydrationState =
  | { status: "loading" }
  | { status: "loaded-with-itinerary"; itinerary: ApiItinerary }
  | { status: "loaded-without-itinerary" }
  | { status: "error"; message: string };

/**
 * Client-side composer entry point for the trips page. Auth is already
 * enforced by the parent RequireRole wrapper — an anonymous visitor never
 * reaches this component, and RequireRole only renders children once its
 * own auth check has resolved (no fetch is ever attempted while auth is
 * still loading).
 *
 * The backend database is the source of truth for whether a traveler has
 * an existing itinerary — this component never assumes "no itinerary"
 * just because local state is empty (that was the root cause of the
 * itinerary-disappears-on-refresh bug: a bare `useState(null)` was
 * treated as "nothing exists" on every remount, even though the itinerary
 * was actually sitting in the database the whole time). On mount, it
 * fetches the traveler's saved itineraries via GET /api/v1/itineraries
 * and only falls back to the composer form once that fetch has actually
 * completed and confirmed there is nothing to show — never before, and
 * never on a fetch failure (an error is shown with a retry action, not
 * silently treated as "no trip yet"). This fetch is read-only: it never
 * triggers a compose call itself, so remounts/Strict-Mode double-effects
 * can never create a duplicate itinerary.
 */
export function TripComposerSection() {
  const [state, setState] = useState<HydrationState>({ status: "loading" });

  // Fetches the traveler's saved itineraries and resolves the next state.
  // Deliberately does NOT set "loading" itself — the initial useState
  // value already covers the mount case, and the explicit retry handler
  // below sets "loading" itself before calling this, satisfying the
  // lint rule against synchronous setState calls inside an effect body.
  const fetchSavedItinerary = useCallback(async (signal?: AbortSignal): Promise<HydrationState | null> => {
    try {
      const { items } = await listMyItineraries(signal);
      const current = selectCurrentItinerary(items);
      return current
        ? { status: "loaded-with-itinerary", itinerary: current }
        : { status: "loaded-without-itinerary" };
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return null;
      return {
        status: "error",
        message: err instanceof ApiError ? err.message : "Couldn't load your trip. Please try again.",
      };
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchSavedItinerary(controller.signal).then((next) => {
      if (next) setState(next);
    });
    return () => controller.abort();
  }, [fetchSavedItinerary]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    fetchSavedItinerary().then((next) => {
      if (next) setState(next);
    });
  }, [fetchSavedItinerary]);

  if (state.status === "loading") {
    return (
      <div className="space-y-3" aria-live="polite" aria-busy="true">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <ErrorState
        title="Couldn't load your trip"
        description={state.message}
        onRetry={retry}
      />
    );
  }

  if (state.status === "loaded-with-itinerary") {
    return (
      <div className="space-y-3">
        <RealItineraryTimeline itinerary={state.itinerary} />
        <button
          type="button"
          className="text-sm font-medium text-accent"
          onClick={() => setState({ status: "loaded-without-itinerary" })}
        >
          &larr; Compose another itinerary
        </button>
      </div>
    );
  }

  return (
    <ItineraryComposerForm
      onComposed={(itinerary) => setState({ status: "loaded-with-itinerary", itinerary })}
    />
  );
}
