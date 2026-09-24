# LocaLens — Architecture

> **Current Phase: PHASE 5 — Conversational AI + Gemini Live Voice Agent**
> Last updated: 2026-09-23

---

## 1. System Overview

LocaLens is a two-sided platform connecting travelers and local experience providers through AI-assisted discovery, deterministic feasibility checking, personalized ranking, and dynamic plan composition.

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENTS                               │
│  Traveler Web App (Next.js)  │  Provider Web App (Next.js)   │
└───────────────────┬──────────────────────┬───────────────────┘
                    │                      │
                    ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    API GATEWAY / LAYER                        │
│                    FastAPI (Python)                           │
│               Typed routes · Pydantic models                  │
│              JWT authentication · Role-based access          │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────────────────┐
        ▼           ▼                       ▼
┌───────────┐ ┌───────────┐         ┌────────────────┐
│ CONTEXT & │ │EXPERIENCE │         │   SAFETY &     │
│  INTENT   │ │DISCOVERY  │         │  EMERGENCY     │
│  ENGINE   │ │  ENGINE   │         │   MODULE       │
└─────┬─────┘ └─────┬─────┘         │  (ISOLATED)    │
      │             │               └────────────────┘
      ▼             ▼
┌──────────────────────────────┐
│   CONSTRAINT & FEASIBILITY   │ ◄── DETERMINISTIC ONLY
│         ENGINE               │     No LLM here
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  PERSONALIZED RANKING &      │
│    MATCHING ENGINE           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    AI EXPERIENCE COMPOSER    │ ◄── LLM-assisted composition
│    (Gemini LLM)              │     Post-feasibility only
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  PERSONALIZED OUTPUT         │
│  (Itinerary / Plan)          │
└──────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌─────────────┐ ┌────────────────────┐
│  FEEDBACK & │ │  DYNAMIC REPLANNING│
│  LEARNING   │ │  ENGINE            │
│  ENGINE     │ └────────────────────┘
└─────────────┘
```

---

## 2. Logical Capability Modules

### A. Conversation & Context Engine
- Accepts traveler natural-language (text) or voice (Gemini Live) input
- Uses Gemini LLM to extract structured `TravelerContext`
- Maintains conversational state across turns (bounded recent-history window)
- Outputs structured intent, not experience recommendations — retrieval via
  `search_experiences` (Phase 4/5) or the full semantic+feasibility pipeline (Phase 6, when the
  extracted context carries a hard constraint)
- **Phase**: 5 — IMPLEMENTED (understand + retrieve); Phase 6 extended `TravelerContext` with
  optional feasibility-oriented fields and wired hard-constraint turns to the Phase 6 pipeline;
  personalization is Phase 7 — this engine does not do that

### B. Experience Discovery Engine
- Retrieves candidate experiences from the catalog
- Uses semantic search (pgvector on PostgreSQL, Python cosine similarity on SQLite) for
  intent-matched retrieval
- Falls back to keyword/tag search when embeddings are unavailable/disabled
- Applies OSM/Overpass for real location POI data
- **Phase**: 4 (catalog + keyword search) — IMPLEMENTED; 6 (semantic retrieval,
  `SemanticRetrievalService`) — IMPLEMENTED on SQLite (`sqlite_python_semantic` +
  `keyword_fallback` modes verified), pgvector path (`pgvector_semantic` mode) implemented but
  **NOT VERIFIED live — no PostgreSQL instance available**

### C. Constraint & Feasibility Engine
- **DETERMINISTIC ONLY — no LLM involvement**
- Checks: opening hours, travel time, budget, availability, group size, accessibility, itinerary conflicts, capacity, distance, duration, total time, active status
- Returns a tri-state (FEASIBLE / INFEASIBLE / UNKNOWN) verdict with machine-readable reason
  codes — UNKNOWN (required data missing) can never be upgraded to FEASIBLE
- Rejects infeasible/unknown candidates before ranking — `DiscoveryPipelineService` only ever
  returns FEASIBLE candidates in its result set
- Example output:
  ```json
  {
    "experience_id": "...",
    "status": "INFEASIBLE",
    "reasons": [
      { "code": "BUDGET_EXCEEDED", "message": "...", "blocking": true, "evidence": {} },
      { "code": "OPENING_HOURS_CONFLICT", "message": "...", "blocking": true, "evidence": {} }
    ]
  }
  ```
- **Phase**: 6 — IMPLEMENTED (`src/services/feasibility.py`, `src/services/discovery_pipeline.py`)

### D. Personalized Ranking & Matching Engine
- Operates only on feasibility-verified candidates (Phase 6's pipeline output is the intended
  Phase 7 input — Phase 6 itself does not rank)
- Scores experiences against traveler affinity model
- Initially rule-based weighted scoring
- Eventually ML-based (traveler embedding × experience embedding)
- **Phase**: 7 — NOT STARTED

### E. AI Experience Composer
- Combines ranked, feasible experiences into a coherent time-ordered plan
- Uses Gemini LLM for narrative description, transition language, timing suggestions
- The LLM does NOT decide feasibility during composition
- Composition is validated again by the feasibility engine post-assembly
- **Phase**: 8

### F. Personalized Experience Output
- Produces final structured + narrative output (itinerary object)
- Includes: time slots, travel directions, estimated costs, explanations
- **Phase**: 8

### G. Dynamic Replanning Engine
- Triggered by: time change, budget change, experience unavailability, weather change, location change, preference change
- Re-evaluates feasibility of existing plan items
- Retrieves alternatives if needed
- Re-composes a revised plan
- **Phase**: 9

### H. Feedback & Learning Engine
- Captures: views, saves, bookings, completions, ratings, reviews, skip signals
- Trains/updates traveler affinity model
- Feeds demand signals to provider intelligence
- **Phase**: 7

### I. Provider Intelligence
- Aggregates: views, saves, bookings, reviews per experience
- Produces demand trend signals (which traveler types, times, budgets)
- Surfaces actionable insights to the provider dashboard
- **Phase**: 10

### J. Safety & Emergency Module
- **Fully isolated from all recommendation systems**
- Does NOT depend on: discovery, ranking, composer, provider data, preference model
- Access: authenticated traveler identity, emergency configuration
- Capabilities: emergency contacts, nearby safety resources, alert mechanisms
- **Phase**: 11

---

## 3. Data Flow

### Request Flow (Happy Path)

```
USER NATURAL LANGUAGE / VOICE INPUT
              ↓
     Context & Intent Engine                          [Phase 5 — IMPLEMENTED]
     (Gemini LLM extracts TravelerContext)
              ↓
     Semantic Retrieval                                [Phase 6 — IMPLEMENTED]
     (SemanticRetrievalService: embed query → candidate
      pool; SAFE pre-filters only — status/category/city;
      SQLite Python cosine verified, pgvector NOT VERIFIED
      live, keyword_fallback when embeddings unavailable)
              ↓
     Deterministic Feasibility Engine   ← DETERMINISTIC  [Phase 6 — IMPLEMENTED]
     (FeasibilityService: tri-state verdict per candidate;
      only FEASIBLE candidates survive; UNKNOWN never
      becomes FEASIBLE; DiscoveryPipelineService is the
      hard gate — this is the CURRENT END of the pipeline)
              ↓
     [ Personalized Ranking Engine — Phase 7, NOT IMPLEMENTED ]
     (would score the FEASIBLE candidate pool; does not
      exist yet — Phase 6's pipeline returns candidates
      unranked)
              ↓
     [ AI Experience Composer — Phase 8, NOT IMPLEMENTED ]
              ↓
     [ Plan Validation (Feasibility Engine again) — Phase 8 ]
              ↓
     [ Personalized Output → Client — Phase 8 ]
