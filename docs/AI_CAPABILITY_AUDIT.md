# AI Capability Audit

This document is a factual inventory of every traveler-facing capability
that exists in the LocaLens repository today, produced by direct code
inspection (not aspiration). It is the input to any future work that
extends the AI agent into a natural-language control layer over the
existing product — see `docs/AI_CAPABILITY_MATRIX.md` for the condensed
per-capability summary table.

**Ground rule:** nothing in this document is invented. Where a
traveler-facing surface exists in the UI without a working backend, it is
labeled `UI-ONLY / NOT AI-AVAILABLE` and no tool should be built for it.

---

## 1. Frontend routes (traveler-facing)

| Route | File | What it does |
|---|---|---|
| `/discover` | `apps/web/app/discover/page.tsx` → `DiscoverExperience.tsx` | Keyword/filter experience browser. The `ConversationalDiscoveryInput` component accepts text/voice, but the visible result list always comes from `GET /api/v1/experiences` (plain keyword/filter) — never from semantic search or recommendations, regardless of whether the query came from typing or from the AI input. |
| `/discover/[id]` | `apps/web/app/discover/[id]/page.tsx` | Experience detail (server-fetched `GET /api/v1/experiences/{id}`), renders reviews + `WriteReviewForm`. |
| `/trip` | `apps/web/app/trip/page.tsx` | Traveler-only. Itinerary composer + list (`GET /api/v1/itineraries`). |
| `/trip/[id]` | `apps/web/app/trip/[id]/page.tsx` | Traveler-only. Single itinerary detail (`GET /api/v1/itineraries/{id}`), 404 if not owned. |
| `/saved` | `apps/web/app/saved/page.tsx` | **UI-ONLY / NOT AI-AVAILABLE.** Static empty state referencing a bookmark icon that does not exist anywhere in `ExperienceCard`. No backend model, repository, or endpoint. |
| `/safety` | `apps/web/app/safety/page.tsx` | Real: `EmergencyButton` + `SafetyDashboard`, backend-integrated. |
| `/safety/emergency` | `apps/web/app/safety/emergency/page.tsx` | Static, real `tel:` links for India emergency numbers. Two features explicitly marked **not implemented** in the UI copy itself: live emergency-service integration, and location sharing with emergency contacts (button disabled). |
| `/login`, `/register` | `apps/web/app/login/page.tsx`, `register/page.tsx` | Real, backed by `/api/v1/auth/*`. |
| `/provider/*` | `apps/web/app/provider/**` | Provider-facing, not traveler-facing — out of scope for a traveler AI agent. |

## 2. Backend API endpoints

Auth column: `none` = unauthenticated, `CurrentUser` = any logged-in
user, `require_traveler` = must have a traveler profile, `CurrentProvider`
= provider-only (excluded below as not traveler-facing).

### auth.py
| Route | Auth | Mutates? | Service |
|---|---|---|---|
| `POST /auth/register` | none | yes | `auth_service.register_user` |
| `POST /auth/login` | none | yes (session) | `auth_service.authenticate_user` |
| `POST /auth/refresh` | cookie | yes | — |
| `POST /auth/logout` | cookie | yes | — |
| `GET /auth/me` | CurrentUser | no | — |
| `POST /auth/live-token` | require_traveler | no | issues ephemeral Gemini Live token |

### experiences.py
| Route | Auth | Mutates? | Service |
|---|---|---|---|
| `GET /experiences` | none | no | `ExperienceDiscoveryService.search` — deterministic keyword/filter/bbox |
| `POST /experiences/semantic-search` | CurrentUser | no | `DiscoveryPipelineService.run` — semantic retrieval + feasibility gate |
| `GET /experiences/{id}` | none | no | includes reviews, rating, availability |
| `GET /experiences/{id}/reviews` | none | no | — |
| `POST /experiences/{id}/reviews` | require_traveler | **yes** | `reviews.submit_review` — real persisted review |

