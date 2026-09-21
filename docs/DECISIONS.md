# LocaLens — Architectural Decision Records

> This file records every significant architectural decision.
> Format: Decision → Why → Alternatives Considered → Consequences
> New decisions are appended; existing decisions are never edited (only superseded).
> Last updated: 2026-09-22

---

## ADR-001: Next.js App Router for Frontend

**Decision**: Use Next.js 16 with the App Router as the frontend framework.

**Why**:
- App Router is the current standard Next.js architecture (Pages Router is legacy)
- Server Components improve initial load performance
- TypeScript-first
- Strong ecosystem for PWA-oriented apps
- Excellent Vercel deployment integration

**Alternatives Considered**:
- Vite + React (SPA): Simpler setup, but no SSR; weaker for SEO and performance
- Remix: Mature, but smaller ecosystem and team familiarity
- SvelteKit: Excellent performance, but less team-common

**Consequences**:
- Server/Client component boundary must be understood by all frontend contributors
- Some third-party libraries require `"use client"` wrappers
- Deployment target is Vercel (or compatible Node/Docker environment)

---

## ADR-002: FastAPI Backend

**Decision**: Use FastAPI (Python) as the backend API framework.

**Why**:
- Native async support aligns with SQLAlchemy 2.0 async and Pydantic v2
- Auto-generated OpenAPI docs accelerate development
- Strong ecosystem for ML/AI integration (Python-native)
- Pydantic v2 provides fast, typed request/response validation

**Alternatives Considered**:
- Django REST Framework: Mature but synchronous-first; heavier for API-only use
- Node.js/Express: Would allow full-stack TypeScript; loses Python ML ecosystem
- Gin (Go): Fast, but no ML library advantage and unfamiliar to team

**Consequences**:
- Python is the primary backend language
- Must use `async def` routes and `AsyncSession` consistently
- ML/ranking code can be co-located with the API or extracted to a service

---

## ADR-003: SQLAlchemy 2.0 ORM

**Decision**: Use SQLAlchemy 2.0 (async) as the ORM layer.

**Why**:
- Stable, mature, production-grade ORM
- Full async support (`AsyncSession`, `create_async_engine`)
- Works with both SQLite (dev) and PostgreSQL (prod) without code changes
- Declarative models integrate cleanly with Pydantic

**Alternatives Considered**:
- Tortoise ORM: Async-native but smaller community; less PostgreSQL compatibility coverage
- Raw SQL (asyncpg): Maximum control; not worth the maintenance cost at this stage
- SQLModel: Thin wrapper over SQLAlchemy; acceptable, but adds abstraction layer with limited benefit

**Consequences**:
- All database interactions must use `AsyncSession`
- No SQLite-specific types or syntax in model definitions
- 2.0-style query API (`select()`, `scalars()`) must be used; 1.x `session.query()` is forbidden

---

## ADR-004: Alembic for Migrations

**Decision**: Use Alembic for database schema migrations.

**Why**:
- Official SQLAlchemy migration tool
- Autogenerate support from model definitions
- Version-controlled migration history

**Alternatives Considered**:
- Flyway: JVM-based; incompatible ecosystem
- Django migrations: Coupled to Django
- Manual schema scripts: No version control benefit

**Consequences**:
- Every schema change requires a new Alembic revision
- Existing migration files must never be edited
- Migration files committed to version control

---

## ADR-005: SQLite for Local Development

**Decision**: Use SQLite (via `aiosqlite`) for local development.

**Why**:
- Zero installation — available on all developer machines
- Instant setup; no Docker dependency for database
- Sufficient for development and functional testing
- `DATABASE_URL` switch is the only change needed for production

**Alternatives Considered**:
- Docker PostgreSQL from Day 1: More production-accurate; adds developer friction
- In-memory database: Fast; loses data on restart; impractical for iterative work

**Consequences**:
- Developers can run the full stack without Docker
- SQLite-specific behavior (case sensitivity, type affinity) must be avoided
- CI must run tests against PostgreSQL before production deployments

