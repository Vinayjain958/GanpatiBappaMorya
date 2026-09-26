import type { Trip } from "@/types/trip";
import { ItineraryItemCard } from "@/components/trip/ItineraryItemCard";
import { ReplanBanner } from "@/components/trip/ReplanBanner";

export function ItineraryTimeline({ trip }: { trip: Trip }) {
  return (
    <div className="space-y-4">
      <ReplanBanner />

      <ol
        className="relative space-y-4 before:absolute before:bottom-4 before:left-[1.125rem] before:top-4 before:w-px before:border-l before:border-dashed before:border-line-strong"
        aria-label={`Itinerary for ${trip.title}`}
      >
        {trip.items.map((item) => (
          <li key={item.id} className="relative pl-10">
            <span
              aria-hidden="true"
              className="absolute left-[0.65rem] top-5 z-10 size-3.5 rounded-full border-2 border-surface bg-pastel-mint shadow-xs ring-4 ring-pastel-mint/30"
            />
            <ItineraryItemCard item={item} />
          </li>
        ))}
      </ol>
    </div>
  );
}