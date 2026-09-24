export { apiClient, ApiError } from "@/lib/api/client";
export { getHealth } from "@/lib/api/health";
export type { HealthResponse } from "@/lib/api/health";
export { getExperience, listExperiences } from "@/lib/api/experiences";
export { mapApiExperienceToUi } from "@/lib/api/experienceAdapter";
export { checkFeasibility, semanticSearchExperiences } from "@/lib/api/feasibility";
export { getMe, login, logout, refreshSession, registerAccount } from "@/lib/api/auth";
export { listCategories } from "@/lib/api/categories";
export type { ApiCategory } from "@/lib/api/categories";
export {
  getNearbyPois,
  getRoute,
  getTravelTimeMatrix,
  reverseGeocode,
  searchLocation,
} from "@/lib/api/location";
export { getMyExperiences, getMyProvider, updateMyProvider } from "@/lib/api/providers";
export {
  createAvailability,
  createExperience,
  deactivateAvailability,
  deactivateExperience,
  listAvailability,
  updateAvailability,
  updateExperience,
} from "@/lib/api/experiencesWrite";

/**
 * Placeholder namespace for future domain modules, wired up in the
 * phases that introduce their backend routes:
 *   - itinerary   (Phase 8)
 *   - itinerary   (Phase 8)
 */
export { recommendationApi } from "@/lib/api/recommendations";
export { feedbackApi } from "@/lib/api/feedback";
