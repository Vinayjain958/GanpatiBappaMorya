import { apiClient } from "@/lib/api/client";

export interface ApiCategory {
  id: string;
  slug: string;
  name: string;
  icon: string | null;
  sort_order: number;
}

export function listCategories() {
  return apiClient.get<ApiCategory[]>("/api/v1/categories");
}
