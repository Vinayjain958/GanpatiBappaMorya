# LocaLens — Task Backlog

> High-signal phase-based task backlog.
> Tasks are categorized by phase and priority.
> Low-level implementation details are tracked in GitHub Issues / sprint boards (not here).
> Last updated: 2026-09-22

---

## P0 — Reset, Baseline & Master Contract

- [x] Inspect project folder and confirm clean state
- [x] Initialize git repository
- [x] Create `.gitignore` (Python, Node, Next.js, SQLite, secrets, IDEs)
- [x] Create `.env.example` with full environment contract
- [x] Create `README.md` (human + AI agent orientation)
- [x] Create `docs/AI_CONTEXT.md` (AI agent context + invariants)
- [x] Create `docs/ARCHITECTURE.md` (full logical architecture)
- [x] Create `docs/PRODUCT_CONTRACT.md` (product purpose, users, capabilities)
- [x] Create `docs/PROJECT_STATE.md` (current implementation status)
- [x] Create `docs/DECISIONS.md` (16 architectural decision records)
- [x] Create `docs/TASKS.md` (this file)
- [x] Create `docs/ROADMAP.md` (13-phase roadmap with gates)
- [x] Create `docs/CHANGELOG.md` (initial changelog entry)
- [x] Create directory placeholders for `apps/web/`, `apps/api/`, `scripts/`, `tests/`
- [x] Verify repository structure is clean and consistent

---

## P1 — Application Foundation & UI System

> **Target**: Working dev environment with both apps running. No business logic.

### Frontend (apps/web/)
- [ ] Initialize Next.js 16 project (`npx create-next-app@latest`)
- [ ] Configure TypeScript (strict mode)
- [ ] Configure Tailwind CSS v4
- [ ] Establish color palette and design tokens
- [ ] Create root layout component (`app/layout.tsx`)
- [ ] Create shell/navigation components (header, sidebar)
- [ ] Create page templates (traveler, provider)
- [ ] Create typed API client (`src/lib/api/client.ts`)
- [ ] Configure `NEXT_PUBLIC_API_BASE_URL` environment handling
- [ ] Responsive layout foundations (mobile + desktop)
- [ ] Add Google Fonts (Inter or Outfit)
- [ ] Create `app/page.tsx` (landing page placeholder — not full UI)

### Backend (apps/api/)
- [ ] Initialize FastAPI project structure
- [ ] Configure Pydantic v2 settings (env-based config)
- [ ] Create `GET /health` endpoint
- [ ] Create CORS middleware configuration
- [ ] Create application factory (`create_app()`)
- [ ] Define project module structure (`modules/`, `adapters/`, `core/`)
- [ ] Create adapter interfaces (Python Protocol) for all external services
- [ ] Create mock implementations for all adapters
- [ ] Create environment startup validation (warn on missing optional keys; fail on required)

### Developer Experience
- [ ] Configure `pyproject.toml` / `requirements.txt` with pinned versions
- [ ] Configure `package.json` scripts for concurrent dev (`npm run dev`)
- [ ] Linting: Ruff (Python), ESLint + Prettier (TypeScript)
- [ ] Type checking: mypy or pyright (Python), `tsc --noEmit` (TypeScript)
- [ ] Add `scripts/dev.sh` or `scripts/dev.ps1` to start both apps

---

## P2 — Database, Models & Realistic Seed Data

> **Target**: Queryable database with realistic demo data.

- [ ] Configure SQLAlchemy async engine factory
- [ ] Configure Alembic (async-compatible)
- [ ] Create base model class (timestamps, UUID primary keys)
- [ ] Model: `User` (id, email, hashed_password, role, created_at)
- [ ] Model: `Traveler` (extends User; preferences, accessibility)
- [ ] Model: `Provider` (extends User; business name, description)
- [ ] Model: `Experience` (id, provider_id, title, description, category, location, pricing, capacity, accessibility, opening_hours, is_synthetic)
- [ ] Model: `ExperienceCategory` (id, name, slug)
- [ ] Model: `Location` (id, lat, lng, place_name, address, city, country)
- [ ] Generate initial Alembic migration
- [ ] Create seed script (`scripts/seed.py`)
- [ ] Seed data: 15–25 Mumbai/Fort/Kala Ghoda area experiences (synthetic; labelled)
- [ ] Seed data: 3–5 demo provider accounts (synthetic; labelled)
- [ ] Verify seed data runs clean on fresh database

