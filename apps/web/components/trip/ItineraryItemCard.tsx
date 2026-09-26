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
        "flex gap-3 rounded-2xl border border-line bg-surface p-3.5 shadow-porcelain sm:gap-4 sm:p-4.5 transition-all duration-200 hover:shadow-porcelain-hover",
        item.status === "at_risk" && "border-danger/30 bg-danger-soft/20",
      )}
    >
      <div className="flex w-16 shrink-0 items-center justify-center self-start rounded-xl border border-pastel-lemon/80 bg-pastel-lemon/40 px-2 py-2.5 text-center text-xs font-semibold tabular-nums text-ink shadow-xs">
        {item.time}
      </div>

      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-semibold text-ink">{item.title}</p>
            <p className="text-xs text-ink-subtle">{item.category}</p>
          </div>
          <Badge tone={statusTone[item.status]}>
            {statusLabel[item.status]}
          </Badge>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-ink-muted">
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3.5 shrink-0 text-accent" aria-hidden="true" />
            {item.location} &middot; {item.provider}
          </span>

          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5 shrink-0" aria-hidden="true" />
            <span className="tabular-nums">{item.durationMinutes}</span> min
            {item.travelMinutesFromPrevious > 0
              ? ` (+${item.travelMinutesFromPrevious} min travel)`
              : ""}
          </span>

          <span className="inline-flex items-center gap-1">
            <Wallet className="size-3.5 shrink-0" aria-hidden="true" />
            <span className="font-medium tabular-nums text-ink">
              {item.costInr === 0 ? "Free" : `₹${item.costInr.toLocaleString("en-IN")}`}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}