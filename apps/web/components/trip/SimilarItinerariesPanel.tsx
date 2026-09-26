"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { describeSimilarExample, similarCountLabel } from "@/lib/trip/planningForm";
import type { SimilarItinerariesResponse } from "@/types/api";

/**
 * Shows the similarity answer BEFORE any itinerary is generated. Viewing
 * examples is optional; "Create personalized itinerary" is always
 * available — including when the count is 0 or the lookup failed.
 * Examples are anonymized summaries of plans their owners chose to share.
 */
export function SimilarItinerariesPanel({
  checking,
  result,
  lookupError,
  busy,
  loadingMore,
  onCreate,
  onLoadMore,
}: {
  checking: boolean;
  result: SimilarItinerariesResponse | null;
  lookupError: string | null;
  busy: boolean;
  loadingMore: boolean;
  onCreate: () => void;
  onLoadMore: () => void;
}) {
  const [showExamples, setShowExamples] = useState(false);

  if (checking) {
    return (
      <p className="flex items-center gap-2 rounded-xl bg-accent-soft px-3.5 py-3 text-sm text-ink" role="status" aria-live="polite">
        <Loader2 className="size-4 animate-spin text-accent" aria-hidden="true" />
        Finding similar trip plans…
      </p>
    );
  }

  const count = result?.similar_count ?? null;

  return (
    <div className="space-y-3 rounded-2xl border border-line bg-surface p-4" aria-live="polite">
      {lookupError ? (
        <p className="text-sm text-ink-muted" role="status">
          Couldn&apos;t check for similar plans ({lookupError}). You can still create your itinerary.
        </p>
      ) : count !== null ? (
        <p className="text-base font-semibold text-ink" role="status">
          {similarCountLabel(count)}
        </p>
      ) : null}

      {result && result.examples_total > 0 && result.examples_total < (count ?? 0) ? (
        <p className="text-xs text-ink-subtle">
          {result.examples_total} of these were shared by their planners and can be previewed.
        </p>
      ) : null}
      {result && count !== null && count > 0 && result.examples_total === 0 ? (
        <p className="text-xs text-ink-subtle">None of them were shared publicly, so there&apos;s nothing to preview.</p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {result && result.examples_total > 0 ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowExamples((v) => !v)}
            aria-expanded={showExamples}
            aria-controls="similar-plan-examples"
            disabled={busy}
          >
            {showExamples ? "Hide similar plans" : "View similar plans"}
          </Button>
        ) : null}
        <Button type="button" size="sm" onClick={onCreate} disabled={busy} loading={busy}>
          <Sparkles className="size-4" aria-hidden="true" />
          Create personalized itinerary
        </Button>
      </div>

      {showExamples && result ? (
        <div id="similar-plan-examples" className="space-y-2">
          <ul className="grid gap-2 sm:grid-cols-2">
            {result.examples.map((example) => {
              const view = describeSimilarExample(example);
              return (
                <li key={example.example_id} className="rounded-xl border border-line bg-surface-raised p-3 text-sm">
                  <p className="font-semibold text-ink">
                    {view.duration} · {view.destination}
                  </p>
                  <p className="text-ink-muted">{view.travelers}</p>
                  {view.themes ? <p className="text-ink-muted">{view.themes}</p> : null}
                  <p className="text-ink-muted">{view.pace}</p>
                  <p className="mt-1 text-xs text-ink-subtle">
                    {view.stops}
                    {view.distance ? ` · ${view.distance}` : ""}
                  </p>
                </li>
              );
            })}
          </ul>
          {result.has_more ? (
            <Button type="button" variant="ghost" size="sm" onClick={onLoadMore} loading={loadingMore} disabled={busy}>
              Show more
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
