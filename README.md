# LocaLens

> **HackCelestial 3.0 · PS-6 — Local & Experiences — Intelligent Local Discovery & Experience Platform**

LocaLens is an AI-powered local experience discovery and matching platform that connects the right traveler with the right experience at the right time — via natural language and voice interaction.

---

## The Problem It Solves

Most local discovery tools work like this:

> search → list results → user guesses which one is right

LocaLens works like this:

> **understand → retrieve → verify feasibility → personalize → compose → adapt → learn**

A traveler says:

> *"I have about 3 hours near Fort, I'm with two friends, we want local food and something cultural, and we don't want to spend more than ₹1500."*

LocaLens:

1. **Understands** the traveler's full context (location, time, group, budget, interests)
2. **Retrieves** candidate local experiences
3. **Checks feasibility** deterministically (opening hours, travel time, budget, availability)
4. **Ranks** experiences personalized to this specific traveler
5. **Composes** a realistic mini-itinerary from compatible experiences
6. **Adapts** instantly when conditions change (less time, budget shift, experience unavailable)
7. **Learns** from traveler behavior over time
8. **Connects** relevant travelers with local providers

---

## Architecture Direction

```
Traveler / Provider
        ↓
  API Layer (FastAPI)
        ↓
┌─────────────────────────────────────────┐
│  Context & Intent Engine (Gemini LLM)   │
│  Experience Discovery Engine            │
│  Constraint & Feasibility Engine ─────► Deterministic — no LLM shortcut
│  Personalized Ranking & Matching Engine │
│  AI Experience Composer (Gemini LLM)   │
│  Dynamic Replanning Engine             │
│  Feedback & Learning Engine            │
│  Provider Intelligence                 │
│  Safety & Emergency Module (isolated)  │
└─────────────────────────────────────────┘
        ↓
  Database (SQLite → PostgreSQL)
  External Adapters (Gemini / Maps / Weather / Events)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full architectural contract.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React, TypeScript, Tailwind CSS, App Router |
| **Backend** | Python, FastAPI 0.141+, Pydantic v2, SQLAlchemy 2.0 (async) |
| **Database** | SQLite (local dev) → PostgreSQL / Supabase (production) |
| **AI** | Google Gemini (text + Live voice), function-calling / tool use |
| **Maps** | MapLibre GL JS, OpenStreetMap, Nominatim, OSRM |
| **Weather** | OpenWeather (adapter-based) |
| **Events** | Ticketmaster adapter + seed events |

---

## Repository Structure

```
/
├── apps/
│   ├── web/          ← Next.js frontend (Phase 1+)
│   └── api/          ← FastAPI backend + database + ingestion scripts (Phase 1+)
│       ├── src/models/, src/repositories/, src/schemas/  ← database layer (Phase 2)
│       ├── alembic/                                       ← migrations (Phase 2)
│       └── scripts/    ← ingest_overture.py, synthetic_data.py, seed.py (Phase 2)
├── data/
│   ├── processed/    ← committed, curated ingestion output (small)
│   ├── raw/          ← gitignored raw Overture export
│   └── README.md     ← data source, licensing & attribution documentation
├── docs/             ← Architecture, contracts, decisions, roadmap
├── scripts/          ← Cross-repo developer utility scripts (dev.ps1/dev.sh)
├── tests/            ← Cross-app integration tests
├── .env.example      ← Environment variable contract (no secrets)
├── .gitignore
└── README.md
```

---

## Current Phase

**PHASE 6 — Semantic Retrieval + Constraint / Feasibility Engine** ✅ (real Gemini embedding
verification and live pgvector verification both pending — no API key / no PostgreSQL instance
available in this environment)

LocaLens now retrieves candidates semantically and verifies every one deterministically before
it can ever reach a traveler, on top of the Phase 5 conversational understanding layer and the
Phase 4 location-aware discovery engine (353 experiences — 288 Overture-derived + 65 labelled
synthetic — across 20 categories, 311 providers). A traveler's request is embedded and matched
against the catalog (real `pgvector` on PostgreSQL — not yet verified live; a portable Python
cosine-similarity path on SQLite — verified), then every candidate is run through a 100%
deterministic `FeasibilityService` (budget, duration, travel time/distance, opening hours,
availability, capacity, accessibility, itinerary conflicts) that returns a tri-state
FEASIBLE/INFEASIBLE/UNKNOWN verdict — the LLM is never the feasibility authority, and only
FEASIBLE candidates are ever returned to the traveler. Gemini gained a second tool,
`check_feasibility`, whose argument schema has no field for price/hours/capacity/availability,
so it cannot supply an invented fact even if it tried. `GEMINI_API_KEY` still never reaches the
browser — only a short-lived, server-locked ephemeral token. See `docs/DECISIONS.md`
ADR-040–ADR-044 for the architecture and `docs/PROJECT_STATE.md` for full status labels.
Personalized ML ranking, the AI experience composer, itinerary generation, and booking are not
implemented yet.

To try voice locally, set a real `GEMINI_API_KEY` in `.env` (see `.env.example`) — without one,
text discovery still works via a deterministic mock, and the microphone clearly shows
unavailable rather than faking a connection.

### Running locally

```bash
# Backend
cd apps/api && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
python scripts/seed.py          # reseed the catalog (uses the committed data/processed/ snapshot)
uvicorn src.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web && npm install && npm run dev
```

Or run both together: `powershell -File scripts/dev.ps1` (Windows) / `./scripts/dev.sh` (POSIX).

Then register a traveler or provider account at `/register`. To create a local ADMIN account
(never self-registrable), set `ADMIN_SEED_EMAIL`/`ADMIN_SEED_PASSWORD` in `.env` and run
`python scripts/create_admin.py` from `apps/api/`.

To re-run open-data ingestion against Overture directly (optional — requires network access
and `pip install -r requirements-ingestion.txt`):

```bash
cd apps/api && python scripts/ingest_overture.py
```

See [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) for detailed status.
See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full phase roadmap.

---

## Development Strategy

1. **Documentation-first**: All architectural decisions are recorded in `docs/` before code is written.
2. **Adapter-based integrations**: Every external service (Gemini, weather, maps, events) is hidden behind an adapter interface. Development fallbacks exist so the app runs without real credentials.
3. **Deterministic feasibility**: The LLM is never the final authority on whether an experience is feasible. A deterministic engine handles all constraint checking.
4. **Two-sided marketplace**: Traveler and Provider are both first-class domains throughout the system.
5. **Phase-gated complexity**: Features are introduced in deliberate phases. Nothing is built prematurely.

---

## Working with This Repository

### For Human Engineers

- Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) before touching the codebase.
- Record every significant decision in [`docs/DECISIONS.md`](docs/DECISIONS.md).
- Update [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) when phase status changes.
- Never merge AI/LLM logic with deterministic feasibility logic.
- No business logic inside React components.

### For AI Coding Agents

- **Start here**: Read [`docs/AI_CONTEXT.md`](docs/AI_CONTEXT.md) before any code change.
- Check [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) for current implementation status.
- Consult [`docs/DECISIONS.md`](docs/DECISIONS.md) before proposing architectural changes.
- Use status labels: `IMPLEMENTED` / `PARTIAL` / `PLANNED` / `NOT IMPLEMENTED`.
- Never mark a placeholder as implemented.
- Never put deterministic logic inside an LLM adapter.
- Never expose `GEMINI_API_KEY` in frontend/browser code.

---

## License

*Internal prototype — HackCelestial 3.0. Not for public distribution.*