(`POST/PATCH/DELETE /experiences` are provider-only, excluded.)

### itineraries.py
All routes `require_traveler` + ownership (non-owned itinerary 404s, never 403).

| Route | Mutates? | Service |
|---|---|---|
| `POST /itineraries/compose` | **yes** | `compose_and_persist_itinerary` — full pipeline |
| `GET /itineraries` | no | list mine |
| `POST /itineraries/similar` | no (no persistence) | `ItinerarySimilarityService.find_similar` |
| `GET /itineraries/{id}` | no | — |
| `POST /itineraries/{id}/items` | **yes** | `add_item_to_itinerary` |
| `DELETE /itineraries/{id}` | **yes** | sets status=CANCELLED |
| `POST /itineraries/{id}/replan` | **yes** | `ReplanningService.replan_itinerary`; optimistic lock via `expected_version`, 409 on conflict |
| `GET /itineraries/{id}/updates` | no (SSE stream) | — |

### bookings.py
Request/accept/decline only — **no payment integration anywhere**; `ACCEPTED` is never rendered as "confirmed" or "booked."

| Route | Auth | Mutates? |
|---|---|---|
| `POST /itineraries/{id}/booking-requests` | require_traveler | yes — creates `REQUESTED` |
| `GET /bookings/me` | require_traveler | no |
| `POST /bookings/{id}/cancel` | require_traveler + ownership | yes |

### categories.py
`GET /categories` — none, read-only, from `CategoryRepository`.

### context.py
Both `CurrentUser`, read-only: `GET /context/weather?lat&lng`, `GET /context/events?lat&lng&radius_m`.

### feasibility.py
`POST /feasibility/check` — `CurrentUser`, read-only, **fully deterministic, no LLM** → `FeasibilityService.evaluate`.

### feedback.py
| Route | Auth | Mutates? |
|---|---|---|
| `POST /feedback/interactions` | require_traveler | yes — idempotent via `client_event_id` |
| `GET /feedback/profile/affinities` | require_traveler | no |
| `GET /feedback/metrics` | require_traveler | no |

### location.py
No auth on any route — public read-only pass-throughs to adapters:
`GET /location/search`, `GET /location/reverse`, `GET /location/nearby-pois`,
`POST /location/route`, `POST /location/travel-time-matrix`.

### recommendations.py
`POST /recommendations` — require_traveler, read-only → `DiscoveryPipelineService.run_with_ranking`.

### safety.py
| Route | Auth | Mutates? |
|---|---|---|
| `GET/POST/PATCH/DELETE /safety/emergency-contacts[/{id}]` | require_traveler | yes (CRUD) |
| `GET /safety/resources/nearby` | require_traveler | no — tiered OSM/Mapbox/seed fallback, never silently fakes data in `live` mode |
| `POST /safety/emergency-alerts` | require_traveler | yes — idempotent via `idempotency_key`, dispatched via `alert_adapters` |
| `GET /safety/emergency-alerts[/{id}]` | require_traveler | no |
| `POST /safety/emergency-alerts/{id}/cancel` | require_traveler | yes |

### conversation.py
See §4.

## 3. Backend services (one-line summaries)

