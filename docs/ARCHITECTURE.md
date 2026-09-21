# LocaLens — Architecture

> **Current Phase: PHASE 0 — Reset, Baseline & Master Contract**
> Last updated: 2026-09-22

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
- Accepts traveler natural-language or voice input
- Uses Gemini LLM to extract structured `TravelerContext`
- Maintains conversational state across turns
- Outputs structured intent, not experience recommendations
- **Phase**: 5

### B. Experience Discovery Engine
- Retrieves candidate experiences from the catalog
- Uses semantic search (pgvector) for intent-matched retrieval
- Falls back to keyword/tag search in early phases
- Applies OSM/Overpass for real location POI data
- **Phase**: 4 (catalog), 6 (semantic retrieval)

### C. Constraint & Feasibility Engine
- **DETERMINISTIC ONLY — no LLM involvement**
- Checks: opening hours, travel time, budget, availability, group size, accessibility, itinerary conflicts, capacity, provider availability
- Returns structured feasibility verdict with machine-readable reason codes
- Rejects infeasible candidates before ranking
- Example output:
  ```json
  {
    "feasible": false,
    "reasons": [
      { "code": "BUDGET_EXCEEDED", "message": "..." },
      { "code": "OUTSIDE_OPENING_HOURS", "message": "..." }
    ]
  }
  ```
- **Phase**: 6

### D. Personalized Ranking & Matching Engine
- Operates only on feasibility-verified candidates
- Scores experiences against traveler affinity model
- Initially rule-based weighted scoring
- Eventually ML-based (traveler embedding × experience embedding)
- **Phase**: 7

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
     Context & Intent Engine
     (Gemini LLM extracts TravelerContext)
              ↓
     Experience Discovery Engine
     (retrieves candidate experiences)
              ↓
     Constraint & Feasibility Engine   ← DETERMINISTIC
     (filters infeasible candidates)
              ↓
     Personalized Ranking Engine
     (scores remaining candidates)
              ↓
     AI Experience Composer
     (composes plan from top candidates)
              ↓
     Plan Validation (Feasibility Engine again)
              ↓
     Personalized Output → Client
```

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

| Adapter | Interface | Implementation(s) |
|---|---|---|
| `AIAdapter` | `generate_text()`, `issue_live_token()` | GeminiAdapter, MockAIAdapter |
| `GeocodingAdapter` | `geocode()`, `reverse_geocode()` | NominatimAdapter, MockGeocodingAdapter |
| `RoutingAdapter` | `get_travel_time()`, `get_route()` | OSRMAdapter, MockRoutingAdapter |
| `POIAdapter` | `search_nearby()` | OverpassAdapter, MockPOIAdapter |
| `WeatherAdapter` | `get_current()`, `get_forecast()` | OpenWeatherAdapter, MockWeatherAdapter |
| `EventAdapter` | `search_events()` | TicketmasterAdapter, SeedEventAdapter |
| `MapTilesAdapter` | `get_tile_url()` | MapTilerAdapter, OSMTilesAdapter |

Each adapter implements a stable interface (Python Protocol / ABC).
The application services depend on the interface, not the implementation.

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

These will be introduced in the phases listed:

| Entity | Phase |
|---|---|
| User, Traveler, Provider | 3 |
| ProviderProfile | 3 |
| Experience, ExperienceCategory | 4 |
| ExperienceAvailability, ExperienceMedia | 4 |
| Location | 4 |
| Event | 4/9 |
| TravelerPreference, TravelerAffinity | 7 |
| Review, Rating | 7 |
| Itinerary, ItineraryItem | 8 |
| Booking | 8 |
| Interaction, SavedExperience | 7/8 |
| ProviderInsight, DemandSignal | 10 |
| WeatherSnapshot | 9 |
| ReplanningEvent | 9 |

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

## 7. AI Voice Architecture (Phase 5+)

Gemini Live API is used for real-time voice interaction.
**The browser must never hold a long-lived API key.**

### Token Flow

```
Browser                FastAPI Backend            Google Gemini
  │                         │                          │
  │── POST /auth/live-token ──►                         │
  │                         │── create ephemeral token ─►
  │                         │◄─ short-lived token ──────│
  │◄── token response ───────│                          │
  │                         │                          │
  │── WebSocket (BidiGenerateContentConstrained) ────────►
  │◄─────────────── Live audio/text stream ─────────────│
```

The ephemeral token is:
- Server-issued with constrained scope (`live_connect_constraints`)
- Short TTL (minutes)
- Used for a single Live session
- Never stored server-side after issuance

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

## 9. Security Principles

- `GEMINI_API_KEY` is never exposed to the browser
- `SUPABASE_SERVICE_ROLE_KEY` is never exposed to the browser
- Public client variables are explicitly prefixed `NEXT_PUBLIC_`
- Ephemeral tokens with minimal TTL for Gemini Live sessions
- JWT authentication for all authenticated API routes
- Role-based access: `TRAVELER`, `PROVIDER`, `ADMIN`
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
