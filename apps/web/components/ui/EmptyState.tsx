import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line-strong bg-surface-sunken/50 px-6 py-14 text-center",
        className,
      )}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-surface text-ink-subtle">
        <Icon className="size-6" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-ink">{title}</p>
        {description ? <p className="max-w-sm text-sm text-ink-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