```

Phase 6 concretely implements the first two deterministic stages above
(`src/services/semantic_retrieval.py`, `src/services/feasibility.py`,
wired together by `src/services/discovery_pipeline.py`) and stops there
by design — ranking, composition, and plan validation remain explicitly
out of scope until Phases 7–8.

### Dynamic Replanning Flow

```
REAL-TIME CHANGE EVENT
(time / budget / availability / weather / location)
              ↓
     Dynamic Replanning Engine
              ↓
     Re-check Feasibility (Deterministic)
              ↓
     Re-rank (if needed)
              ↓
     Re-compose (AI Composer)
              ↓
     Updated Plan → Client
```

### Provider Flow

```
PROVIDER INPUT (profile, experience data, availability)
              ↓
     Provider Profile & Catalog Service
              ↓
     Discovery + Matching (traveler exposure)
              ↓
     Interaction Tracking (views / saves / bookings / reviews)
              ↓
     Provider Intelligence (aggregated insights)
              ↓
     Provider Dashboard
```

---

## 4. External Service Adapters

All external services are accessed through adapter interfaces.
This enables:
- Swapping providers without changing application logic
- Development fallbacks when credentials are absent
- Easy testing via mock adapters

| Adapter | Interface | Implementation(s) | Status |
|---|---|---|---|
| `AIAdapter` | `generate_text()`, `issue_live_token()` | `GeminiAIAdapter`, `MockAIAdapter` | IMPLEMENTED (Phase 5) |
| `GeocodingAdapter` | `search()`, `reverse()` | `NominatimGeocodingAdapter`, `MockGeocodingAdapter` | IMPLEMENTED (Phase 4) |
| `RoutingAdapter` | `get_route()`, `get_travel_time_matrix()` | `OSRMRoutingAdapter`, `MockRoutingAdapter` | IMPLEMENTED (Phase 4) |
| `POIAdapter` | `search_nearby()` | `OverpassPOIAdapter`, `MockPOIAdapter` | IMPLEMENTED (Phase 4) |
| `WeatherAdapter` | `get_current()`, `get_forecast()` | OpenWeatherAdapter, MockWeatherAdapter | PLANNED (Phase 9) |
| `EventAdapter` | `search_events()` | TicketmasterAdapter, SeedEventAdapter | PLANNED (Phase 9) |
| `MapTilesAdapter` | n/a — superseded | Style URL config (`NEXT_PUBLIC_MAP_STYLE_URL`, OpenFreeMap default) | IMPLEMENTED (Phase 4, simplified — see below |

Each adapter implements a stable interface (Python Protocol / ABC).
The application services depend on the interface, not the implementation.
Live Phase 4 adapters are rate-limited (`IntervalRateLimiter`) and
TTL-cached (`TTLCache[T]`) per-service (`apps/api/src/core/{rate_limit,cache}.py`);
`LOCATION_SERVICES_ENABLED=false` swaps all three to their Mock implementation
via `apps/api/src/core/location.py` (see `docs/DECISIONS.md` ADR-030/ADR-031).
Map *tile rendering* turned out not to need a swappable backend adapter the
way geocoding/routing/POI do — MapLibre GL JS fetches style/tiles directly
from a configured URL (OpenFreeMap by default), so `MapTilesAdapter` is
realized as frontend config (`apps/web/lib/config/map.ts`) rather than a
backend Protocol; see ADR-026.

---

## 4a. Data Foundation (Phase 2)

LocaLens combines open geospatial place data with locally curated
experience metadata to build the prototype catalog:

```
Overture Maps Places (open, real-world POIs, Mumbai bbox)
        ↓ DuckDB spatial/httpfs query (no full-dataset download)
