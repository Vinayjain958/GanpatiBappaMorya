import {
  RecordInteractionRequest,
  RecordInteractionResponse,
  AffinityProfileResponse
} from "@/types/api";
import { apiClient } from "./client";

export const feedbackApi = {
  recordInteraction: async (request: RecordInteractionRequest): Promise<RecordInteractionResponse> => {
    return apiClient.post("/api/v1/feedback/interactions", request);
  },

  getAffinities: async (): Promise<AffinityProfileResponse> => {
    return apiClient.get("/api/v1/feedback/profile/affinities");
  },

  getMetrics: async (): Promise<Record<string, unknown>> => {
    return apiClient.get("/api/v1/feedback/metrics");
  }
};
