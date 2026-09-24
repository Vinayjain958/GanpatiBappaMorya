/** Shapes returned by the FastAPI experience endpoints. Mirrors
 * apps/api/src/schemas/experience.py — keep in sync. */

export interface ApiCategorySummary {
  id: string;
  slug: string;
  name: string;
  icon: string | null;
}

export interface ApiLocationSummary {
  id: string;
  latitude: number;
  longitude: number;
  place_name: string | null;
  address: string | null;
  locality: string | null;
  city: string;
  state: string | null;
  country: string | null;
}

export interface ApiProviderSummary {
  id: string;
  business_name: string;
  provider_type: string | null;
  verification_status: string;
  is_synthetic: boolean;
}

export interface ApiOpeningHourWindow {
  day_of_week: number;
  open_time: string | null;
  close_time: string | null;
  is_closed: boolean;
}

export interface ApiExperienceSummary {
  id: string;
  title: string;
  short_description: string;
  category: ApiCategorySummary;
  location: ApiLocationSummary;
  provider: ApiProviderSummary;
  currency: string;
  price: number | null;
  minimum_price: number | null;
  maximum_price: number | null;
  price_type: string;
  is_price_estimated: boolean;
  duration_minutes: number | null;
  duration_is_estimated: boolean;
  rating: number | null;
  review_count: number | null;
  status: string;
  verification_status: string;
  is_synthetic: boolean;
  is_enriched: boolean;
  /** Straight-line distance from the query's lat/lng — null unless a
   * location-aware search was made. Never travel time. */
  distance_km: number | null;
  /** Only populated for the current result page when travel-time
   * enrichment succeeded (see apps/api/src/api/v1/experiences.py). */
  travel_time_minutes: number | null;
  travel_time_source: "osrm" | "haversine_estimate" | null;
}

