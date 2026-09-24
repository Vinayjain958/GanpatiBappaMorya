import type { Trip } from "@/types/trip";
import { ItineraryItemCard } from "@/components/trip/ItineraryItemCard";
import { ReplanBanner } from "@/components/trip/ReplanBanner";

export function ItineraryTimeline({ trip }: { trip: Trip }) {
  return (
    <div className="space-y-4">
      <ReplanBanner />
      <ol className="space-y-3" aria-label={`Itinerary for ${trip.title}`}>
        {trip.items.map((item) => (
          <li key={item.id}>
            <ItineraryItemCard item={item} />
          </li>
        ))}
      </ol>
    </div>
  );
}