Raw candidate export → normalize → deduplicate → validate
        ↓
LocaLens enrichment (estimated duration/price/tags — always marked)
        ↓
+ Synthetic demo layer (fictional providers/experiences, clearly labelled)
        ↓
Database (SQLAlchemy async models) → Experience read API → Discover UI
```

Every `Location`, `Provider`, and `Experience` row carries provenance
columns (`source_type`, `source_name`, `source_record_id`,
`source_version`, `source_license`, `source_confidence`, `is_synthetic`,
`is_enriched`) via a shared `ProvenanceMixin`. See `data/README.md` for
the full source, licensing, and attribution documentation, and
`docs/DECISIONS.md` ADR-017/ADR-018 for the rationale.

Phase 4 adds live OSM/Nominatim/Overpass/OSRM location services (geocoding,
nearby-POI discovery, routing/travel-time) behind backend adapters —
architecturally separate from the catalog above. Nominatim/Overpass results
are never ingested into the database and never become `Experience` rows;
they are transient, per-request lookups. See `data/README.md` §9 and
`docs/DECISIONS.md` ADR-022 through ADR-032.

---

## 5. Database Boundary

### Local Development

```
SQLite (async via aiosqlite)
SQLAlchemy 2.0 ORM (async session)
Alembic for migrations
```

### Production

```
PostgreSQL (async via asyncpg)
Supabase for managed hosting
pgvector extension for semantic retrieval (Phase 6+)
Same SQLAlchemy models — only the DATABASE_URL changes
```

**Rule**: No SQLite-specific syntax or behavior in model/query code.
All queries must be portable to PostgreSQL.

### Conceptual Domain Entities

| Entity | Phase | Status |
|---|---|---|
| User, Traveler | 2/3 | IMPLEMENTED (auth: register/login/JWT — Phase 3) |
| Provider | 2/3 | IMPLEMENTED (catalog + registered-account ownership; claiming still PLANNED) |
| AuthSession | 3 | IMPLEMENTED (refresh token rotation/revocation) |
| ExperienceCategory | 2 | IMPLEMENTED |
| Location | 2 | IMPLEMENTED (lat/lng only — no PostGIS/spatial types) |
| Experience | 2/3 | IMPLEMENTED (core fields + provider-owned CRUD — booking/review fields deferred) |
| ExperienceOpeningHour | 2/3 | IMPLEMENTED (provider-editable in Phase 3) |
| ExperienceAvailability | 3 | IMPLEMENTED (bookable time slots — booking/reservation logic deferred) |
| ExperienceMedia | 4 | PLANNED (no new media model added in Phase 4 — out of scope, see ROADMAP) |
| ConversationSession, ConversationMessage | 5 | IMPLEMENTED (user-owned; transcript text + structured metadata only, no audio persisted) |
| Event | 4/9 | PLANNED |
| TravelerPreference, TravelerAffinity | 7 | PLANNED |
| Review, Rating | 7 | PLANNED |
| Itinerary, ItineraryItem | 8 | PLANNED |
| Booking | 8 | PLANNED |
| Interaction, SavedExperience | 7/8 | PLANNED |
| ProviderInsight, DemandSignal | 10 | PLANNED |
| WeatherSnapshot | 9 | PLANNED |
| ReplanningEvent | 9 | PLANNED |

---

## 6. AI Boundary

### LLM Responsibilities (Gemini)
- Natural language understanding
- Intent and context extraction
- Conversational responses
- Experience narrative summarization
- Explanation of recommendations
- Composition assistance (narrative, transitions)
- Conversational follow-up

### Deterministic Service Responsibilities
- Feasibility checking (ALL hard constraints)
- Time arithmetic (travel time, duration, overlap)
- Opening hour validation
- Budget calculations
- Geographic distance calculations
- Itinerary conflict detection
- Capacity/group size validation

### ML Responsibilities (Phase 7+)
- Personalized ranking scores
- Traveler affinity vectors
- Traveler–experience matching
- Traveler–provider matching
- Demand prediction

### Optimization Responsibilities (Phase 8+)
- Experience composition selection
- Itinerary time slot allocation
- Route ordering optimization

**Critical invariant**: These responsibilities must never be merged.
A single "AI service" that handles both LLM and deterministic logic is forbidden.

---

## 7. AI Voice Architecture (Phase 5 — IMPLEMENTED)

Gemini Live API (`gemini-3.8-live`) is used for real-time voice interaction, via the official
`@google/genai` browser SDK (`ai.live.connect(...)`), not a hand-rolled WebSocket protocol.
**The browser never holds `GEMINI_API_KEY`.**

### Token Flow

```
Browser                FastAPI Backend            Google Gemini
  │                         │                          │
  │── POST /auth/live-token ──►                         │
  │                         │── auth_tokens.create() ───►
  │                         │◄─ ephemeral token ────────│
  │◄── token response ───────│                          │
  │                         │                          │
  │── ai.live.connect({apiKey: token}) ───────────────────►
  │◄─────────────── Live audio/transcript stream ───────│
  │                         │                          │
  │── (Gemini requests search_experiences) ─────────────│
  │── POST /conversations/{id}/tool-calls ─►             │
  │                         │── ExperienceDiscoveryService
  │◄── real catalog results ─│                          │
  │── session.sendToolResponse(...) ──────────────────────►
