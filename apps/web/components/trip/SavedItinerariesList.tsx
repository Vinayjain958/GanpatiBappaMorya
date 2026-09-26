import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { itineraryStatusLabel, itinerarySummaryLine } from "@/lib/itinerary/itineraryDisplay";
import { routeSummaryDisplay } from "@/lib/itinerary/itineraryMapData";
import type { ApiItinerary } from "@/types/api";

/** Every itinerary the traveler has saved (from GET /api/v1/itineraries),
 * each linking to its own persisted detail page. */
export function SavedItinerariesList({
  itineraries,
  currentId,
}: {
  itineraries: ApiItinerary[];
  currentId: string | null;
}) {
  if (!itineraries.length) return null;

  return (
    <section aria-labelledby="saved-trips-heading" className="space-y-3 border-t border-line pt-6">
      <h2 id="saved-trips-heading" className="text-lg font-semibold tracking-tight text-ink">
        Your saved itineraries
      </h2>
      <ul className="grid gap-3 sm:grid-cols-2">
        {itineraries.map((itinerary) => {
          const route = routeSummaryDisplay(itinerary.route);
          const date = new Date(`${itinerary.itinerary_date}T00:00:00`).toLocaleDateString(undefined, {
            weekday: "short",
            day: "numeric",
            month: "short",
            year: "numeric",
          });
          return (
            <li key={itinerary.id}>
              <Link
                href={`/trip/${itinerary.id}`}
                className="block rounded-2xl border border-line bg-surface-raised p-4 shadow-soft transition-shadow hover:shadow-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                aria-current={itinerary.id === currentId ? "page" : undefined}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-ink">{itinerary.title}</p>
                  <Badge tone={itinerary.status === "CANCELLED" ? "danger" : "accent"}>
                    {itineraryStatusLabel(itinerary.status)}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-ink-muted">
                  {date}
                  {itinerary.planning_profile?.destination_label ? ` · ${itinerary.planning_profile.destination_label}` : ""}
                </p>
                <p className="mt-1 text-xs text-ink-subtle">
                  {itinerarySummaryLine(itinerary)}
                  {route.distance ? ` · ${route.distance} travel` : ""}
                  {itinerary.planning_profile ? ` · ${itinerary.planning_profile.group_size} traveler${itinerary.planning_profile.group_size === 1 ? "" : "s"}` : ""}
                </p>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
