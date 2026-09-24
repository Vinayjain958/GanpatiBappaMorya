import { describe, it, expect, vi, beforeEach } from "vitest";
import { feedbackApi } from "./feedback";
import * as client from "./client";

vi.mock("./client", () => ({
  fetchApi: vi.fn(),
}));

describe("feedbackApi", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should record interaction", async () => {
    const mockResponse = { interaction_id: "int-1", created: true, idempotent: false };
    vi.mocked(client.fetchApi).mockResolvedValue(mockResponse);

    const result = await feedbackApi.recordInteraction({
      experience_id: "exp-1",
      event_type: "SAVE",
      client_event_id: "test",
    });

    expect(client.fetchApi).toHaveBeenCalledWith("/api/v1/feedback/interactions", {
      method: "POST",
      body: JSON.stringify({
        experience_id: "exp-1",
        event_type: "SAVE",
        client_event_id: "test",
      }),
    });
    expect(result).toEqual(mockResponse);
  });
});