---

## P3 — Authentication, Roles & Provider Foundation

> **Target**: Secure API; providers can create listings.

- [ ] JWT access + refresh token implementation
- [ ] `POST /auth/register` (traveler and provider)
- [ ] `POST /auth/login`
- [ ] `POST /auth/refresh`
- [ ] Role enum: `TRAVELER`, `PROVIDER`, `ADMIN`
- [ ] Role-based route guards (FastAPI dependency)
- [ ] `GET/PUT /providers/me` (provider profile)
- [ ] `POST /experiences` (provider creates listing)
- [ ] `PUT /experiences/{id}` (provider edits listing)
- [ ] `DELETE /experiences/{id}` (provider removes listing)
- [ ] Availability model + CRUD endpoints
- [ ] Frontend: login, register, role-based routing
- [ ] Frontend: provider dashboard shell

---

## P4 — Experience Discovery, Catalog & OSM Location Layer

> **Target**: Experiences discoverable via location + basic filters + map view.

- [ ] `GET /experiences` (search, filter, paginate, location radius)
- [ ] `GET /experiences/{id}` (detail)
- [ ] `GeocodingAdapter` interface + Nominatim implementation + mock
- [ ] `RoutingAdapter` interface + OSRM implementation + mock
- [ ] `POIAdapter` interface + Overpass implementation + mock
- [ ] Location radius search (PostGIS or haversine formula)
- [ ] MapLibre GL JS map component (frontend)
- [ ] Experience pins on map
- [ ] Experience detail page (frontend)
- [ ] Category filter UI
- [ ] Distance + travel time display

---

## P5 — Conversational AI + Gemini Live Voice Agent

> **Target**: Traveler can describe request in text or voice; system returns relevant experiences.

- [ ] `AIAdapter` interface + GeminiAdapter + MockAIAdapter
- [ ] `TravelerContext` Pydantic schema (full context model)
- [ ] Prompt template for intent extraction → `TravelerContext`
- [ ] `POST /conversation/extract-context` endpoint
- [ ] Conversational session model (server-side state)
- [ ] `POST /conversation/message` endpoint (text turn)
- [ ] `POST /auth/live-token` (ephemeral token for Gemini Live)
- [ ] Voice UI component (browser WebSocket → Gemini Live)
- [ ] Gemini function/tool calling integration
- [ ] Tool: `search_experiences` (calls discovery engine)
- [ ] End-to-end: voice input → intent extraction → experience results

---

## P6 — Semantic Retrieval + Constraint / Feasibility Engine

> **Target**: Semantic search active. Infeasible experiences never reach ranking.

- [ ] Experience embedding generation (Gemini embedding model)
- [ ] pgvector setup (Supabase / production migration)
- [ ] Semantic search endpoint
- [ ] Keyword fallback for SQLite/dev mode
- [ ] Feasibility Engine: opening hours check
- [ ] Feasibility Engine: budget check
- [ ] Feasibility Engine: travel time / distance check
- [ ] Feasibility Engine: group size / capacity check
- [ ] Feasibility Engine: accessibility check
- [ ] Feasibility Engine: itinerary conflict check
- [ ] Feasibility Engine: availability / provider availability check
- [ ] Machine-readable rejection reason codes
- [ ] Tool: `check_feasibility`
- [ ] Integration tests: verify no infeasible experience passes the filter

---

## P7 — Real ML Ranking + Feedback Learning

> **Target**: Different traveler profiles produce meaningfully different rankings.