---

## ADR-006: PostgreSQL / Supabase for Production

**Decision**: Target PostgreSQL (Supabase managed) for the production database.

**Why**:
- pgvector extension required for semantic retrieval (Phase 6+)
- Supabase provides managed PostgreSQL with row-level security, auth, and storage
- Direct DATABASE_URL switch from SQLite; no SQLAlchemy model changes needed

**Alternatives Considered**:
- PlanetScale (MySQL): No pgvector support
- MongoDB: Document model less suited to relational marketplace data
- Firebase: No SQL; no pgvector; vendor lock-in

**Consequences**:
- pgvector is the target extension for semantic embeddings
- Phase 6+ assumes PostgreSQL in CI/staging
- Supabase managed auth may complement or replace custom JWT in a later phase (decision deferred)

---

## ADR-007: Google Gemini Ecosystem for AI

**Decision**: Use Google Gemini (text and Live API) as the primary AI provider.

**Why**:
- HackCelestial 3.0 alignment with Google ecosystem
- Gemini 2.0 Flash provides fast, capable reasoning
- Gemini Live API is the most mature real-time voice API available
- Function/tool calling supports structured application tool use
- Single provider reduces credential and integration complexity

**Alternatives Considered**:
- OpenAI GPT + Whisper: Strong but not hackathon-aligned; no native Live equivalent
- Anthropic Claude: Strong reasoning; no native Live voice API
- Multi-provider: Adds complexity without benefit at this stage

**Consequences**:
- `GEMINI_API_KEY` is a critical credential; must never reach the browser
- LLM provider is behind `AIAdapter` interface; can be swapped in future
- Gemini function calling format must be used for tool integration

---

## ADR-008: Gemini Live API for Voice

**Decision**: Use the Gemini Live API for real-time voice interaction.

**Why**:
- Core product differentiator: voice-first traveler input
- Gemini Live supports real-time audio streaming, turn detection, and tool calling
- `BidiGenerateContentConstrained` endpoint designed specifically for browser clients

**Alternatives Considered**:
- Whisper (STT) + TTS pipeline: Higher latency; not real-time; more integration work
- LiveKit + Gemini: Better network resilience (WebRTC); adds complexity for Phase 0-5
- ElevenLabs TTS: Output only; not full voice interaction

**Consequences**:
- Backend must issue ephemeral tokens via `POST /auth/live-token`
- Tokens must have short TTL and constrained scope
- WebSocket endpoint used by browser: `BidiGenerateContentConstrained`

---

## ADR-009: MapLibre / OpenStreetMap Ecosystem for Maps

**Decision**: Use MapLibre GL JS for rendering and the OSM ecosystem for data.

**Why**:
- MapLibre GL JS is open-source (no usage-based billing for renders)
- OpenStreetMap data is free, global, and community-maintained
- Nominatim for geocoding, Overpass for POI discovery, OSRM for routing — all free for reasonable usage
- No vendor lock-in; all services replaceable via adapter interface

**Alternatives Considered**:
- Google Maps: Significant per-request billing at scale; vendor lock-in
- Mapbox: MapLibre fork; billing model less favorable
- HERE Maps: Enterprise-focused; not developer-friendly for hackathon

**Consequences**:
- OSM/Nominatim rate limits apply; caching is required for production
- OSRM public instance has usage limits; self-hosted option for production
- MapTiler API key optional for premium tile styles (OSM tiles are fallback)
- All map service interactions go through adapter interfaces

---

## ADR-010: Adapter-Based External Integrations

**Decision**: All external service calls go through typed adapter interfaces, not direct API calls.

**Why**:
- Enables mock/fallback implementations for development without real credentials
- Application services depend on stable interfaces, not external API specifics
- Swapping providers (e.g., OpenWeather → Tomorrow.io) requires only adapter implementation change
- Testability: mock adapters enable unit testing without external dependencies

**Alternatives Considered**:
- Direct API calls with environment-guarded mocks: Works but couples code to API shape
- BFF (Backend for Frontend) layer: Too much overhead at this stage

