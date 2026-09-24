import { apiClient } from "@/lib/api/client";
import type { ApiExperienceListResponse, ExperienceListFilters } from "@/types/api";
import type { ProviderMe, ProviderUpdateInput } from "@/types/provider-api";

export function getMyProvider() {
  return apiClient.get<ProviderMe>("/api/v1/providers/me");
}

export function updateMyProvider(payload: ProviderUpdateInput) {
  return apiClient.put<ProviderMe>("/api/v1/providers/me", payload);
}

function toSearchParams(filters: ExperienceListFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.limit != null) params.set("limit", String(filters.limit));
  if (filters.offset != null) params.set("offset", String(filters.offset));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function getMyExperiences(filters: ExperienceListFilters = {}) {
  return apiClient.get<ApiExperienceListResponse>(`/api/v1/providers/me/experiences${toSearchParams(filters)}`);
}
