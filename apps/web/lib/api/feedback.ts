import { 
  RecordInteractionRequest, 
  RecordInteractionResponse,
  AffinityProfileResponse
} from "@/types/api";
import { fetchApi } from "./client";

export const feedbackApi = {
  recordInteraction: async (request: RecordInteractionRequest): Promise<RecordInteractionResponse> => {
    return fetchApi("/api/v1/feedback/interactions", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
  
  getAffinities: async (): Promise<AffinityProfileResponse> => {
    return fetchApi("/api/v1/feedback/profile/affinities");
  },
  
  getMetrics: async (): Promise<Record<string, unknown>> => {
    return fetchApi("/api/v1/feedback/metrics");
  }
};
