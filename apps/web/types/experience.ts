/** Category slug — must stay in sync with apps/api/src/core/category_map.py CATEGORIES
 * until a GET /api/v1/categories endpoint exists. */
export type ExperienceCategory = string;

export interface ExperienceProvider {
  id: string;
  name: string;
  verified: boolean;
}

export interface AccessibilityInfo {
  wheelchairAccessible: boolean | null;
  stepFree: boolean | null;
  notes?: string;
}

export interface Experience {
  id: string;
  title: string;
  category: ExperienceCategory;
  categoryLabel: string;
  shortDescription: string;
  description: string;
  imageUrl: string;
  location: {
    area: string;
    city: string;
    lat: number;
    lng: number;
  };
  /** Straight-line distance — null unless a location-aware search
   * supplied it (or a local reference point was used as a fallback). */
  distanceKm: number | null;
  /** Only present when travel-time enrichment succeeded for this result. */
  travelTimeMinutes: number | null;
  travelTimeSource: "osrm" | "haversine_estimate" | null;
  durationMinutes: number | null;
  priceInr: number;
  isPriceEstimated: boolean;
  rating: number | null;
  reviewCount: number | null;
  provider: ExperienceProvider;
  tags: string[];
  accessibility: AccessibilityInfo;
  availability: "available" | "limited" | "unavailable";
  openingHours: string | null;
  highlights: string[];
  isSynthetic: boolean;
}
