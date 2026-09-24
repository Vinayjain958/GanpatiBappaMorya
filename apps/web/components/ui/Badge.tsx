import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

type Tone = "neutral" | "accent" | "success" | "warning" | "danger" | "highlight";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-sunken text-ink-muted",
  accent: "bg-accent-soft text-accent",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
  highlight: "bg-highlight-soft text-highlight",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium leading-none",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
