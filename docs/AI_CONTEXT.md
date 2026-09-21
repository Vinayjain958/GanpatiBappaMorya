# LocaLens — AI Agent Context File

> **READ THIS FIRST before modifying any code in this repository.**
> This file is the primary orientation document for AI coding agents.
> Last updated: 2026-09-22 | Current phase: PHASE 0

---

## What LocaLens Is

LocaLens is an AI-powered local experience discovery and matching platform built for HackCelestial 3.0 (PS-6).

It connects travelers and local experience providers through:
- Natural language and voice interaction (Gemini Live)
- Deterministic feasibility checking (not LLM-based)
- Personalized ML ranking
- AI-assisted experience composition
- Dynamic replanning when conditions change
- Two-sided marketplace (Traveler + Provider)

The core product loop: **understand → retrieve → verify feasibility → personalize → compose → adapt → learn**

---

## Current Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, App Router | Next.js 16.x |
| Backend | Python, FastAPI, Pydantic v2 | FastAPI 0.141+ |
| ORM | SQLAlchemy (async) | 2.0.x |
| Migrations | Alembic | latest |
| Database (dev) | SQLite + aiosqlite | — |
| Database (prod) | PostgreSQL + asyncpg, Supabase | — |
| AI | Google Gemini (text + Live voice) | Gemini 2.0 |
| Maps | MapLibre GL JS, OSM, Nominatim, OSRM | — |
| Weather | OpenWeather (adapter-based) | — |
| Events | Ticketmaster adapter + seed events | — |

---

## Repository Structure

```
/
├── apps/
│   ├── web/          ← Next.js frontend (Phase 1+)
│   └── api/          ← FastAPI backend (Phase 1+)
├── docs/             ← Architecture, contracts, decisions, roadmap
│   ├── AI_CONTEXT.md          ← YOU ARE HERE
│   ├── ARCHITECTURE.md        ← Full architecture document
│   ├── PRODUCT_CONTRACT.md    ← Product purpose, users, capabilities
│   ├── PROJECT_STATE.md       ← Current implementation status
│   ├── DECISIONS.md           ← Architectural decision records
│   ├── TASKS.md               ← Phase-based task backlog
│   ├── ROADMAP.md             ← Phase roadmap
│   └── CHANGELOG.md           ← Change history
├── scripts/          ← Developer utility scripts
├── tests/            ← Cross-app integration tests
├── .env.example      ← Environment variable contract
├── .gitignore
└── README.md
```

---

## Architecture Summary

```
Traveler / Provider
      ↓
API Layer (FastAPI)
      ↓
Context & Intent Engine (Gemini LLM)
      ↓
Experience Discovery Engine
      ↓
Constraint & Feasibility Engine ← DETERMINISTIC ONLY — no LLM here
      ↓
Personalized Ranking Engine
      ↓
AI Experience Composer (Gemini LLM — post-feasibility only)
      ↓
Personalized Output
      ↓
Feedback & Learning Engine
      ↓ (on real-time changes)
Dynamic Replanning Engine → loops back to feasibility check
```

External adapters (all behind interface boundaries):
- `AIAdapter` — Gemini text generation and ephemeral Live token issuance
- `GeocodingAdapter` — Nominatim
- `RoutingAdapter` — OSRM
- `POIAdapter` — Overpass API
- `WeatherAdapter` — OpenWeather
- `EventAdapter` — Ticketmaster / seed events
- `MapTilesAdapter` — MapTiler / OSM

---

## Module Ownership

| Module | Phase | Status |
|---|---|---|
| Context & Intent Engine | 5 | PLANNED |
| Experience Discovery Engine | 4 | PLANNED |
| Constraint & Feasibility Engine | 6 | PLANNED |
| Personalized Ranking Engine | 7 | PLANNED |
| AI Experience Composer | 8 | PLANNED |
| Dynamic Replanning Engine | 9 | PLANNED |
| Feedback & Learning Engine | 7 | PLANNED |
| Provider Intelligence | 10 | PLANNED |
| Safety & Emergency Module | 11 | PLANNED |
| Authentication & Roles | 3 | PLANNED |
| Database models & migrations | 2 | PLANNED |
| UI system & design | 1 | PLANNED |
| API foundation | 1 | PLANNED |

---

## Critical Invariants — Never Violate These