**Consequences**:
- Every external service must have: (a) a typed interface, (b) a real implementation, (c) a mock/fallback
- Interface files live in `apps/api/adapters/` (Phase 1+)
- Mock adapters are used by default when API keys are absent

---

## ADR-011: Deterministic Feasibility Engine

**Decision**: The Constraint & Feasibility Engine is 100% deterministic. No LLM involvement.

**Why**:
- LLMs may hallucinate or be inconsistent about hard constraints (opening hours, budget math)
- Infeasible experience recommendations damage trust irrecoverably
- Deterministic logic is testable, predictable, and auditable
- Rejections can be expressed as machine-readable reason codes

**Alternatives Considered**:
- LLM-only feasibility: Fast to implement; not reliable; violates product trust
- LLM + deterministic validation: Redundant; LLM is still not needed for constraint checking

**Consequences**:
- Feasibility Engine is a standalone service with typed inputs and outputs
- No `if llm_says_feasible` anywhere in the codebase
- Rejection reasons are structured: `{ code, message }` pairs

---

## ADR-012: LLM Never Determines Feasibility

**Decision**: A direct corollary to ADR-011. The LLM output is never used to decide whether an experience is feasible.

**Why**: Same as ADR-011. Emphasized separately because this is an invariant that must survive code review.

**Consequences**:
- Any code that passes LLM output directly to the ranking engine without feasibility checking is a bug
- Code review must enforce this boundary

---

## ADR-013: Provider and Traveler as First-Class Domains

**Decision**: Provider and Traveler are distinct, equal first-class domains throughout the system.

**Why**:
- PS-6 explicitly requires both sides of the marketplace
- Provider intelligence is not an afterthought; it is a core product capability
- Traveler-only architectures commonly fail to deliver on two-sided marketplace requirements

**Alternatives Considered**:
- Traveler-first + minimal provider layer: Simpler short-term; fails PS-6 requirements
- Unified "user" with roles only: Loses semantic clarity

**Consequences**:
- Separate database models, API routes, and UI areas for Provider and Traveler
- Both domains are always considered in architecture discussions
- Provider experience listings belong to the Provider domain; matching belongs to shared infrastructure

---

## ADR-014: Safety Module is Architecturally Isolated

**Decision**: The Safety & Emergency Module has no dependencies on the recommendation system.

**Why**:
- Safety must remain functional even if the recommendation system fails
- Recommendation failures must never propagate to safety features
- Clean separation enables independent testing and compliance

**Consequences**:
- `apps/api/modules/safety/` must not import from `discovery`, `ranking`, `composer`, or `providers`
- Safety may only access: traveler identity, emergency configuration, external safety APIs
- Any future code review that introduces a dependency from Safety to Recommendation is a bug

---

## ADR-015: Synthetic/Demo Data Must Be Explicitly Labelled

**Decision**: All synthetic, generated, or demo data must carry an explicit `is_synthetic: true` marker.

**Why**:
- Presenting fabricated statistics as real-world facts is misleading
- Hackathon judges must be able to distinguish real data from demo data
- Prevents accidental production use of demo data

**Consequences**:
- Seed data scripts set `is_synthetic = True` on all generated records
- Provider intelligence dashboards display "Demo Data" labels when using synthetic data
- No synthetic records are presented as real without explicit user consent

---

## ADR-016: No Hardcoded Golden-Path Business Logic

**Decision**: The architecture must produce demo scenarios from general logic, not special-cased code.

**Why**:
- Golden-path demo code is fragile, unmaintainable, and not honest about system capability
- The constraint/ranking/composition logic should work for ANY valid input
- Judges can tell when a demo is hardcoded

**Alternatives Considered**:
- Hardcoded demo for hackathon speed: Faster initially; fails during questions; wrong technically

**Consequences**:
- Mumbai/Fort area seed data is acceptable as realistic demo seed data
- No `if location == "Fort"` special cases in business logic
- Demo scenarios emerge from: general seed data + general algorithms