```

The ephemeral token is:
- Server-issued with constrained scope via `live_connect_constraints` — locks the token to
  `gemini_model_live`, the `search_experiences` tool declaration, and response modality, so a
  tampered client cannot redefine tools or inject a different system prompt
- Short TTL (`GEMINI_LIVE_TOKEN_TTL_SECONDS` to start a session, `GEMINI_LIVE_SESSION_TTL_SECONDS`
  once connected — Google's own defaults of 1 min / 30 min)
- Never stored server-side after issuance, never logged
- The `search_experiences` tool call itself is backend-only — the browser forwards it verbatim
  to `POST /api/v1/conversations/{id}/tool-calls`, which is the only place it actually executes
  (see docs/DECISIONS.md ADR-035/ADR-036)

---

## 8. Safety Module Isolation

The Safety & Emergency Module is architecturally isolated:

**What it may access:**
- Authenticated traveler identity (user ID, contact info)
- Emergency configuration (emergency contacts, safety resource data)

**What it must NOT access or depend on:**
- Experience discovery engine
- Ranking or scoring logic
- AI composer
- Provider intelligence
- Traveler preference model
- Provider database

**Why**: Safety must remain functional even if the recommendation system fails.
The failure of any recommendation component must never impair safety features.

---

## 8a. Authentication Architecture (Phase 3)

FastAPI is the single authentication authority end to end — no second auth
platform (NextAuth/Better Auth) sits alongside it.

```
Browser                          Next.js (client)              FastAPI
  │                                     │                           │
  │── login/register form ─────────────►│                           │
  │                                     │── POST /auth/login ──────►│
  │                                     │                           │── verify password (Argon2)
  │                                     │                           │── issue access JWT (mem-only)
  │                                     │                           │── issue refresh JWT
  │                                     │                           │── store AuthSession (hashed)
  │◄── Set-Cookie: refresh (HttpOnly) ──┼───────────────────────────│
  │                                     │◄── { access_token, user } │
  │  (access token held in JS memory only — lib/auth/tokenStore.ts) │
  │                                     │                           │
  │── subsequent API calls ────────────►│── Authorization: Bearer ─►│
  │   (cookie auto-attached)            │   credentials: "include"  │── get_current_user
  │                                     │                           │   (reloads User from DB —
  │                                     │                           │    stale role claim never
  │                                     │                           │    trusted alone)
  │                                     │                           │
  │  access token expires (~15 min) ────┼── 401 ───────────────────►│
  │                                     │── POST /auth/refresh ────►│── rotate: revoke old
  │                                     │   (cookie auto-attached)  │   AuthSession, issue new
  │◄── new refresh cookie ──────────────┼───────────────────────────│   pair; reuse of an
  │                                     │◄── new access_token ──────│   already-rotated token
  │                                     │── retries original call ─►│   revokes ALL sessions
