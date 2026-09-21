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
│   └── api/          ← FastAPI backend (Phase 1+)
├── docs/             ← Architecture, contracts, decisions, roadmap
├── scripts/          ← Developer utility scripts
├── tests/            ← Cross-app integration tests
├── .env.example      ← Environment variable contract (no secrets)
├── .gitignore
└── README.md
```

---

## Current Phase

**PHASE 0 — Reset, Baseline & Master Contract**

The engineering foundation, documentation, and architectural contract have been established.
No application code exists yet. Phase 1 begins next.

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
