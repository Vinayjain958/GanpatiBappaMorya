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

/** Resolved image + provenance for attribution/labeling. `isFallback` means
 * imageUrl is LocaLens's own generic category art, not a real venue photo —
 * see apps/api/src/services/experience_images.py for the resolution ladder. */
export interface ExperienceImage {
  imageUrl: string;
  isFallback: boolean;
  isPlaceSpecific: boolean;
  source: string | null;
  sourceUrl: string | null;
  license: string | null;
  author: string | null;
  attributionText: string | null;
}

export interface ReviewItem {
  id: string;
  rating: number;
  title: string | null;
  body: string | null;
  author: string;
  reviewedAt: string;
  isSynthetic: boolean;
}

export interface ExperienceRatingSummary {
  /** Null when the experience has zero real reviews (e.g. a brand-new
   * traveler contribution) — the UI must render "No ratings yet", never
   * a fabricated 0.0. */
  averageRating: number | null;
  reviewCount: number;
  distribution: Record<number, number>;
  isSynthetic: boolean;
}

export interface OpeningHourDay {
  day: string;
  dayIndex: number;
  open: string | null;
  close: string | null;
  isClosed: boolean;
  isSynthetic?: boolean;
}

export interface ReviewSubmission {
  ratingValue: number;
  title: string;
  body: string;
}

export interface Experience {
  id: string;
  title: string;
  category: ExperienceCategory;
  categoryLabel: string;
  shortDescription: string;
  description: string;
  /** Convenience flat URL for simple <img>/<Image> usage — always equals
   * image.imageUrl. Prefer `image` when you need attribution/provenance. */
  imageUrl: string;
  image: ExperienceImage;
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
  openingHoursWeekly?: OpeningHourDay[];
  isOpeningHoursSynthetic?: boolean;
  reviews?: ReviewItem[];
  ratingSummary?: ExperienceRatingSummary | null;
  highlights: string[];
  isSynthetic: boolean;
  /** Only present on the detail shape (ApiExperienceDetail carries
   * source_type; list/summary responses don't). "traveler_submission"
   * means this was published directly by a traveler via the "Add a
   * Local Experience" contribution flow (see docs/DECISIONS.md ADR-058)
   * — the UI shows a "Community Added" label for it, never "Verified". */
  sourceType?: string;
  /** Phase 7 — only present when this result came from the personalized
   * ranking pipeline (POST /api/v1/recommendations); undefined for plain
   * discovery/search results. */
  matchSignals?: string[];
  personalized?: boolean;
}