```

Key properties (see docs/DECISIONS.md ADR-019/ADR-020/ADR-021 for the
full rationale):

- **Access token**: HS256 JWT, `JWT_ACCESS_SECRET`, ~15 min, held only in
  browser memory (`apps/web/lib/auth/tokenStore.ts`) — never
  localStorage/sessionStorage/IndexedDB.
- **Refresh token**: HS256 JWT, a *separate* `JWT_REFRESH_SECRET`, ~7 days,
  set only as an HttpOnly cookie (`__Host-`-prefixed when Secure), rotated
  on every use, never present in any JSON response.
- **`AuthSession`** table stores only `sha256(refresh_token)` — never the
  raw token — plus `revoked_at`/`replaced_by_session_id` for rotation and
  logout revocation.
- **`apps/web/proxy.ts`** performs an optimistic, presence-only cookie
  check for `/trip`, `/saved`, `/provider*` — it never decodes the cookie
  and is explicitly not the authorization boundary.
- **Ownership**: `provider_id` is always derived from the authenticated
  user server-side (`get_current_provider` in `src/core/deps.py`) and
  never accepted from a request body.
- **Provider lineages stay distinct**: catalog-imported (Overture) and
  synthetic demo providers have no `user_id` and cannot log in; only
  `source_type="registered"` providers are real accounts. Reseeding the
  Overture/synthetic catalog (`scripts/seed.py`) never touches registered
  accounts' data.

---

## 9. Security Principles

- `GEMINI_API_KEY` is never exposed to the browser — `IMPLEMENTED` (Phase 5): see §7
- `SUPABASE_SERVICE_ROLE_KEY` is never exposed to the browser
- Public client variables are explicitly prefixed `NEXT_PUBLIC_`
- Ephemeral tokens with minimal TTL for Gemini Live sessions — `IMPLEMENTED` (Phase 5)
- JWT authentication for all authenticated API routes — `IMPLEMENTED` (Phase 3): see §8a
- Role-based access: `TRAVELER`, `PROVIDER`, `ADMIN` — `IMPLEMENTED` (Phase 3)
- `POST /auth/live-token` is `require_traveler`-gated; `search_experiences` tool arguments are
  always schema-validated server-side, never trusted raw from the model — `IMPLEMENTED` (Phase 5)
- Passwords hashed with Argon2 (`pwdlib`), never logged/returned/stored in plaintext
- Access tokens never persist in browser storage; refresh tokens never reach JavaScript
- Synthetic/demo data is always explicitly labelled as synthetic

---

## 10. Implementation Status Labels

All features, modules, and capabilities must carry one of:

| Label | Meaning |
|---|---|
| `IMPLEMENTED` | Fully built and tested |
| `PARTIAL` | Some functionality exists; not complete |
| `PLANNED` | Designed; not yet started |
| `NOT IMPLEMENTED` | Explicitly out of scope or deferred |

**Rule**: A placeholder stub is NOT `IMPLEMENTED`. It is `PARTIAL` at best.
