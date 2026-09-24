import { Clock, MapPin, Wallet } from "lucide-react";
import type { ItineraryItem } from "@/types/trip";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils/cn";

const statusTone = {
  confirmed: "success",
  pending: "warning",
  at_risk: "danger",
} as const;

const statusLabel = {
  confirmed: "Confirmed",
  pending: "Pending",
  at_risk: "At risk",
} as const;

export function ItineraryItemCard({ item }: { item: ItineraryItem }) {
  return (
    <div
      className={cn(
        "flex gap-4 rounded-xl border border-line bg-surface p-4",
        item.status === "at_risk" && "border-danger/40",
      )}
    >
      <div className="w-16 shrink-0 text-sm font-semibold text-ink">{item.time}</div>
      <div className="flex-1 space-y-1.5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="font-semibold text-ink">{item.title}</p>
            <p className="text-xs text-ink-subtle">{item.category}</p>
          </div>
          <Badge tone={statusTone[item.status]}>{statusLabel[item.status]}</Badge>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3.5" aria-hidden="true" />
            {item.location} &middot; {item.provider}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" aria-hidden="true" />
            {item.durationMinutes} min
            {item.travelMinutesFromPrevious > 0 ? ` (+${item.travelMinutesFromPrevious} min travel)` : ""}
          </span>
          <span className="inline-flex items-center gap-1">
            <Wallet className="size-3.5" aria-hidden="true" />
            {item.costInr === 0 ? "Free" : `₹${item.costInr}`}
          </span>
        </div>
      </div>
    </div>
  );
}
