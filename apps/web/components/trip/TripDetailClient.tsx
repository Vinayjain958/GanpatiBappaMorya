"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, MapPinned } from "lucide-react";
import { ItineraryDetailView } from "@/components/trip/ItineraryDetailView";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError } from "@/lib/api/client";
import { getItinerary } from "@/lib/api/itineraries";
import type { ApiItinerary } from "@/types/api";

type DetailState =
  | { status: "loading" }
  | { status: "loaded"; itinerary: ApiItinerary }
  | { status: "not-found" }
  | { status: "error"; message: string };

/** Loads one saved itinerary from the API on every mount — a browser
 * refresh or a new login re-reads the same persisted data (including the
 * route snapshot), never React memory or browser storage. */
export function TripDetailClient({ itineraryId }: { itineraryId: string }) {
  const [state, setState] = useState<DetailState>({ status: "loading" });

  const load = useCallback(
    async (signal?: AbortSignal): Promise<DetailState | null> => {
      try {
        return { status: "loaded", itinerary: await getItinerary(itineraryId, signal) };
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return null;
        if (err instanceof ApiError && err.status === 404) return { status: "not-found" };
        return {
          status: "error",
          message: err instanceof ApiError ? err.message : "Couldn't load this trip. Please try again.",
        };
      }
    },
    [itineraryId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then((next) => {
      if (next) setState(next);
    });
    return () => controller.abort();
  }, [load]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    load().then((next) => {
      if (next) setState(next);
    });
  }, [load]);

  const back = (
    <Link href="/trip" className="inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline">
      <ArrowLeft className="size-4" aria-hidden="true" />
      All trips
    </Link>
  );

  if (state.status === "loading") {
    return (
      <div className="space-y-4" aria-busy="true" aria-live="polite">
        <span className="sr-only">Loading your trip…</span>
        <Skeleton className="h-24 w-full rounded-2xl" />
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,460px)]">
          <Skeleton className="h-96 w-full rounded-2xl" />
          <Skeleton className="h-96 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (state.status === "not-found") {
    return (
      <div className="space-y-4">
        {back}
        <EmptyState
          icon={MapPinned}
          title="Trip not found"
          description="This itinerary doesn't exist or isn't yours."
          action={
            <Link href="/trip">
              <Button size="sm" className="rounded-full">Back to your trips</Button>
            </Link>
          }
        />
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="space-y-4">
        {back}
        <ErrorState title="Couldn't load this trip" description={state.message} onRetry={retry} />
      </div>
    );
  }

  const { itinerary } = state;
  const date = new Date(`${itinerary.itinerary_date}T00:00:00`).toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      {back}
      <header className="rounded-2xl border border-line bg-pastel-lavender/45 p-5 shadow-soft sm:p-6">
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{itinerary.title}</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {date}
          {itinerary.planning_profile?.destination_label ? ` · ${itinerary.planning_profile.destination_label}` : ""}
          {` · ${itinerary.start_time.slice(0, 5)}–${itinerary.end_time.slice(0, 5)}`}
        </p>
      </header>
      <ItineraryDetailView key={itinerary.id} itinerary={itinerary} />
    </div>
  );
}
