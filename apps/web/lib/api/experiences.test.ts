import { describe, it, expect, vi, beforeEach } from "vitest";
import { createExperienceReview } from "./experiences";
import * as client from "./client";

vi.mock("./client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe("createExperienceReview", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("posts the review payload and returns the created review + updated rating summary", async () => {
    const mockResponse = {
      review: {
        id: "rev-1",
        rating_value: 4,
        title: "Pretty good",
        body: "Enjoyed the visit overall.",
        author_display_name: "Jane",
        reviewed_at: "2026-09-26T12:00:00Z",
        is_synthetic: false,
      },
      rating_summary: {
        average_rating: 4.2,
        review_count: 6,
        rating_distribution: { "3": 1, "4": 3, "5": 2 },
        is_synthetic: true,
      },
    };
    vi.mocked(client.apiClient.post).mockResolvedValue(mockResponse);

    const result = await createExperienceReview("exp-1", {
      rating_value: 4,
      title: "Pretty good",
      body: "Enjoyed the visit overall.",
    });

    expect(client.apiClient.post).toHaveBeenCalledWith(
      "/api/v1/experiences/exp-1/reviews",
      { rating_value: 4, title: "Pretty good", body: "Enjoyed the visit overall." },
      { signal: undefined },
    );
    expect(result).toEqual(mockResponse);
  });
});