- [ ] `Interaction` model (view, save, complete, skip, rate)
- [ ] `TravelerPreference` model
- [ ] `TravelerAffinity` model (per-category/tag affinity scores)
- [ ] Feedback API (`POST /interactions`)
- [ ] Personalized ranking algorithm (weighted scoring → later embedding-based)
- [ ] Affinity update on new feedback
- [ ] Ranking endpoint integrated into main discovery pipeline
- [ ] Quality metric: A/B ranking comparison for different profiles

---

## P8 — AI Experience Composer + Itinerary + Booking

> **Target**: Valid time-ordered itinerary narrative produced from traveler context.

- [ ] Composition algorithm (select + order + time-allocate)
- [ ] `Itinerary` model
- [ ] `ItineraryItem` model (experience, time_start, time_end, travel_gap)
- [ ] Gemini narrative composer (post-feasibility only)
- [ ] Post-composition feasibility re-validation
- [ ] `POST /itineraries` (save itinerary)
- [ ] `GET /itineraries/{id}`
- [ ] Booking request model + `POST /booking-requests`
- [ ] Tool: `compose_experience`
- [ ] Tool: `save_experience`
- [ ] Tool: `create_booking_request`
- [ ] Itinerary view UI (frontend)

---

## P9 — Real-Time Context + Events + Dynamic Replanning

> **Target**: Changing traveler context triggers a new valid plan within seconds.

- [ ] `WeatherAdapter` interface + OpenWeather implementation + mock
- [ ] `EventAdapter` interface + Ticketmaster implementation + seed fallback
- [ ] `WeatherSnapshot` model
- [ ] `Event` model
- [ ] `ReplanningEvent` model (trigger + reason)
- [ ] Dynamic Replanning Engine
- [ ] Re-feasibility → re-rank → re-compose pipeline
- [ ] WebSocket or SSE endpoint for live plan updates
- [ ] Tool: `replan_experience`
- [ ] Tool: `get_weather`
- [ ] Tool: `get_events`
- [ ] Demo scenario: time reduction → replan
- [ ] Demo scenario: experience unavailable → replan

---

## P10 — Provider Intelligence & Two-Sided Marketplace

> **Target**: Provider can see demand intelligence and traveler matches.

- [ ] `DemandSignal` aggregation service
- [ ] `ProviderInsight` model
- [ ] Provider analytics API (`GET /providers/me/insights`)
- [ ] Traveler–provider matching score
- [ ] Provider notification: qualified traveler match
- [ ] Provider analytics dashboard UI
- [ ] Demand trend charts (views, saves, bookings over time)
- [ ] "Synthetic Data" label enforcement in UI

---

## P11 — Safety & Emergency

> **Target**: Safety features functional independently of recommendation system.

- [ ] Safety module isolation verified (no recommendation imports)
- [ ] Emergency contact model + CRUD
- [ ] Nearby safety resources endpoint (hospitals, police, consulates)
- [ ] Emergency alert mechanism (notification or webhook)
- [ ] Safety UI component (accessible, always-visible trigger)
- [ ] Safety API: auth-only, no recommendation dependency

---

## P12 — Full Integration, Testing, Hardening & Deployment

> **Target**: Production-ready demo on real infrastructure.

- [ ] End-to-end integration test suite (Playwright for frontend, pytest for API)
- [ ] API performance testing (response time < 2s for all demo endpoints)
- [ ] OWASP top 10 basic security review
- [ ] Vercel frontend deployment
- [ ] Docker containerization for FastAPI
- [ ] Cloud/container deployment for FastAPI (Render/Railway/GCP)
- [ ] Supabase production database setup
- [ ] pgvector enabled in production
- [ ] All `.env` variables configured in deployment platform
- [ ] Demo environment seed data loaded
- [ ] Synthetic data labels verified in production UI
- [ ] `docs/PROJECT_STATE.md` fully updated to IMPLEMENTED
- [ ] Final demo rehearsal and timing