### INV-1: LLM is never the final feasibility authority
The Constraint & Feasibility Engine makes all hard constraint decisions.
The LLM may summarize, explain, or assist composition — never decide feasibility.

### INV-2: Infeasible experiences are rejected before ranking
The ranking engine only receives verified-feasible candidates.

### INV-3: No business logic in React components
All business logic lives in application services on the backend.
Frontend components call APIs; they do not contain domain logic.

### INV-4: All external services behind adapter interfaces
No direct calls to Gemini, Nominatim, OSRM, OpenWeather, or any external API
from within application services or UI components.
All calls go through typed adapter interfaces.

### INV-5: GEMINI_API_KEY must never reach the browser
The FastAPI backend issues short-lived ephemeral tokens for Gemini Live sessions.
The master API key stays server-side only.

### INV-6: Database queries must be portable
No SQLite-specific syntax. All queries must work on PostgreSQL.

### INV-7: Safety module is architecturally isolated
The Safety & Emergency Module does not depend on any recommendation system component.

### INV-8: Synthetic/demo data is always labelled
Any seed or synthetic data includes explicit markers (e.g., `is_synthetic: true`).

### INV-9: No hardcoded golden demo path
Intelligence must emerge from the general architecture.
Mumbai/Fort area may be used as seed data, but logic must generalize.

### INV-10: Honest feature status
Always use: IMPLEMENTED / PARTIAL / PLANNED / NOT IMPLEMENTED.
Never mark a placeholder as IMPLEMENTED.

---

## Current Implementation Status

**Phase**: PHASE 0 — Reset, Baseline & Master Contract

**IMPLEMENTED:**
- Repository initialized
- Full documentation baseline (this file + all docs/)
- Architectural contract
- Environment variable contract (.env.example)
- .gitignore
- README.md

**PARTIAL:**
- (nothing yet)

**PLANNED:**
- Everything else (see docs/ROADMAP.md)

**NOT IMPLEMENTED:**
- All application code (Phase 1+)

---

## Current Known Limitations

- No application code exists
- No database schema exists
- No API endpoints exist
- No frontend exists
- All AI, map, weather, and event features are deferred to their respective phases

---

## How to Safely Modify This Repository

### Before any change:
1. Check `docs/PROJECT_STATE.md` for current phase status
2. Confirm the change belongs to the current or an already-started phase
3. Check `docs/DECISIONS.md` to ensure you are not contradicting a recorded decision

### When adding a new module:
1. Define its interface (Python Protocol or TypeScript interface) first
2. Implement the concrete class behind that interface
3. Create a mock/fallback implementation for development
4. Register the adapter/service in the dependency injection layer
5. Update `docs/PROJECT_STATE.md` status

### When modifying the database:
1. Never edit existing Alembic migration files
2. Always create a new migration: `alembic revision --autogenerate -m "description"`
3. Ensure models use standard SQLAlchemy types — no SQLite-only types

### When working with AI/Gemini:
1. All Gemini calls go through `AIAdapter` interface
2. Never put `GEMINI_API_KEY` in frontend code
3. For Live voice: use the ephemeral token endpoint (`POST /auth/live-token`)
4. Never trust LLM output for feasibility decisions

### When adding a new experience:
1. Include: `is_synthetic: true/false`
2. Include: opening hours, capacity, accessibility info (even if null initially)
3. Ensure experience has at least one location coordinate

### When adding external API calls:
1. Create or implement the appropriate adapter interface
2. Add a mock fallback for when the API key is absent
3. Add the API key to `.env.example` with a comment
4. Never hardcode API URLs — use configuration

---

## Future Gemini Live Tool Contract (Phase 5+)

The voice agent will call application tools — not invent results.

Planned tools (NOT implemented yet):
- `get_current_context` — retrieves traveler's current structured context
- `search_experiences` — calls the discovery engine
- `check_feasibility` — calls the feasibility engine
- `get_route` — calls the routing adapter
- `get_weather` — calls the weather adapter
- `get_events` — calls the event adapter
- `compose_experience` — calls the composer engine
- `replan_experience` — calls the replanning engine
- `save_experience` — saves to traveler's list
- `create_booking_request` — initiates booking flow

These tools are defined here for architectural awareness.
Do not implement them until Phase 5.
