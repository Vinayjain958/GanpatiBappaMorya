"use client";

import { useReducer, useRef, useState } from "react";
import { CheckCircle2, Circle, Loader2, Users } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { ParticipantFields } from "@/components/trip/ParticipantFields";
import { SimilarItinerariesPanel } from "@/components/trip/SimilarItinerariesPanel";
import { StartLocationField } from "@/components/trip/StartLocationField";
import { ApiError } from "@/lib/api/client";
import { composeItinerary, findSimilarItineraries, getItinerary } from "@/lib/api/itineraries";
import {
  MAX_PARTICIPANTS,
  buildComposeRequest,
  buildSimilarRequest,
  hasErrors,
  initialPlannerState,
  initialPlanningValues,
  isPlannerBusy,
  parseGroupSize,
  plannerReducer,
  plannerSteps,
  resizeParticipants,
  validatePlanningForm,
} from "@/lib/trip/planningForm";
import type { PlanningFormErrors, PlanningFormValues, StartLocationValue } from "@/lib/trip/planningForm";
import { isCompositionFailure } from "@/types/api";
import type {
  ApiItinerary,
  CompositionPace,
  CompositionValidationResponse,
  SimilarItinerariesResponse,
} from "@/types/api";

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
  CAPACITY_UNAVAILABLE: "has no capacity data on record to confirm your group fits",
};

/**
 * Builds a message from backend reason codes and response data.
 */
function describeCompositionFailure(
  result: CompositionValidationResponse,
): string {
  if (result.candidate_count === 0) {
    return "No experiences matched your search. Try a broader interest or a different date.";
  }

  if (result.feasible_count === 0) {
    return `Found ${result.candidate_count} matching experiences, but none fit your constraints — try an earlier/later time window, a higher budget, a smaller group, or fewer experiences.`;
  }

  const reasonCounts = new Map<string, number>();
  for (const issue of result.issues) {
    const reasons = (issue.evidence.reasons as string[] | undefined) ?? [
      issue.code,
    ];
    for (const reason of reasons) {
      reasonCounts.set(reason, (reasonCounts.get(reason) ?? 0) + 1);
    }
  }

  const topReason = [...reasonCounts.entries()].sort(
    (a, b) => b[1] - a[1],
  )[0]?.[0];
  const explanation = topReason ? REASON_LABELS[topReason] : undefined;

  if (explanation) {
    return `Found ${result.feasible_count} matching experiences, but the best available option ${explanation}. Try a different time window or budget.`;
  }

  return `Found ${result.feasible_count} matching experiences, but couldn't fit them into a valid plan for the given constraints.`;
}

const EMPTY_ERRORS: PlanningFormErrors = { fields: {}, participants: {} };

/**
 * The single Trip Planner form. Collects the trip + group context, first
 * asks the backend how many similar itineraries already exist (read-only,
 * nothing is saved), and only runs the real compose pipeline when the
 * traveler explicitly clicks "Create personalized itinerary". Feasibility,
 * ordering, timing and routing all stay server-side; this component only
 * renders state from lib/trip/planningForm.ts.
 */
