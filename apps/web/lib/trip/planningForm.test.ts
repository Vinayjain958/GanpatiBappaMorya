import { describe, expect, it } from "vitest";
import {
  MAX_PARTICIPANTS,
  buildComposeRequest,
  buildPlanningContext,
  buildSimilarRequest,
  describeSimilarExample,
  hasErrors,
  initialPlannerState,
  initialPlanningValues,
  isPlannerBusy,
  parseAge,
  parseGroupSize,
  plannerReducer,
  plannerSteps,
  resizeParticipants,
  similarCountLabel,
  validatePlanningForm,
} from "./planningForm";
import type { PlanningFormValues, TripPlannerEvent, TripPlannerState } from "./planningForm";

function validValues(overrides: Partial<PlanningFormValues> = {}): PlanningFormValues {
  return {
    ...initialPlanningValues(),
    destination: "Mumbai",
    date: "2026-10-12",
    groupSize: "4",
    participants: [
      { sequence: 1, age: "21", gender: "female" },
      { sequence: 2, age: "22", gender: "male" },
      { sequence: 3, age: "24", gender: "female" },
      { sequence: 4, age: "20", gender: "prefer_not_to_say" },
    ],
    ...overrides,
  };
}

function run(events: TripPlannerEvent[], start: TripPlannerState = initialPlannerState): TripPlannerState {
  return events.reduce(plannerReducer, start);
}

describe("group size -> participant rows", () => {
  it("group size 1 renders one row", () => {
    expect(initialPlanningValues().participants).toHaveLength(1);
    expect(resizeParticipants([], 1)).toEqual([{ sequence: 1, age: "", gender: "" }]);
  });

  it("group size 4 renders four blank rows — nothing invented", () => {
    const rows = resizeParticipants(initialPlanningValues().participants, 4);
    expect(rows.map((r) => r.sequence)).toEqual([1, 2, 3, 4]);
    expect(rows.every((r) => r.age === "" && r.gender === "")).toBe(true);
  });

  it("5 -> 3 keeps the first three rows and what was typed in them", () => {
    const five = resizeParticipants(validValues().participants, 5);
    const three = resizeParticipants(five, 3);
    expect(three).toEqual(validValues().participants.slice(0, 3));
  });

  it("parses group size strictly", () => {
    expect(parseGroupSize("4")).toBe(4);
    expect(parseGroupSize("0")).toBeNull();
    expect(parseGroupSize("2.5")).toBeNull();
    expect(parseGroupSize("")).toBeNull();
    expect(parseGroupSize(String(MAX_PARTICIPANTS + 1))).toBeNull();
  });
});

describe("validation mirrors the backend", () => {
  it("accepts a complete form", () => {
    expect(hasErrors(validatePlanningForm(validValues()))).toBe(false);
  });

  it("requires destination and date, and a valid time window", () => {
    const errors = validatePlanningForm(validValues({ destination: " ", date: "", startTime: "18:00", endTime: "09:00" }));
    expect(errors.fields.destination).toBeTruthy();
    expect(errors.fields.date).toBeTruthy();
    expect(errors.fields.time).toBeTruthy();
  });

  it("validates ages as whole numbers 0-120", () => {
    expect(parseAge("0")).toBe(0);
    expect(parseAge("120")).toBe(120);
    expect(parseAge("121")).toBeNull();
    expect(parseAge("-1")).toBeNull();
    expect(parseAge("21.5")).toBeNull();
    const errors = validatePlanningForm(
      validValues({
        participants: [
          { sequence: 1, age: "", gender: "" },
          { sequence: 2, age: "130", gender: "" },
          { sequence: 3, age: "24", gender: "" },
          { sequence: 4, age: "abc", gender: "" },
        ],
      }),
    );
    expect(Object.keys(errors.participants).map(Number)).toEqual([1, 2, 4]);
  });

  it("flags a participant count that doesn't match group size", () => {
    const errors = validatePlanningForm(validValues({ groupSize: "5" }));
    expect(errors.fields.groupSize).toBeTruthy();
  });

  it("rejects negative budgets", () => {
    expect(validatePlanningForm(validValues({ maxBudget: "-5" })).fields.maxBudget).toBeTruthy();
  });
});

describe("request builders", () => {
  it("maps gender '' to null and never sends names", () => {
    const ctx = buildPlanningContext(validValues({ participants: [{ sequence: 1, age: "30", gender: "" }], groupSize: "1" }));
    expect(ctx).toEqual({
      group_size: 1,
      participants: [{ sequence: 1, age_years: 30, gender: null }],
      start_location_label: null,
      is_discoverable: false,
    });
  });

  it("similarity request carries no start-location coordinates", () => {
    const request = buildSimilarRequest(
      validValues({ startLocation: { lat: 18.9, lng: 72.8, label: "Hotel", source: "search" } }),
    );
    expect(request).not.toHaveProperty("origin_lat");
    expect(request.city).toBe("Mumbai");
    expect(request.planning.group_size).toBe(4);
    expect(request.planning.start_location_label).toBe("Hotel");
  });

  it("compose request reuses origin_lat/origin_lng and nests planning", () => {
    const request = buildComposeRequest(
      validValues({ startLocation: { lat: 18.9, lng: 72.8, label: "Hotel", source: "browser" }, shareAnonymously: true }),
    );
    expect(request.origin_lat).toBe(18.9);
    expect(request.origin_lng).toBe(72.8);
    expect(request.start_time).toBe("09:00:00");
    expect(request.planning?.participants).toHaveLength(4);
    expect(request.planning?.is_discoverable).toBe(true);
    expect(request).not.toHaveProperty("traveler_id");
  });
});