export interface ApiExperienceDetail extends ApiExperienceSummary {
  full_description: string;
  minimum_group_size: number | null;
  maximum_group_size: number | null;
  capacity: number | null;
  wheelchair_accessible: boolean | null;
  step_free: boolean | null;
  accessibility_notes: string | null;
  suitability: string[] | null;
  tags: string[] | null;
  opening_hours_status: string;
  opening_hours: ApiOpeningHourWindow[];
  source_type: string;
  source_name: string | null;
  source_license: string | null;
  attribution_required: boolean;
  attribution_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiExperienceListResponse {
  items: ApiExperienceSummary[];
  total: number;
  limit: number;
  offset: number;
}

export type DiscoverySort = "relevance" | "distance" | "price" | "duration" | "newest";

export interface ExperienceListFilters {
  q?: string;
  category?: string;
  city?: string;
  locality?: string;
  provider?: string;
  min_price?: number;
  max_price?: number;
  min_duration_minutes?: number;
  max_duration_minutes?: number;
  source_type?: string;
  is_synthetic?: boolean;
  status?: string;
  lat?: number;
  lng?: number;
  radius_km?: number;
  sort?: DiscoverySort;
  limit?: number;
  offset?: number;
}

/* ─── Phase 6: semantic search + deterministic feasibility ────────────────
 * Mirrors apps/api/src/schemas/feasibility.py and
 * apps/api/src/schemas/semantic_search.py — keep in sync. */

export type FeasibilityStatus = "FEASIBLE" | "INFEASIBLE" | "UNKNOWN";

/** Every reason code FeasibilityService can emit — mirrors
 * apps/api/src/core/feasibility_reasons.py exactly. */
export type FeasibilityReasonCode =
  | "EXPERIENCE_INACTIVE"
  | "MISSING_LOCATION"
  | "BUDGET_EXCEEDED"
  | "PRICE_UNAVAILABLE"
  | "UNSUPPORTED_CURRENCY"
  | "DURATION_EXCEEDED"
  | "DURATION_UNAVAILABLE"
  | "OUTSIDE_AVAILABLE_TIME"
  | "OPENING_HOURS_CONFLICT"
  | "OPENING_HOURS_UNAVAILABLE"
  | "TRAVEL_TIME_EXCEEDED"
  | "TRAVEL_TIME_UNAVAILABLE"
  | "MAX_DISTANCE_EXCEEDED"
  | "GROUP_SIZE_EXCEEDS_CAPACITY"
  | "CAPACITY_UNAVAILABLE"
  | "ACCESSIBILITY_NOT_SUPPORTED"
  | "ACCESSIBILITY_DATA_UNAVAILABLE"
  | "AVAILABILITY_CONFLICT"
  | "AVAILABILITY_UNAVAILABLE"
  | "ITINERARY_CONFLICT"
  | "MISSING_TIME_CONTEXT"
  | "MISSING_ORIGIN"
  | "ROUTE_UNAVAILABLE";

export interface FeasibilityEvidence {
  [key: string]: unknown;
}

export interface FeasibilityReason {
  code: FeasibilityReasonCode;
  constraint: string;
  message: string;
  blocking: boolean;
  evidence: FeasibilityEvidence;
}

export interface FeasibilityVerdict {
  experience_id: string;
  status: FeasibilityStatus;
  reasons: FeasibilityReason[];
  checked_at: string;
  evidence: FeasibilityEvidence;
}

export interface CommittedTimeBlock {
  start: string;
  end: string;
}

export interface TravelerConstraints {
  currency?: string;
  budget_min?: number | null;
  budget_max?: number | null;
  available_date?: string | null;
  available_start?: string | null;
  available_end?: string | null;
  available_duration_minutes?: number | null;
  timezone?: string | null;
  origin_lat?: number | null;
  origin_lng?: number | null;
  travel_mode?: "driving" | "walking" | "cycling" | null;
  max_distance_km?: number | null;
  max_travel_time_minutes?: number | null;
  party_size?: number | null;
  accessibility_requirements?: ("wheelchair_accessible" | "step_free")[];
  existing_commitments?: CommittedTimeBlock[];
}

export interface FeasibilityCheckRequest {
  experience_id: string;
  constraints?: TravelerConstraints;
}

/** Always honestly reported — never claims pgvector/semantic retrieval
 * happened when it fell back to keyword search. */
export type RetrievalMode = "pgvector_semantic" | "sqlite_python_semantic" | "keyword_fallback";

export interface SemanticSearchRequest {
  query?: string;
  interests?: string[];
  category_slug?: string;
  city?: string;
  locality?: string;
  location_text?: string;
  constraints?: TravelerConstraints;
  limit?: number;
}

export interface SemanticSearchItem {
  experience: ApiExperienceSummary;
  semantic_similarity: number | null;
}

export interface ExcludedReasonSummary {
  reason_counts: Record<string, number>;
  sample: { experience_id: string; status: FeasibilityStatus; reasons: string[] }[];
}

export interface SemanticSearchResponse {
  items: SemanticSearchItem[];
  retrieval_mode: RetrievalMode;
  candidate_count: number;
  feasible_count: number;
  excluded_count: number;
  excluded_summary: ExcludedReasonSummary;
}

// === Phase 7 (Ranking & Feedback) ===

export interface ApiRankedExperienceItem extends ApiExperienceSummary {
  rank: number;
  ranking_score: number;
  ranking_model_version: string;
  semantic_relevance: number;
  personalized: boolean;
  match_signals: string[];
}

export interface RecommendationRequest {
  query?: string | null;
  interests?: string[];
  constraints?: TravelerConstraints;
  top_k?: number;
}

export interface RecommendationResponse {
  items: ApiRankedExperienceItem[];
  retrieval_mode: string;
  candidate_count: number;
  feasible_count: number;
  excluded_count: number;
  excluded_summary: ExcludedReasonSummary;
  ranking_model_version: string;
  personalized: boolean;
}

export type InteractionEventType = "IMPRESSION" | "VIEW" | "SAVE" | "UNSAVE" | "COMPLETE" | "SKIP" | "RATING";

export interface RecordInteractionRequest {
  experience_id: string;
  event_type: InteractionEventType;
  rating?: number | null;
  client_event_id: string;
  rank_position?: number | null;
  recommendation_session_id?: string | null;
  occurred_at?: string | null;
  source?: string | null;
}

export interface RecordInteractionResponse {
  interaction_id: string;
  created: boolean;
  idempotent: boolean;
}

export interface TravelerAffinitySummary {
  dimension_type: string;
  dimension_key: string;
  score: number;
  confidence: number;
  interaction_count: number;
}

export interface AffinityProfileResponse {
  traveler_id: string;
  affinities: TravelerAffinitySummary[];
  personalized_since?: string | null;
}

export interface UpdatePreferenceRequest {
  preferred_category_slugs?: string[] | null;
  budget_sensitivity?: string | null;
  preferred_duration_minutes?: number | null;
  preferred_max_distance_km?: number | null;
  accessibility_requirements?: string[] | null;
}

export interface TravelerPreferenceResponse extends UpdatePreferenceRequest {
  id: string;
  traveler_id: string;
}

