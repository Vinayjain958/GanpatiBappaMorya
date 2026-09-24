import { cn } from "@/lib/utils/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      role="presentation"
      aria-hidden="true"
      className={cn("animate-pulse rounded-md bg-surface-sunken", className)}
    />
  );
}