describe("planner state machine", () => {
  it("shows a loading state while checking similar plans, then the count", () => {
    const checking = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }]);
    expect(checking.phase).toBe("CHECKING_SIMILAR");
    expect(isPlannerBusy(checking.phase)).toBe(true);
    const done = plannerReducer(checking, { type: "SIMILAR_LOADED", count: 12 });
    expect(done).toMatchObject({ phase: "SIMILAR_RESULTS", similarCount: 12 });
    expect(similarCountLabel(12)).toBe("12 similar itineraries found");
  });

  it("zero results still allows personalized generation", () => {
    const zero = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_LOADED", count: 0 }]);
    expect(similarCountLabel(0)).toBe("0 similar itineraries found");
    expect(plannerReducer(zero, { type: "GENERATE_STARTED" }).phase).toBe("GENERATING");
  });

  it("a failed similarity lookup never blocks generation", () => {
    const failed = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_FAILED", message: "down" }]);
    expect(failed.similarError).toBe("down");
    expect(plannerReducer(failed, { type: "GENERATE_STARTED" }).phase).toBe("GENERATING");
  });

  it("generation cannot start before the similarity step (never auto-creates)", () => {
    expect(plannerReducer(initialPlannerState, { type: "GENERATE_STARTED" }).phase).toBe("EMPTY");
    expect(run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "GENERATE_STARTED" }]).phase).toBe("CHECKING_SIMILAR");
  });

  it("prevents duplicate submissions while busy", () => {
    const generating = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_LOADED", count: 1 }, { type: "GENERATE_STARTED" }]);
    expect(isPlannerBusy(generating.phase)).toBe(true);
    expect(plannerReducer(generating, { type: "GENERATE_STARTED" })).toBe(generating);
    expect(plannerReducer(generating, { type: "SUBMIT" })).toBe(generating);
    expect(plannerReducer(generating, { type: "EDIT_FIELD" })).toBe(generating);
  });

  it("walks success: generating -> route loading -> completed", () => {
    const done = run([
      { type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_LOADED", count: 3 },
      { type: "GENERATE_STARTED" }, { type: "LOADING_ROUTE" },
    ]);
    expect(done.phase).toBe("ROUTING");
    expect(plannerSteps("ROUTING").map((s) => s.status)).toEqual(["done", "done", "active", "pending"]);
    expect(plannerReducer(done, { type: "COMPLETED" }).phase).toBe("COMPLETED");
    expect(plannerSteps("COMPLETED").every((s) => s.status === "done")).toBe(true);
  });

  it("handles an infeasible plan and a hard error", () => {
    const base = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_LOADED", count: 0 }, { type: "GENERATE_STARTED" }]);
    const rejected = plannerReducer(base, { type: "GENERATE_REJECTED", message: "No plan fits" });
    expect(rejected).toMatchObject({ phase: "SIMILAR_RESULTS", error: "No plan fits" });
    const failed = plannerReducer(base, { type: "FAILED", message: "Server error" });
    expect(failed).toMatchObject({ phase: "ERROR", error: "Server error" });
    expect(plannerReducer(failed, { type: "GENERATE_STARTED" }).phase).toBe("GENERATING"); // retry allowed
  });

  it("validation failure returns to the relevant editing state", () => {
    const state = run([{ type: "SUBMIT" }, { type: "VALIDATION_FAILED", groupRelated: true }]);
    expect(state.phase).toBe("GROUP_DETAILS_EDITING");
  });

  it("editing after results invalidates the similarity answer", () => {
    const results = run([{ type: "SUBMIT" }, { type: "SIMILAR_STARTED" }, { type: "SIMILAR_LOADED", count: 4 }]);
    expect(plannerReducer(results, { type: "EDIT_GROUP" })).toMatchObject({ phase: "GROUP_DETAILS_EDITING", similarCount: null });
  });
});

describe("similar example preview", () => {
  it("shows only safe, high-level facts", () => {
    const view = describeSimilarExample({
      example_id: "x",
      destination_label: "Mumbai",
      duration_days: 1,
      group_size: 4,
      pace: "balanced",
      interests: ["food"],
      category_names: ["Food & Drink", "Culture & Heritage"],
      stop_count: 3,
      total_distance_km: 8.7,
      total_travel_minutes: 34,
      similarity_score: 0.9,
      matched_dimensions: ["destination"],
    });
    expect(view).toEqual({
      duration: "1 Day",
      destination: "Mumbai",
      travelers: "4 Travelers",
      themes: "Food & Drink + Culture & Heritage",
      pace: "Moderate pace",
      stops: "3 stops",
      distance: "8.7 km of travel",
    });
  });
});
