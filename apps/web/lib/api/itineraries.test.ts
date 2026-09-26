import { beforeEach, describe, expect, it, vi } from "vitest";
import * as client from "./client";
import { composeItinerary, findSimilarItineraries, getItinerary, listMyItineraries } from "./itineraries";
import { fixtureItinerary } from "@/lib/itinerary/itineraryFixtures.test-data";
import { selectCurrentItinerary } from "@/lib/itinerary/itineraryDisplay";

vi.mock("./client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe("itinerary persistence API client", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("loads saved itineraries on mount from GET /api/v1/itineraries", async () => {
    const saved = fixtureItinerary();
    vi.mocked(client.apiClient.get).mockResolvedValue({ items: [saved], total: 1 });

    const result = await listMyItineraries();

    expect(client.apiClient.get).toHaveBeenCalledWith("/api/v1/itineraries", { signal: undefined });
    expect(selectCurrentItinerary(result.items)?.id).toBe("itin-1");
  });

  it("re-reads one itinerary (with participants + persisted route) by id", async () => {
    const saved = fixtureItinerary();
    vi.mocked(client.apiClient.get).mockResolvedValue(JSON.parse(JSON.stringify(saved)));

    const result = await getItinerary("itin-1");

    expect(client.apiClient.get).toHaveBeenCalledWith("/api/v1/itineraries/itin-1", { signal: undefined });
    // Shape round-trips through JSON unchanged (what a refresh receives).
    expect(result).toEqual(saved);
    expect(result.route?.legs[0].geometry?.type).toBe("LineString");
    expect(result.participants).toHaveLength(4);
    expect(result.planning_profile?.group_size).toBe(4);
  });

  it("posts the similarity lookup to /itineraries/similar (read-only endpoint)", async () => {
    vi.mocked(client.apiClient.post).mockResolvedValue({
      similar_count: 12, examples: [], examples_total: 0, limit: 5, offset: 0, has_more: false,
    });
    const request = {
      city: "Mumbai",
      itinerary_date: "2026-10-12",
      planning: { group_size: 1, participants: [{ sequence: 1, age_years: 30, gender: null }] },
    };

    const result = await findSimilarItineraries(request);

    expect(client.apiClient.post).toHaveBeenCalledWith("/api/v1/itineraries/similar", request, { signal: undefined });
    expect(result.similar_count).toBe(12);
  });

  it("sends the planning context through the existing compose endpoint", async () => {
    vi.mocked(client.apiClient.post).mockResolvedValue(fixtureItinerary());
    const request = {
      itinerary_date: "2026-10-12",
      start_time: "09:00:00",
      end_time: "18:00:00",
      city: "Mumbai",
      origin_lat: 18.93,
      origin_lng: 72.83,
      planning: { group_size: 1, participants: [{ sequence: 1, age_years: 30, gender: null }] },
    };

    await composeItinerary(request);

    expect(client.apiClient.post).toHaveBeenCalledWith("/api/v1/itineraries/compose", request, { signal: undefined });
  });
});
