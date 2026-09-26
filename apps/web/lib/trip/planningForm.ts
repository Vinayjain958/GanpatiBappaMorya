import { env } from "@/lib/config/env";
import type {
  ComposeItineraryRequest,
  CompositionPace,
  ItineraryPlanningContext,
  ParticipantGender,
  SimilarItinerariesRequest,
  SimilarItinerarySummary,
} from "@/types/api";

/**
 * Pure model for the personalized Trip Planner form (ADR-056). React
 * components only render this state and dispatch events — every
 * validation rule, request shape and state transition lives here so it
 * is unit-testable and identical across components. Backend validation
 * (src/schemas/itinerary.py) stays authoritative; these rules only
 * mirror it for good UX and never "fix" invalid input silently.
 */

export const MIN_PARTICIPANT_AGE = 0;
export const MAX_PARTICIPANT_AGE = 120;
export const MAX_PARTICIPANTS = env.maxItineraryParticipants;

export const GENDER_OPTIONS: ReadonlyArray<{ value: ParticipantGender; label: string }> = [
  { value: "prefer_not_to_say", label: "Prefer not to say" },
  { value: "female", label: "Female" },
  { value: "male", label: "Male" },
  { value: "non_binary", label: "Non-binary" },
  { value: "self_described", label: "Another identity" },
];

export interface ParticipantDraft {
  sequence: number;
  /** Raw input text — never coerced until validation. */
  age: string;
  /** "" = not provided (sent as null). */
  gender: ParticipantGender | "";
}

export interface StartLocationValue {
  lat: number;
  lng: number;
  label: string;
  source: "search" | "browser";
}

export interface PlanningFormValues {
  destination: string;
  query: string;
  date: string;
  startTime: string;
  endTime: string;
  maxExperiences: number;
  maxBudget: string;
  pace: CompositionPace;
  groupSize: string;
  participants: ParticipantDraft[];
  startLocation: StartLocationValue | null;
  shareAnonymously: boolean;
}

export function initialPlanningValues(): PlanningFormValues {
  return {
    destination: "",
    query: "",
    date: "",
    startTime: "09:00",
    endTime: "18:00",
    maxExperiences: 4,
    maxBudget: "",
    pace: "balanced",
    groupSize: "1",
    participants: [{ sequence: 1, age: "", gender: "" }],
    startLocation: null,
    shareAnonymously: false,
  };
}

/** Parses the group-size input. Returns null for anything that isn't a
 * whole number in range (the caller shows an error; rows are left as-is). */
export function parseGroupSize(raw: string): number | null {
  if (!/^\d+$/.test(raw.trim())) return null;
  const value = Number(raw.trim());
  if (value < 1 || value > MAX_PARTICIPANTS) return null;
  return value;
}

/**
 * Resizes participant rows to `size`: keeps existing rows (and what was
 * typed in them) in order, drops only the excess rows at the end, and
 * appends BLANK rows for new travelers — never invents ages/genders.
 */
export function resizeParticipants(current: ParticipantDraft[], size: number): ParticipantDraft[] {
  const next = current.slice(0, size).map((p, i) => ({ ...p, sequence: i + 1 }));
  for (let i = next.length; i < size; i += 1) {
    next.push({ sequence: i + 1, age: "", gender: "" });
  }
  return next;
}

export function parseAge(raw: string): number | null {
  const trimmed = raw.trim();
  if (!/^\d+$/.test(trimmed)) return null;
  const value = Number(trimmed);
  if (value < MIN_PARTICIPANT_AGE || value > MAX_PARTICIPANT_AGE) return null;
  return value;
}

export interface PlanningFormErrors {
  fields: Partial<Record<"destination" | "date" | "time" | "maxBudget" | "groupSize" | "maxExperiences", string>>;
  /** keyed by participant sequence */
  participants: Record<number, string>;
}

export function hasErrors(errors: PlanningFormErrors): boolean {
  return Object.keys(errors.fields).length > 0 || Object.keys(errors.participants).length > 0;
}

