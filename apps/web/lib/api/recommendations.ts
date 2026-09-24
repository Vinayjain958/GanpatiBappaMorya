import { RecommendationRequest, RecommendationResponse } from "@/types/api";
import { fetchApi } from "./client";

export const recommendationApi = {
  getRecommendations: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
    return fetchApi("/api/v1/recommendations", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};
