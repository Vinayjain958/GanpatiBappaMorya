import type { LucideIcon } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";
import type { SafetyResource } from "@/types/safety";
import { AlertCircle } from "lucide-react";

export function SafetyResourceCard({
  icon: Icon,
  resource
}: {
  icon: LucideIcon;
  resource: SafetyResource;
}) {
  return (
    <Card>
      <CardBody className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-ink truncate">{resource.name}</p>
          {resource.address && <p className="text-sm text-ink-muted truncate">{resource.address}</p>}
          {resource.phone && <p className="text-sm text-ink-muted truncate">{resource.phone}</p>}
          
          <div className="mt-2 flex items-center gap-2 text-xs">
            {resource.distance_km !== undefined && (
              <span className="text-accent font-medium">
                {resource.distance_km.toFixed(1)} km away
              </span>
            )}
            
            {resource.is_synthetic && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                <AlertCircle className="size-3" />
                Simulated Data
              </span>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