export function validatePlanningForm(values: PlanningFormValues): PlanningFormErrors {
  const errors: PlanningFormErrors = { fields: {}, participants: {} };

  if (!values.destination.trim()) errors.fields.destination = "Enter a destination city.";
  if (!values.date) errors.fields.date = "Choose a date.";
  if (!values.startTime || !values.endTime || values.endTime <= values.startTime) {
    errors.fields.time = "End time must be after start time.";
  }
  if (values.maxBudget.trim() !== "") {
    const budget = Number(values.maxBudget);
    if (!Number.isFinite(budget) || budget < 0) errors.fields.maxBudget = "Budget can't be negative.";
  }
  if (!Number.isInteger(values.maxExperiences) || values.maxExperiences < 1 || values.maxExperiences > 20) {
    errors.fields.maxExperiences = "Choose between 1 and 20 experiences.";
  }

  const groupSize = parseGroupSize(values.groupSize);
  if (groupSize === null) {
    errors.fields.groupSize = `Group size must be a whole number from 1 to ${MAX_PARTICIPANTS}.`;
  } else if (values.participants.length !== groupSize) {
    errors.fields.groupSize = "Every traveler in the group needs a row.";
  }

  for (const participant of values.participants) {
    if (participant.age.trim() === "") {
      errors.participants[participant.sequence] = "Enter an age.";
    } else if (parseAge(participant.age) === null) {
      errors.participants[participant.sequence] =
        `Age must be a whole number from ${MIN_PARTICIPANT_AGE} to ${MAX_PARTICIPANT_AGE}.`;
    }
  }

  return errors;
}

/** Only call after validatePlanningForm() returned no errors. */
export function buildPlanningContext(values: PlanningFormValues): ItineraryPlanningContext {
  return {
    group_size: values.participants.length,
    participants: values.participants.map((p) => ({
      sequence: p.sequence,
      age_years: parseAge(p.age) as number,
      gender: p.gender === "" ? null : p.gender,
    })),
    start_location_label: values.startLocation?.label ?? null,
    is_discoverable: values.shareAnonymously,
  };
}

function budgetOrNull(values: PlanningFormValues): number | null {
  return values.maxBudget.trim() === "" ? null : Number(values.maxBudget);
}

/** Similarity lookup payload — deliberately without start-location
 * coordinates (not a similarity signal; data minimization). */
export function buildSimilarRequest(
  values: PlanningFormValues,
  page: { limit?: number; offset?: number } = {},
): SimilarItinerariesRequest {
  return {
    city: values.destination.trim(),
    itinerary_date: values.date,
    query: values.query.trim() || null,
    max_budget: budgetOrNull(values),
    pace: values.pace,
    planning: buildPlanningContext(values),
    limit: page.limit ?? 5,
    offset: page.offset ?? 0,
  };
}

export function buildComposeRequest(values: PlanningFormValues): ComposeItineraryRequest {
  return {
    query: values.query.trim() || undefined,
    city: values.destination.trim(),
    itinerary_date: values.date,
    start_time: `${values.startTime}:00`,
    end_time: `${values.endTime}:00`,
    max_experiences: values.maxExperiences,
    max_budget: budgetOrNull(values) ?? undefined,
    pace: values.pace,
    origin_lat: values.startLocation?.lat ?? null,
    origin_lng: values.startLocation?.lng ?? null,
    planning: buildPlanningContext(values),
  };
}

// ─── Planner state machine ──────────────────────────────────────────────

export type TripPlannerPhase =
  | "EMPTY"
  | "FORM_EDITING"
  | "GROUP_DETAILS_EDITING"
  | "VALIDATING"
  | "CHECKING_SIMILAR"
  | "SIMILAR_RESULTS"
  | "GENERATING"
  | "ROUTING"
  | "COMPLETED"
  | "ERROR";

export interface TripPlannerState {
  phase: TripPlannerPhase;
  similarCount: number | null;
  /** Similarity lookup failed — generation stays available regardless. */
  similarError: string | null;
  error: string | null;
}

export type TripPlannerEvent =
  | { type: "EDIT_FIELD" }
  | { type: "EDIT_GROUP" }
  | { type: "SUBMIT" }
  | { type: "VALIDATION_FAILED"; groupRelated: boolean }
  | { type: "SIMILAR_STARTED" }
  | { type: "SIMILAR_LOADED"; count: number }
  | { type: "SIMILAR_FAILED"; message: string }
  | { type: "GENERATE_STARTED" }
  | { type: "GENERATE_REJECTED"; message: string }
  | { type: "LOADING_ROUTE" }
  | { type: "COMPLETED" }
  | { type: "FAILED"; message: string };

export const initialPlannerState: TripPlannerState = {
  phase: "EMPTY",
  similarCount: null,
  similarError: null,
  error: null,
};

