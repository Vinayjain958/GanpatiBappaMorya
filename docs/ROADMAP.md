# LocaLens — Roadmap

> 13-phase delivery roadmap for HackCelestial 3.0 — PS-6.
> Each phase builds on the previous. Phase boundaries are intentional gates.
> Last updated: 2026-09-22

---

## Phase Dependency Graph

```
PHASE 0 (Foundation)
    │
    ▼
PHASE 1 (App Foundation & UI System)
    │
    ▼
PHASE 2 (Database, Models & Seed Data)
    │
    ▼
PHASE 3 (Auth, Roles & Provider Foundation)
    │         │
    ▼         ▼
PHASE 4   PHASE 3 also enables Provider UI
(Discovery, Catalog & OSM Layer)
    │
    ▼
PHASE 5 (Conversational AI + Gemini Live Voice)
    │
    ▼
PHASE 6 (Semantic Retrieval + Feasibility Engine)
    │
    ▼
PHASE 7 (ML Ranking + Feedback Learning)
    │
    ▼
PHASE 8 (AI Composer + Itinerary + Booking)
    │
    ▼
PHASE 9 (Real-Time Context + Events + Replanning)
    │
    ▼
PHASE 10 (Provider Intelligence & Marketplace)
    │
    ▼
PHASE 11 (Safety & Emergency)     [can start after Phase 3]
    │
    ▼
PHASE 12 (Integration, Testing, Hardening & Deployment)
```

---

## Phase Descriptions

---

### PHASE 0 — Reset, Baseline & Master Contract

**Status**: ✅ Complete

**Goal**: Establish the engineering foundation before writing any application code.

**Deliverables**:
- Repository initialized
- Full documentation suite (all `docs/` files)
- Architectural contract established (13 invariant rules + 16 ADRs)
- Environment variable contract (`.env.example`)
- Project roadmap, task backlog, and changelog
- High-level source structure
- `.gitignore`
- `README.md`

**Phase Gate**: Architecture contract approved. Documentation complete.

---

### PHASE 1 — Application Foundation & UI System

**Status**: ⏳ Not started

**Depends on**: Phase 0

**Goal**: Create working scaffolds for both apps; establish the design system.

**Deliverables**:
- `apps/web/`: Next.js 16 + App Router + TypeScript + Tailwind CSS
- `apps/api/`: FastAPI + Pydantic v2 structure
- Core layout components (shell, navigation, page templates)
- Typed API client layer (`apps/web/src/lib/api/`)
- `GET /health` endpoint
- Environment configuration validation (startup checks)
- Development server setup (both apps running concurrently)
- Responsive, accessible UI foundation

**Phase Gate**: Both dev servers run. `GET /health` returns 200. No business logic yet.

---

### PHASE 2 — Database, Models & Realistic Seed Data

**Status**: ⏳ Not started

**Depends on**: Phase 1

**Goal**: Establish the database layer and a realistic dataset for development.

**Deliverables**:
- SQLAlchemy async engine + session factory
- Alembic migration pipeline initialized
- Core models: User, Traveler, Provider, Experience, ExperienceCategory, Location
- Seed data: Mumbai/Fort/Kala Ghoda area experiences (realistic; explicitly synthetic)
- Seed script (`scripts/seed.py`)
- Model schemas validated via Pydantic

**Phase Gate**: Database migrates. Seed script runs. Experiences queryable via API.

---

### PHASE 3 — Authentication, Roles & Provider Foundation

**Status**: ⏳ Not started

**Depends on**: Phase 2

**Goal**: Secure the API and enable provider accounts and experience listings.

**Deliverables**:
- JWT authentication (access + refresh tokens)
- Role system: TRAVELER, PROVIDER, ADMIN
- User registration + login endpoints
- Provider profile creation and editing
- Experience CRUD (provider-owned)
- Availability management (provider-side)
- Route guards (frontend + API)

**Phase Gate**: A provider can register, create a listing, and set availability. Authentication enforced.

---

### PHASE 4 — Experience Discovery, Catalog & OSM Location Layer

**Status**: ⏳ Not started

**Depends on**: Phase 2, Phase 3

**Goal**: Make experiences discoverable via location and basic filters.

**Deliverables**:
- Experience catalog API (search, filter, paginate)
- `GeocodingAdapter` (Nominatim) + mock fallback
- `RoutingAdapter` (OSRM) for travel time + mock fallback
- `POIAdapter` (Overpass) for nearby POI discovery + mock fallback
- Location-radius search endpoint
- MapLibre GL JS integration (frontend map view)
- Experience detail page

**Phase Gate**: Traveler can browse experiences on a map and filter by location radius.

---

### PHASE 5 — Conversational AI + Gemini Live Voice Agent

**Status**: ⏳ Not started

**Depends on**: Phase 4

**Goal**: Enable natural language and voice as the primary traveler interaction mode.

