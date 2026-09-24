import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="space-y-1.5">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</p>
        ) : null}
        <h2 className="text-xl font-semibold tracking-tight text-ink sm:text-2xl">{title}</h2>
        {description ? <p className="max-w-2xl text-sm text-ink-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
