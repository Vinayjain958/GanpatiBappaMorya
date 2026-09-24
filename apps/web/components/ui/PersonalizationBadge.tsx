import { Sparkles } from "lucide-react";
import { Badge } from "./Badge";
import { cn } from "@/lib/utils/cn";

export interface PersonalizationBadgeProps {
  signals?: string[];
  className?: string;
}

export function PersonalizationBadge({ signals = [], className }: PersonalizationBadgeProps) {
  if (!signals || signals.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {signals.map((signal) => (
        <Badge key={signal} tone="accent" className="gap-1 px-1.5 py-0.5 text-[10px] sm:text-xs">
          <Sparkles className="size-3" />
          {signal}
        </Badge>
      ))}
    </div>
  );
}
