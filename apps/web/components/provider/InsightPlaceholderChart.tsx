import type { LucideIcon } from "lucide-react";
import { BarChart3 } from "lucide-react";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";

export function InsightPlaceholderChart({
  title,
  description,
  icon: Icon = BarChart3,
}: {
  title: string;
  description: string;
  icon?: LucideIcon;
}) {
  return (
    <Card>
      <CardHeader>
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <p className="text-xs text-ink-subtle">{description}</p>
      </CardHeader>
      <CardBody>
        <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line-strong bg-surface-sunken/60 text-ink-subtle">
          <Icon className="size-6" aria-hidden="true" />
          <p className="text-xs">Not available yet</p>
        </div>
      </CardBody>
    </Card>
  );
}
