import type { LucideIcon } from "lucide-react";
import { Card, CardBody } from "@/components/ui/Card";

export function SafetyResourceCard({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <Card>
      <CardBody className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <div>
          <p className="font-semibold text-ink">{title}</p>
          <p className="text-sm text-ink-muted">{description}</p>
        </div>
      </CardBody>
    </Card>
  );
}