- **discovery.py** — `ExperienceDiscoveryService`: deterministic keyword/filter/bbox+haversine search. Explicitly not AI/ranking.
- **discovery_pipeline.py** — `DiscoveryPipelineService`: semantic retrieval → deterministic feasibility gate; only `FEASIBLE` items ever returned.
- **semantic_retrieval.py** — embedding-based candidate retrieval backing the pipeline above.
- **feasibility.py** — `FeasibilityService`: 100% deterministic budget/duration/distance/hours/availability/capacity/accessibility checks. `UNKNOWN` never becomes `FEASIBLE`.
- **compose_itinerary.py** — orchestrates RETRIEVAL→FEASIBILITY→RANKING→COMPOSITION→VALIDATION→ROUTES→NARRATIVE→persist; single source of ordering truth for both REST compose and the AI `compose_experience` tool.
- **experience_composer.py** — deterministic greedy + local-improvement scheduling into a chronological, travel-aware plan.
- **itinerary_validator.py** — mandatory deterministic post-composition validation, no LLM.
- **itinerary_narrator.py** — Gemini-generated narrative text over already-validated facts only; deterministic template fallback on any Gemini failure.
- **itinerary_routes.py** — persists route-leg snapshots (OSRM or haversine estimate) after the final sequence is decided.
- **itinerary_similarity.py** — pure DB read/arithmetic "similar plans" lookup; no persistence, no ML.
- **replanning.py** — `ReplanningService`: deterministic replan algorithm, reused identically by manual REST replan, the AI `replan_experience` tool, and automatic context-driven replanning.
- **ranking.py** — applies traveler affinities/preferences to rank feasible candidates.
- **affinity.py** — updates/reads traveler category affinities from interaction feedback.
- **reviews.py** — `submit_review`: persists a real, server-attributed review; immediately recomputes aggregate rating.
- **safety/*** — nearby resource lookup (tiered fallback), emergency contacts CRUD, idempotent emergency alert creation + dispatch.
- **conversation.py** (service) — text-turn orchestration: exactly one Gemini call per turn for structured `TravelerContext` extraction only; routes to keyword search or the semantic+feasibility pipeline depending on extracted constraints; the assistant's reply text is always a deterministic template, never free-form LLM commentary.
- **ai_tools.py** — the four existing Gemini/voice tool implementations (§4).
- **context_monitor.py / context_impact.py / weather_impact.py** — automatic context-driven replanning triggers.

No traveler-submitted-experience/contribution service exists anywhere (§8).

## 4. Current AI / conversation layer

### `POST/GET /conversations*` (`apps/api/src/api/v1/conversation.py`)
| Route | Auth | Mutates? |
|---|---|---|
| `POST /conversations` | CurrentUser | yes — creates `ConversationSession(mode="text")` |
| `POST /conversations/{id}/messages` | CurrentUser + ownership | yes — persists messages, one Gemini call per turn |
| `GET /conversations/{id}` | CurrentUser + ownership | no |
| `POST /conversations/{id}/tool-calls` | CurrentUser + ownership | yes — **the voice-path bridge** |

The tool-calls route has an explicit allowlist,
`_KNOWN_TOOLS = {"search_experiences", "check_feasibility", "compose_experience", "replan_experience"}`
— any other name is rejected with 422. `traveler_id` is always
server-derived from the authenticated user, never trusted from the
client.

### Existing tool declarations (`apps/api/src/services/ai_tools.py`)

1. **`search_experiences`** — params: `q, category_slug, city, locality, min_price, max_price, min_duration_minutes, max_duration_minutes, sort, limit` (all optional). Calls `DiscoveryPipelineService` (ranked if a traveler is known, unranked otherwise).
2. **`check_feasibility`** — required `experience_id`; optional `budget_max, available_duration_minutes, party_size, max_travel_time_minutes, max_distance_km, origin_lat, origin_lng, accessibility_requirements[]`. Calls the same `FeasibilityService.evaluate` that backs `POST /feasibility/check`.
3. **`compose_experience`** — required `itinerary_date, start_time, end_time`; optional `experience_ids[], max_experiences, max_budget, pace, must_include_ids[], exclude_ids[]`. Validates any `experience_ids` against the conversation's own `last_search_candidates` cache (never trusts Gemini-supplied ids blindly), then calls the same `compose_and_persist_itinerary` used by the REST endpoint.
4. **`replan_experience`** — required `itinerary_id, requested_change`; optional `affected_experience_id, new_start_time, new_end_time, new_max_budget, new_party_size`. Delegates to the same `ReplanningService` as the manual REST replan route.

### `apps/api/src/adapters/ai.py`
- `MockAIAdapter` — deterministic keyword-extraction fallback for `TravelerContext` only. `issue_live_token()` always raises `AdapterUnavailableError` — **voice is never faked** when unconfigured.
- `GeminiAIAdapter` — real `google-genai` SDK.
  - "Text conversation" = exactly one structured-output `generate_content` call per turn (schema = `TravelerContext`) — the only LLM call on the text path.
  - "Gemini Live voice" = `issue_live_token()` creates an ephemeral, scope-locked token (`lock_additional_fields=["tools", "system_instruction"]`) with all four tool declarations and a locked system instruction; the Live session itself runs browser↔Google directly — the backend never sees the audio stream, only token issuance and the tool-call bridge.

### Frontend voice bridge — **known gap**
- `apps/web/hooks/useVoiceAgent.ts` composes mic capture + `GeminiLiveClient`; never auto-connects; any failure lands in `ERROR`, never a faked `CONNECTED`.
- `apps/web/lib/voice/geminiLiveClient.ts::handleToolCalls` **only actually dispatches `search_experiences`** — any `check_feasibility`, `compose_experience`, or `replan_experience` tool_call arriving from Gemini Live today gets `{error: "Unknown tool"}` from the browser, even though the Live token's system instruction and declarations promise all four. **This is a frontend-only gap** — the backend fully supports all four over the same `/tool-calls` route already used by voice.

### The internal debug string
`apps/web/app/discover/DiscoverExperience.tsx:117-123`:
```
Showing results shaped by: "{discoveryState.q}"
(keyword + filter matching — no AI retrieval yet)
```
This is accurate today — `/discover`'s result grid always comes from
plain `GET /api/v1/experiences`, never from semantic search or
recommendations, regardless of whether the query text came from typing
or the AI input. It is internal implementation disclosure and must not
remain in the traveler-facing UI in its current form (see decision to
remove it, tracked separately).

## 5. Saved experiences

**Does not exist as a real feature — UI-ONLY / NOT AI-AVAILABLE.**
`/saved` is a static empty state referencing a bookmark icon that exists
nowhere in `ExperienceCard`. No `localStorage` persistence, no backend
model/repository/endpoint. ("Saved" elsewhere in the codebase refers to
**saved itineraries** — the real, DB-backed `/trip` list — a different,
unrelated concept.)

## 6. Reviews

Real, fully implemented: `WriteReviewForm` → `POST /experiences/{id}/reviews`
→ `reviews.submit_review`. Author display name is server-derived from the
email local-part (never exposes raw email). Always `is_synthetic=False`,
`source_type="user_submitted"`. Aggregate rating is recomputed immediately
from all review rows.

## 7. Safety

Mostly real:
- **Emergency contacts CRUD** — fully real (`EmergencyContact` model).
- **Nearby safety resources** — fully real, tiered live→fallback, never silently substitutes fake data in `live` mode.
- **Emergency alerts** — fully real, idempotent, dispatched via `alert_adapters` (in-app or webhook).
- **`/safety/emergency`** — phone numbers are real/static (`tel:` links); live emergency-service integration and location sharing with contacts are explicitly marked **not implemented** in the UI copy itself.

## 8. Traveler contribution (adding a new local place)

**Does not exist anywhere**, backend or frontend — confirmed by
exhaustive search of both `apps/api/src` and `apps/web` for
"contribut"/"submit_experience"/equivalent patterns. The only
experience-creation path (`POST /experiences`) is provider-only.

## 9. `ComposeItineraryRequest` schema (`apps/api/src/schemas/itinerary.py`)

Top-level (all `extra="forbid"`):

| Field | Required? | Purpose |
|---|---|---|
| `query` | optional | free-text search intent |
| `interests` | optional | interest tags |
| `category_slugs` | optional | must be from the 20 real slugs (§10) |
| `itinerary_date` | **required** | day of the plan |
| `start_time` | **required** | plan window start |
| `end_time` | **required** | plan window end, must be `> start_time` |
| `max_experiences` | optional (1–20) | stop count cap |
| `max_budget` | optional | total budget ceiling |
| `pace` | optional, default `balanced` | relaxed / balanced / packed |
| `origin_lat` / `origin_lng` | optional | must be given together |
| `travel_mode` | optional, default `driving` | driving / walking / cycling |
| `party_size` | optional (1–50) | must match `planning.group_size` if both given |
| `accessibility_requirements` | optional | `wheelchair_accessible`, `step_free` |
| `city` / `locality` | optional | destination filters |
| `planning` | optional | nested `ItineraryPlanningContext` |

`traveler_id` is never a field — always server-derived from the
authenticated user.

**`ItineraryPlanningContext`** (nested, `extra="forbid"`):

| Field | Required? | Purpose |
|---|---|---|
| `group_size` | **required** (1–50) | party size |
| `participants` | optional | must contain *exactly* `group_size` entries with unique sequential `sequence` |
| `start_location_label` | optional | human-readable label (coords travel via top-level `origin_lat/lng`) |
| `is_discoverable` | optional, default `false` | opt in to anonymized "similar plan" sharing |

**`ParticipantInput`** (nested): `sequence` (required), `age_years`
(required — age-band derivation only, never a ranking signal), `gender`
(optional — context only, never a ranking signal). No name/contact
fields, by explicit data-minimization design.

`SimilarItinerariesRequest` is a related, read-only, non-persisting
request: `planning` is **required** there (unlike compose), and at least
one of `city`/`locality` is required; it deliberately has no start-location
coordinates.

## 10. Category slugs (`apps/api/src/core/category_map.py`)

The real, verified set of 20:

`food-drink`, `street-food`, `cafes`, `culture-heritage`, `art-galleries`,
`museums`, `workshops`, `crafts`, `shopping-markets`, `outdoors`,
`adventure`, `photography`, `family`, `nightlife`, `music`, `community`,
`hidden-gems`, `wellness`, `entertainment`, `local-experiences`.

Any AI tool that accepts a category must use exactly these slugs — never
free-form category strings.

## 11. Location / geocoding

- **Geocoding** — Nominatim-backed (`adapters/geocoding.py`), 1 req/sec self-rate-limited, no autocomplete/type-ahead by design. `GET /location/search`, `GET /location/reverse` (no auth).
- **Routing** — OSRM-backed (`adapters/routing.py`), rate-limited, restricted profile allowlist. `POST /location/route`, `POST /location/travel-time-matrix` (no auth). Also used internally by discovery, feasibility, itinerary composition/routes, and replanning.
- **"Near me"/radius** — `GET /experiences?lat&lng&radius_km` (bbox+haversine, not PostGIS), `GET /safety/resources/nearby?lat&lng&radius_km`, `GET /context/events?lat&lng&radius_m`.
- **Nearby POIs** (non-catalog OSM points) — `adapters/poi.py` (Overpass), `GET /location/nearby-pois`; explicitly never auto-promoted into catalog `Experience` rows.

All external location calls funnel exclusively through these adapters.

---

## Key flags for any future AI-tool design

1. **Saved experiences** is a pure UI stub with zero backend — do not build an AI tool for it until a real save feature is implemented.
2. **Traveler contribution** does not exist anywhere — do not build an AI tool for it.
3. **Voice tool-call gap** — the browser Gemini Live bridge only dispatches `search_experiences` today; `check_feasibility`/`compose_experience`/`replan_experience` are backend-ready but frontend-blocked over voice. Any voice-parity work must fix `geminiLiveClient.ts::handleToolCalls`, not the backend.
4. **`/discover` never invokes AI retrieval** — the debug banner is accurate, not overstated; the visible grid is always plain keyword/filter search today.
5. **Safety emergency page** — phone numbers are real; live integrations and location-sharing are explicitly unimplemented, not silently faked.
6. **Bookings are request-only** — never describe an `ACCEPTED` booking as "confirmed" or "booked" in any AI-facing copy; there is no payment integration.
