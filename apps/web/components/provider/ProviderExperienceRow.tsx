import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import type { ApiExperienceSummary } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const statusTone = {
  active: "success",
  draft: "neutral",
  inactive: "warning",
} as const;

export function ProviderExperienceRow({
  experience,
  onDeactivate,
}: {
  experience: ApiExperienceSummary;
  onDeactivate?: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-line bg-surface p-4">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate font-semibold text-ink">{experience.title}</p>
          <Badge tone={statusTone[experience.status as keyof typeof statusTone] ?? "neutral"} className="capitalize">
            {experience.status}
          </Badge>
        </div>
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-subtle">
          <span>
            {experience.price != null
              ? `₹${experience.price}`
              : experience.minimum_price != null
                ? `₹${experience.minimum_price}+`
                : "Price TBD"}
          </span>
          {experience.duration_minutes != null ? (
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3.5" aria-hidden="true" />
              {experience.duration_minutes} min
            </span>
          ) : null}
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3.5" aria-hidden="true" />
            {experience.location.locality ?? experience.location.city}
          </span>
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Link href={`/provider/experiences/${experience.id}`}>
          <Button variant="outline" size="sm">
            Manage
          </Button>
        </Link>
        {experience.status !== "inactive" && onDeactivate ? (
          <Button variant="ghost" size="sm" onClick={() => onDeactivate(experience.id)}>
            Deactivate
          </Button>
        ) : null}
      </div>
    </div>
  );
}