**Deliverables**:
- `AIAdapter` (Gemini text) + mock fallback
- `TravelerContext` structured schema
- Intent extraction from natural language → `TravelerContext`
- Conversational session management (server-side)
- Ephemeral token endpoint (`POST /auth/live-token`) for Gemini Live
- Voice UI component (browser WebSocket to Gemini Live)
- Gemini function/tool calling → application tools
- Initial tool: `search_experiences`

**Phase Gate**: Traveler can describe a request in text or voice; system returns relevant experiences.

---

### PHASE 6 — Semantic Retrieval + Constraint / Feasibility Engine

**Status**: ⏳ Not started

**Depends on**: Phase 5

**Goal**: Replace keyword search with semantic retrieval. Enforce deterministic feasibility.

**Deliverables**:
- Experience embedding generation (via Gemini embedding model)
- pgvector integration (Supabase/PostgreSQL)
- Semantic search endpoint
- Keyword fallback for SQLite/dev mode
- Deterministic Feasibility Engine (all constraint types)
- Machine-readable rejection reason codes
- Full pipeline: retrieval → feasibility → filtered candidates
- Feasibility tool for Gemini: `check_feasibility`

**Phase Gate**: Infeasible experiences are never returned to the ranking stage. Reason codes returned.

---

### PHASE 7 — Real ML Ranking + Feedback Learning

**Status**: ⏳ Not started

**Depends on**: Phase 6

**Goal**: Personalize recommendations and learn from traveler behavior.

**Deliverables**:
- Interaction tracking (views, saves, completions, skips, ratings)
- TravelerPreference + TravelerAffinity models
- Personalized ranking (initially weighted scoring; later embedding-based)
- Feedback API endpoints
- Feedback loop: interactions → affinity update → ranking improvement
- Recommendation quality metrics

**Phase Gate**: Two travelers with different affinity profiles receive meaningfully different rankings.

---

### PHASE 8 — AI Experience Composer + Itinerary + Booking

**Status**: ⏳ Not started

**Depends on**: Phase 7

**Goal**: Compose multiple feasible experiences into a coherent time-ordered plan.

**Deliverables**:
- Experience composition algorithm (greedy + optimization)
- Gemini LLM narrative composer (post-feasibility only)
- Post-composition feasibility re-validation
- Itinerary object model (ItineraryItem, time slots, travel gaps)
- Save itinerary to traveler profile
- Booking request flow (request intent; no full payment)
- Composer tool for Gemini: `compose_experience`

**Phase Gate**: From a traveler context, the system produces a validated, time-ordered itinerary narrative.

---

### PHASE 9 — Real-Time Context + Events + Dynamic Replanning

**Status**: ⏳ Not started

**Depends on**: Phase 8

**Goal**: React to real-world changes and dynamically update plans.

**Deliverables**:
- `WeatherAdapter` (OpenWeather) + mock fallback
- `EventAdapter` (Ticketmaster / seed events) + fallback
- Real-time context update triggers
- Dynamic Replanning Engine
- Re-feasibility → re-rank → re-compose pipeline
- WebSocket or SSE for live plan update delivery
- Replanning tool for Gemini: `replan_experience`

**Phase Gate**: Changing traveler time or budget triggers a new valid plan within seconds.

---

### PHASE 10 — Provider Intelligence & Two-Sided Marketplace

**Status**: ⏳ Not started

**Depends on**: Phase 7, Phase 9

**Goal**: Give providers actionable demand intelligence and traveler matching.

**Deliverables**:
- Provider analytics dashboard (views, saves, bookings, reviews)
- DemandSignal aggregation
- Traveler–provider matching scores
- ProviderInsight model
- Demand trend reports
- Provider notification for qualified traveler matches

**Phase Gate**: A provider can see which traveler types are interested and what demand looks like.

---

### PHASE 11 — Safety & Emergency

**Status**: ⏳ Not started

**Depends on**: Phase 3 (auth)

**Goal**: Provide isolated safety features independent of all recommendation logic.

**Deliverables**:
- Safety module (isolated; no recommendation dependencies)
- Emergency contact management
- Nearby safety resource lookup (hospitals, police, consulates)
- Emergency alert/notification mechanism
- Safety resource API (read-only, auth-only)

**Phase Gate**: Safety features remain functional even if recommendation services are down.

---

### PHASE 12 — Full Integration, Testing, Hardening & Deployment

**Status**: ⏳ Not started

**Depends on**: All previous phases

**Goal**: Production-ready system for demo and potential post-hackathon use.

**Deliverables**:
- End-to-end integration test suite
- Performance testing (API response time under load)
- Security audit (OWASP top 10 basics)
- Vercel frontend deployment
- FastAPI containerized deployment (Docker + cloud)
- Supabase/PostgreSQL production setup
- pgvector enabled in production
- Demo environment data hardened
- All synthetic data correctly labelled
- `docs/PROJECT_STATE.md` fully updated

**Phase Gate**: Full demo scenario runs end-to-end on production infrastructure. All labels correct.
