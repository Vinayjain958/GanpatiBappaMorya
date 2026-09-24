"use client";

import { useHealthCheck } from "@/hooks/useHealthCheck";
import { cn } from "@/lib/utils/cn";

/** Small, honest indicator of backend reachability — not a feature, a dev signal. */
export function ApiStatusBadge() {
  const { status, data } = useHealthCheck();

  const label =
    status === "success"
      ? `API connected · v${data?.version ?? ""}`
      : status === "error"
        ? "API unreachable"
        : "Checking API…";

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink-subtle">
      <span
        aria-hidden="true"
        className={cn(
          "size-1.5 rounded-full",
          status === "success" && "bg-success",
          status === "error" && "bg-danger",
          (status === "idle" || status === "loading") && "bg-ink-subtle",
        )}
      />
      {label}
    </span>
  );
}
