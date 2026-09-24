"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { ApiError } from "@/lib/api/client";
import { composeItinerary } from "@/lib/api/itineraries";
import { isCompositionFailure } from "@/types/api";
import type { ApiItinerary, CompositionPace, CompositionValidationResponse } from "@/types/api";

const REASON_LABELS: Record<string, string> = {
  OPENING_HOURS_CONFLICT: "isn't open during your chosen time window",
  OPENING_HOURS_UNAVAILABLE: "has no recorded opening hours to verify",
  AVAILABILITY_CONFLICT: "has no bookable slot in your chosen time window",
  AVAILABILITY_UNAVAILABLE: "has no availability data on record",
  BUDGET_EXCEEDED: "costs more than your budget allows",
  PRICE_UNAVAILABLE: "has no listed price to verify against your budget",
  DURATION_EXCEEDED: "takes longer than your available time",
  TRAVEL_TIME_EXCEEDED: "is too far to reach in time",
  GROUP_SIZE_EXCEEDS_CAPACITY: "can't accommodate your group size",
  CAPACITY_UNAVAILABLE: "has no capacity data on record",
};

/** Builds a genuinely explanatory message from the real backend reason
 * codes rather than showing the generic "failed validation" string —
 * every claim here traces back to data actually in the response, never
 * guessed. */
function describeCompositionFailure(result: CompositionValidationResponse): string {
  if (result.candidate_count === 0) {
    return "No experiences matched your search. Try a broader interest or a different date.";
  }
  if (result.feasible_count === 0) {
    return `Found ${result.candidate_count} matching experiences, but none fit your constraints — try an earlier/later time window, a higher budget, or fewer experiences.`;
  }

  const reasonCounts = new Map<string, number>();
  for (const issue of result.issues) {
    const reasons = (issue.evidence.reasons as string[] | undefined) ?? [issue.code];
    for (const reason of reasons) {
      reasonCounts.set(reason, (reasonCounts.get(reason) ?? 0) + 1);
    }
  }
  const topReason = [...reasonCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  const explanation = topReason ? REASON_LABELS[topReason] : undefined;

  if (explanation) {
    return `Found ${result.feasible_count} matching experiences, but the best available option ${explanation}. Try a different time window or budget.`;
  }
  return `Found ${result.feasible_count} matching experiences, but couldn't fit them into a valid plan for the given constraints.`;
}

/**
 * Composer form: date / time window / budget / max experiences /
 * preferences -> calls the backend compose API. Never computes
 * feasibility, ordering, or timing locally — every field here is just a
 * request parameter; all decisions happen server-side
 * (src/services/compose_itinerary.py).
 */
export function ItineraryComposerForm({
  onComposed,
}: {
  onComposed: (itinerary: ApiItinerary) => void;
}) {
  const [query, setQuery] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("18:00");
  const [maxExperiences, setMaxExperiences] = useState(4);
  const [maxBudget, setMaxBudget] = useState("");
  const [pace, setPace] = useState<CompositionPace>("balanced");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!date) {
      setError("Please choose a date.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setValidationMessage(null);
    try {
      const result = await composeItinerary({
        query: query || undefined,
        itinerary_date: date,
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
        max_experiences: maxExperiences,
        max_budget: maxBudget ? Number(maxBudget) : undefined,
        pace,
      });
      if (isCompositionFailure(result)) {
        setValidationMessage(describeCompositionFailure(result));
        return;
      }
      onComposed(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardBody className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-ink">Create an itinerary</h2>
          <p className="text-sm text-ink-muted">
            LocaLens will compose a chronological, travel-aware plan from feasible experiences.
          </p>
        </div>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-ink">What are you interested in?</span>
            <input
              className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. food, heritage walks"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">Date</span>
              <input
                type="date"
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">Max experiences</span>
              <input
                type="number"
                min={1}
                max={20}
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={maxExperiences}
                onChange={(e) => setMaxExperiences(Number(e.target.value))}
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">Start time</span>
              <input
                type="time"
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">End time</span>
              <input
                type="time"
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">Max budget (INR)</span>
              <input
                type="number"
                min={0}
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={maxBudget}
                onChange={(e) => setMaxBudget(e.target.value)}
                placeholder="No limit"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-ink">Pace</span>
              <select
                className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                value={pace}
                onChange={(e) => setPace(e.target.value as CompositionPace)}
              >
                <option value="relaxed">Relaxed</option>
                <option value="balanced">Balanced</option>
                <option value="packed">Packed</option>
              </select>
            </label>
          </div>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          {validationMessage ? (
            <p className="rounded-lg bg-warning-soft px-3 py-2 text-sm text-warning">{validationMessage}</p>
          ) : null}
          <Button type="submit" loading={submitting} className="w-full">
            Compose itinerary
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