export function ItineraryComposerForm({
  onComposed,
}: {
  onComposed: (itinerary: ApiItinerary) => void;
}) {
  const [values, setValues] = useState<PlanningFormValues>(initialPlanningValues);
  const [errors, setErrors] = useState<PlanningFormErrors>(EMPTY_ERRORS);
  const [planner, dispatch] = useReducer(plannerReducer, initialPlannerState);
  const [similar, setSimilar] = useState<SimilarItinerariesResponse | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  // Guards against a double click landing before React re-renders the
  // disabled button (the reducer also ignores duplicate submits).
  const inFlight = useRef(false);

  const busy = isPlannerBusy(planner.phase);
  const showResults =
    planner.phase === "CHECKING_SIMILAR" ||
    planner.phase === "SIMILAR_RESULTS" ||
    planner.phase === "GENERATING" ||
    planner.phase === "ROUTING" ||
    (planner.phase === "ERROR" && (similar !== null || planner.similarError !== null));

  function update(patch: Partial<PlanningFormValues>, group = false) {
    setValues((prev) => ({ ...prev, ...patch }));
    setSimilar(null);
    dispatch({ type: group ? "EDIT_GROUP" : "EDIT_FIELD" });
  }

  function handleGroupSize(raw: string) {
    const size = parseGroupSize(raw);
    setValues((prev) => ({
      ...prev,
      groupSize: raw,
      // Only resize on a valid number: 5 -> 3 keeps the first three rows.
      participants: size === null ? prev.participants : resizeParticipants(prev.participants, size),
    }));
    setSimilar(null);
    dispatch({ type: "EDIT_GROUP" });
  }

  function handleParticipantChange(sequence: number, patch: { age?: string; gender?: PlanningFormValues["participants"][number]["gender"] }) {
    setValues((prev) => ({
      ...prev,
      participants: prev.participants.map((p) => (p.sequence === sequence ? { ...p, ...patch } : p)),
    }));
    setSimilar(null);
    dispatch({ type: "EDIT_GROUP" });
  }

  async function handleFindSimilar(event: React.FormEvent) {
    event.preventDefault();
    if (inFlight.current || busy) return;
    dispatch({ type: "SUBMIT" });

    const found = validatePlanningForm(values);
    setErrors(found);
    if (hasErrors(found)) {
      dispatch({
        type: "VALIDATION_FAILED",
        groupRelated: Boolean(found.fields.groupSize) || Object.keys(found.participants).length > 0,
      });
      return;
    }

    inFlight.current = true;
    dispatch({ type: "SIMILAR_STARTED" });
    try {
      const response = await findSimilarItineraries(buildSimilarRequest(values));
      setSimilar(response);
      dispatch({ type: "SIMILAR_LOADED", count: response.similar_count });
    } catch (err) {
      setSimilar(null);
      dispatch({
        type: "SIMILAR_FAILED",
        message: err instanceof ApiError ? err.message : "lookup failed",
      });
    } finally {
      inFlight.current = false;
    }
  }

  async function handleLoadMore() {
    if (!similar || loadingMore) return;
    setLoadingMore(true);
    try {
      const next = await findSimilarItineraries(
        buildSimilarRequest(values, { limit: similar.limit, offset: similar.examples.length }),
      );
      setSimilar({ ...next, examples: [...similar.examples, ...next.examples] });
    } catch {
      /* keep what is already shown */
    } finally {
      setLoadingMore(false);
    }
  }

  async function handleCreate() {
    if (inFlight.current || busy) return;
    inFlight.current = true;
    dispatch({ type: "GENERATE_STARTED" });
    try {
      const result = await composeItinerary(buildComposeRequest(values));
      if (isCompositionFailure(result)) {
        dispatch({ type: "GENERATE_REJECTED", message: describeCompositionFailure(result) });
        return;
      }
      // Re-read the persisted itinerary (with its saved route) rather than
      // trusting the in-memory compose response — the same path a refresh uses.
      dispatch({ type: "LOADING_ROUTE" });
      const saved = await getItinerary(result.id);
      dispatch({ type: "COMPLETED" });
      onComposed(saved);
    } catch (err) {
      dispatch({
        type: "FAILED",
        message: err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      });
    } finally {
      inFlight.current = false;
    }
  }

  const controlClassName =
    "w-full rounded-xl border border-line-strong bg-surface-raised px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-subtle focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-60";

  const steps = plannerSteps(planner.phase);
  const showSteps = planner.phase === "GENERATING" || planner.phase === "ROUTING" || planner.phase === "COMPLETED";

  return (
    <Card>
      <CardBody className="space-y-5">
        <div className="rounded-2xl bg-pastel-lemon/45 p-4 sm:p-5">
          <h2 className="text-lg font-semibold text-ink">
            Plan a personalized trip
          </h2>
          <p className="mt-1 text-sm leading-6 text-ink-muted">
            Tell LocaLens about your day and your group. We&apos;ll first show how many similar
            plans exist, then compose a feasible, travel-aware itinerary when you&apos;re ready.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleFindSimilar} noValidate>
          <fieldset className="space-y-4" disabled={busy}>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">Destination</span>
                <input
                  className={controlClassName}
                  value={values.destination}
                  onChange={(event) => update({ destination: event.target.value })}
                  placeholder="e.g. Mumbai"
                  aria-invalid={Boolean(errors.fields.destination)}
                  required
                />
                {errors.fields.destination ? (
                  <span className="mt-1 block text-xs text-danger">{errors.fields.destination}</span>
                ) : null}
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">
                  What are you interested in?
                </span>
                <input
                  className={controlClassName}
                  value={values.query}
                  onChange={(event) => update({ query: event.target.value })}
                  placeholder="e.g. food, heritage walks"
                />
              </label>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">Date</span>
                <input
                  type="date"
                  className={controlClassName}
                  value={values.date}
                  onChange={(event) => update({ date: event.target.value })}
                  aria-invalid={Boolean(errors.fields.date)}
                  required
                />
                {errors.fields.date ? (
                  <span className="mt-1 block text-xs text-danger">{errors.fields.date}</span>
                ) : null}
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">
                  Max experiences
                </span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  className={controlClassName}
                  value={values.maxExperiences}
                  onChange={(event) => update({ maxExperiences: Number(event.target.value) })}
                />
                {errors.fields.maxExperiences ? (
                  <span className="mt-1 block text-xs text-danger">{errors.fields.maxExperiences}</span>
                ) : null}
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">
                  Start time
                </span>
                <input
                  type="time"
                  className={controlClassName}
                  value={values.startTime}
                  onChange={(event) => update({ startTime: event.target.value })}
                />
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">
                  End time
                </span>
                <input
                  type="time"
                  className={controlClassName}
                  value={values.endTime}
                  onChange={(event) => update({ endTime: event.target.value })}
                />
                {errors.fields.time ? (
                  <span className="mt-1 block text-xs text-danger">{errors.fields.time}</span>
                ) : null}
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">
                  Max budget (INR)
                </span>
                <input
                  type="number"
                  min={0}
                  className={controlClassName}
                  value={values.maxBudget}
                  onChange={(event) => update({ maxBudget: event.target.value })}
                  placeholder="No limit"
                />
                {errors.fields.maxBudget ? (
                  <span className="mt-1 block text-xs text-danger">{errors.fields.maxBudget}</span>
                ) : null}
              </label>

              <label className="block text-sm">
                <span className="mb-1.5 block font-medium text-ink">Pace</span>
                <select
                  className={controlClassName}
                  value={values.pace}
                  onChange={(event) => update({ pace: event.target.value as CompositionPace })}
                >
                  <option value="relaxed">Relaxed</option>
                  <option value="balanced">Balanced</option>
                  <option value="packed">Packed</option>
                </select>
              </label>
            </div>

            <details className="group rounded-2xl border border-line bg-surface-raised p-4" open>
              <summary className="flex cursor-pointer list-none items-center justify-between gap-2 text-sm font-semibold text-ink">
                <span className="inline-flex items-center gap-2">
                  <Users className="size-4 text-accent" aria-hidden="true" />
                  Group details
                </span>
                <span className="text-xs font-normal text-ink-subtle">
                  {values.participants.length} {values.participants.length === 1 ? "traveler" : "travelers"}
                </span>
              </summary>
              <div className="mt-3 space-y-3">
                <label className="block text-sm">
                  <span className="mb-1.5 block font-medium text-ink">Group size</span>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    max={MAX_PARTICIPANTS}
                    className={`${controlClassName} max-w-32`}
                    value={values.groupSize}
                    onChange={(event) => handleGroupSize(event.target.value)}
                    aria-invalid={Boolean(errors.fields.groupSize)}
                  />
                  {errors.fields.groupSize ? (
                    <span className="mt-1 block text-xs text-danger">{errors.fields.groupSize}</span>
                  ) : (
                    <span className="mt-1 block text-xs text-ink-subtle">
                      Up to {MAX_PARTICIPANTS}. Group size is checked against each experience&apos;s recorded capacity.
                    </span>
                  )}
                </label>
                <ParticipantFields
                  participants={values.participants}
                  errors={errors.participants}
                  disabled={busy}
                  controlClassName={controlClassName}
                  onChange={handleParticipantChange}
                />
                <p className="text-xs text-ink-subtle">
                  Ages and genders are saved privately with your itinerary. They&apos;re never used to guess
                  what you&apos;d enjoy.
                </p>
              </div>
            </details>

            <div className="space-y-1.5 text-sm">
              <span className="block font-medium text-ink">Starting point</span>
              <StartLocationField
                value={values.startLocation}
                onChange={(startLocation: StartLocationValue | null) => update({ startLocation })}
                disabled={busy}
                controlClassName={controlClassName}
              />
            </div>

            <label className="flex items-start gap-2 text-xs text-ink-muted">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={values.shareAnonymously}
                onChange={(event) => update({ shareAnonymously: event.target.checked })}
              />
              <span>
                Let other travelers preview an anonymized summary of this plan (destination, group
                size, themes, pace — never ages, genders or your identity). Off by default.
              </span>
            </label>
          </fieldset>

          {planner.error && planner.phase !== "ERROR" ? (
            <p className="rounded-xl bg-warning-soft px-3.5 py-3 text-sm text-warning" role="alert">
              {planner.error}
            </p>
          ) : null}
          {planner.phase === "ERROR" && planner.error ? (
            <p className="text-sm text-danger" role="alert">
              {planner.error}
            </p>
          ) : null}

          {!showResults ? (
            <Button type="submit" loading={planner.phase === "VALIDATING"} disabled={busy} className="w-full">
              Find similar plans
            </Button>
          ) : null}
        </form>

        {showResults ? (
          <SimilarItinerariesPanel
            checking={planner.phase === "CHECKING_SIMILAR"}
            result={similar}
            lookupError={planner.similarError}
            busy={busy}
            loadingMore={loadingMore}
            onCreate={handleCreate}
            onLoadMore={handleLoadMore}
          />
        ) : null}

        {showSteps ? (
          <ol className="space-y-1.5 text-sm" aria-label="Progress" aria-live="polite">
            {steps.map((step) => (
              <li key={step.label} className="flex items-center gap-2">
                {step.status === "done" ? (
                  <CheckCircle2 className="size-4 text-accent" aria-hidden="true" />
                ) : step.status === "active" ? (
                  <Loader2 className="size-4 animate-spin text-accent" aria-hidden="true" />
                ) : (
                  <Circle className="size-4 text-ink-subtle" aria-hidden="true" />
                )}
                <span className={step.status === "pending" ? "text-ink-subtle" : "text-ink"}>
                  {step.label}
                  <span className="sr-only"> — {step.status}</span>
                </span>
              </li>
            ))}
          </ol>
        ) : null}
      </CardBody>
    </Card>
  );
}
