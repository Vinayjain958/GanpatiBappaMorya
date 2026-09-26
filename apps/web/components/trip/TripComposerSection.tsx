"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { ItineraryComposerForm } from "@/components/trip/ItineraryComposerForm";
import { ItineraryDetailView } from "@/components/trip/ItineraryDetailView";
import { SavedItinerariesList } from "@/components/trip/SavedItinerariesList";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { getItinerary, listMyItineraries } from "@/lib/api/itineraries";
import { selectCurrentItinerary } from "@/lib/itinerary/itineraryDisplay";
import type { ApiItinerary } from "@/types/api";

type HydrationState =
  | { status: "loading" }
  | { status: "loaded-with-itinerary"; itinerary: ApiItinerary; saved: ApiItinerary[] }
  | { status: "loaded-without-itinerary"; saved: ApiItinerary[] }
  | { status: "error"; message: string };

/**
 * Client-side Trip Planner entry point for /trip. Auth is already
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
 * fetches the traveler's saved itineraries via GET /api/v1/itineraries,
 * then the current one's full detail (participants + persisted route
 * geometry) via GET /api/v1/itineraries/{id}, and only falls back to the
 * planner form once those fetches confirm there is nothing to show —
 * never before, and never on a fetch failure (an error is shown with a
 * retry action). These fetches are read-only: they never trigger a
 * compose call, so remounts/Strict-Mode double-effects can never create
 * a duplicate itinerary. Nothing here is kept in localStorage.
 */
export function TripComposerSection() {
  const [state, setState] = useState<HydrationState>({ status: "loading" });

  // Deliberately does NOT set "loading" itself — the initial useState
  // value covers the mount case and retry() sets it explicitly, keeping
  // synchronous setState calls out of the effect body.
  const fetchSaved = useCallback(async (signal?: AbortSignal): Promise<HydrationState | null> => {
    try {
      const { items } = await listMyItineraries(signal);
      const current = selectCurrentItinerary(items);
      if (!current) return { status: "loaded-without-itinerary", saved: items };
      const detail = await getItinerary(current.id, signal);
      return { status: "loaded-with-itinerary", itinerary: detail, saved: items };
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
    fetchSaved(controller.signal).then((next) => {
      if (next) setState(next);
    });
    return () => controller.abort();
  }, [fetchSaved]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    fetchSaved().then((next) => {
      if (next) setState(next);
    });
  }, [fetchSaved]);

  if (state.status === "loading") {
    return (
      <div className="space-y-3" aria-live="polite" aria-busy="true">
        <Skeleton className="h-8 w-48 rounded-xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
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

  const saved = state.saved;

  if (state.status === "loaded-with-itinerary") {
    return (
      <div className="space-y-6">
        <ItineraryDetailView key={state.itinerary.id} itinerary={state.itinerary} />
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="rounded-full text-accent hover:bg-accent-soft"
            onClick={() => setState({ status: "loaded-without-itinerary", saved })}
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            Plan another trip
          </Button>
          <Link
            href={`/trip/${state.itinerary.id}`}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium text-accent hover:bg-accent-soft"
          >
            Open this plan
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
        <SavedItinerariesList itineraries={saved} currentId={state.itinerary.id} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ItineraryComposerForm
        onComposed={(itinerary) =>
          setState({
            status: "loaded-with-itinerary",
            itinerary,
            saved: [itinerary, ...saved.filter((s) => s.id !== itinerary.id)],
          })
        }
      />
      <SavedItinerariesList itineraries={saved} currentId={null} />
    </div>
  );
}
