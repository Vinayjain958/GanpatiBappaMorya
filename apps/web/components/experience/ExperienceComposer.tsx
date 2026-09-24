import { ArrowDown, Clock, Sparkles, Wallet } from "lucide-react";
import type { Trip } from "@/types/trip";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DemoDataBadge } from "@/components/ui/DemoDataBadge";

/**
 * Presentation shell for the future AI Experience Composer (Phase 8).
 * Renders a structured, already-composed plan — never invented reasoning
 * text or a chat transcript. In Phase 1 it is fed mock trip data; later
 * phases wire it to the real composer output with the same shape.
 */
export function ExperienceComposer({ trip }: { trip: Trip }) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-line bg-surface-sunken/60 px-5 py-4">
        <div className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-ink">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-accent">Your experience</p>
            <p className="text-sm text-ink-muted">{trip.contextSummary}</p>
          </div>
        </div>
        <DemoDataBadge />
      </div>

      <CardBody className="space-y-1">
        {trip.items.map((item, index) => (
          <div key={item.id}>
            {index > 0 ? (
              <div className="flex items-center gap-2 py-1 pl-4 text-xs text-ink-subtle">
                <ArrowDown className="size-3.5" aria-hidden="true" />
                {item.travelMinutesFromPrevious} min travel
              </div>
            ) : null}
            <div className="flex items-start justify-between gap-3 rounded-lg border border-line p-3.5">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-ink-subtle">{item.time}</p>
                <p className="font-semibold text-ink">{item.title}</p>
                <p className="text-sm text-ink-muted">
                  {item.location} &middot; {item.provider}
                </p>
              </div>
              <Badge tone="neutral">{item.durationMinutes} min</Badge>
            </div>
          </div>
        ))}
      </CardBody>

      <div className="grid grid-cols-2 gap-3 border-t border-line bg-surface-sunken/50 px-5 py-4 text-sm sm:grid-cols-4">
        <div>
          <p className="flex items-center gap-1 text-xs text-ink-subtle">
            <Clock className="size-3.5" aria-hidden="true" />
            Total time
          </p>
          <p className="font-semibold text-ink">{Math.round(trip.totalTimeMinutes / 60)}h {trip.totalTimeMinutes % 60}m</p>
        </div>
        <div>
          <p className="text-xs text-ink-subtle">Travel time</p>
          <p className="font-semibold text-ink">{trip.totalTravelMinutes} min</p>
        </div>
        <div>
          <p className="flex items-center gap-1 text-xs text-ink-subtle">
            <Wallet className="size-3.5" aria-hidden="true" />
            Estimated cost
          </p>
          <p className="font-semibold text-ink">&#8377;{trip.totalCostInr}</p>
        </div>
        <div>
          <p className="text-xs text-ink-subtle">Preferences matched</p>
          <p className="font-semibold text-ink">{trip.preferencesMatched.length}</p>
        </div>
      </div>
    </Card>
  );
}
