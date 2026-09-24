import { FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

/** Visible marker for any mock/demo content rendered in the UI. */
export function DemoDataBadge({ label = "Demo data" }: { label?: string }) {
  return (
    <Badge tone="highlight" className="uppercase tracking-wide">
      <FlaskConical className="size-3" aria-hidden="true" />
      {label}
    </Badge>
  );
}
