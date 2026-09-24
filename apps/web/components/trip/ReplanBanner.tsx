"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

/**
 * UI-only affordance for the future Dynamic Replanning Engine (Phase 9).
 * Clicking it does not recompute anything yet.
 */
export function ReplanBanner() {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-accent/25 bg-accent-soft px-4 py-3">
      <p className="text-sm text-ink">
        <span className="font-medium">Plan changed?</span> Update your time, budget, or preferences and
        we&apos;ll re-check the plan.
      </p>
      <Button
        variant="outline"
        size="sm"
        disabled
        title="Dynamic replanning arrives in a later phase"
      >
        <RefreshCw className="size-4" aria-hidden="true" />
        Replan
      </Button>
    </div>
  );
}