const BUSY_PHASES: ReadonlySet<TripPlannerPhase> = new Set([
  "VALIDATING",
  "CHECKING_SIMILAR",
  "GENERATING",
  "ROUTING",
]);

/** True while a request is in flight — every submit/generate button is
 * disabled, which is what prevents duplicate submissions. */
export function isPlannerBusy(phase: TripPlannerPhase): boolean {
  return BUSY_PHASES.has(phase);
}

export function plannerReducer(state: TripPlannerState, event: TripPlannerEvent): TripPlannerState {
  switch (event.type) {
    case "EDIT_FIELD":
    case "EDIT_GROUP":
      if (isPlannerBusy(state.phase)) return state; // inputs are locked mid-request
      // Any edit invalidates a previous similarity answer.
      return {
        ...initialPlannerState,
        phase: event.type === "EDIT_GROUP" ? "GROUP_DETAILS_EDITING" : "FORM_EDITING",
      };
    case "SUBMIT":
      if (isPlannerBusy(state.phase)) return state; // duplicate submit ignored
      return { ...state, phase: "VALIDATING", error: null };
    case "VALIDATION_FAILED":
      return { ...state, phase: event.groupRelated ? "GROUP_DETAILS_EDITING" : "FORM_EDITING" };
    case "SIMILAR_STARTED":
      return { ...state, phase: "CHECKING_SIMILAR", similarCount: null, similarError: null };
    case "SIMILAR_LOADED":
      return { ...state, phase: "SIMILAR_RESULTS", similarCount: event.count, similarError: null };
    case "SIMILAR_FAILED":
      return { ...state, phase: "SIMILAR_RESULTS", similarCount: null, similarError: event.message };
    case "GENERATE_STARTED":
      if (state.phase !== "SIMILAR_RESULTS" && state.phase !== "ERROR") return state;
      return { ...state, phase: "GENERATING", error: null };
    case "GENERATE_REJECTED":
      // A valid "no feasible plan" answer: back to results so the user can adjust or retry.
      return { ...state, phase: "SIMILAR_RESULTS", error: event.message };
    case "LOADING_ROUTE":
      return { ...state, phase: "ROUTING" };
    case "COMPLETED":
      return { ...state, phase: "COMPLETED", error: null };
    case "FAILED":
      return { ...state, phase: "ERROR", error: event.message };
    default:
      return state;
  }
}

export interface PlannerStep {
  label: string;
  status: "pending" | "active" | "done";
}

/** Truthful step list — no fake percentages. Composition AND route
 * calculation both happen inside the one server-side compose request, so
 * they are reported as a single step; "Loading saved route" is the
 * follow-up read of the persisted itinerary. */
export function plannerSteps(phase: TripPlannerPhase): PlannerStep[] {
  const order: TripPlannerPhase[] = ["CHECKING_SIMILAR", "GENERATING", "ROUTING", "COMPLETED"];
  const labels = [
    "Finding similar plans",
    "Creating personalized itinerary and calculating route",
    "Loading saved route",
    "Finalizing itinerary",
  ];
  if (phase === "COMPLETED") return labels.map((label) => ({ label, status: "done" }));
  const current = phase === "SIMILAR_RESULTS" ? 1 : order.indexOf(phase);
  return labels.map((label, index) => ({
    label,
    status:
      current === -1 ? "pending" : index < current ? "done" : index === current ? "active" : "pending",
  }));
}

export function similarCountLabel(count: number): string {
  return `${count} similar ${count === 1 ? "itinerary" : "itineraries"} found`;
}

const PACE_LABELS: Record<string, string> = {
  relaxed: "Relaxed pace",
  balanced: "Moderate pace",
  packed: "Packed pace",
};

function titleCase(value: string): string {
  return value.replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Display-only summary of an anonymized similar-plan example. */
export function describeSimilarExample(example: SimilarItinerarySummary) {
  const themes = example.category_names.length ? example.category_names : example.interests.map(titleCase);
  return {
    duration: `${example.duration_days} ${example.duration_days === 1 ? "Day" : "Days"}`,
    destination: example.destination_label ?? "Destination not recorded",
    travelers: `${example.group_size} ${example.group_size === 1 ? "Traveler" : "Travelers"}`,
    themes: themes.length ? themes.join(" + ") : null,
    pace: PACE_LABELS[example.pace] ?? example.pace,
    stops: `${example.stop_count} ${example.stop_count === 1 ? "stop" : "stops"}`,
    distance: example.total_distance_km != null ? `${example.total_distance_km} km of travel` : null,
  };
}
