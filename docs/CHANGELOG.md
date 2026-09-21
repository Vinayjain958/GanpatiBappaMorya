# LocaLens — Changelog

> All notable changes to LocaLens are documented here.
> Format: [Phase] [Date] — Description
> Ordered: most recent first.

---

## [Phase 0] 2026-09-22 — Foundation Established

### Added

- Repository initialized (`git init`)
- `.gitignore` — covers Python, Node.js, Next.js, SQLite, secrets, IDEs, and OS artifacts
- `.env.example` — full environment variable contract with comments; no real secrets
- `README.md` — project overview for human engineers and AI coding agents
- `docs/AI_CONTEXT.md` — primary orientation document for AI coding agents; includes invariants, stack, module ownership, and safe modification guidelines
- `docs/ARCHITECTURE.md` — full logical architecture document; all 10 capability modules, data flows, adapter contracts, database boundary, AI boundary, voice architecture, and safety isolation
- `docs/PRODUCT_CONTRACT.md` — product purpose, target users, traveler and provider experience, differentiators, capability status table, non-goals, demo strategy
- `docs/PROJECT_STATE.md` — current implementation status tracker; all phases; known risks; next milestone
- `docs/DECISIONS.md` — 16 architectural decision records (ADR-001 through ADR-016)
- `docs/TASKS.md` — phase-based high-signal task backlog for all 13 phases
- `docs/ROADMAP.md` — 13-phase roadmap with dependency graph, deliverables, and phase gates
- `docs/CHANGELOG.md` — this file
- `apps/web/` — directory placeholder for Next.js frontend (Phase 1)
- `apps/api/` — directory placeholder for FastAPI backend (Phase 1)
- `scripts/` — directory placeholder for developer utility scripts
- `tests/` — directory placeholder for cross-app integration tests

### Architectural Contract Established

- 13 non-negotiable architectural rules documented in `ARCHITECTURE.md`
- 16 architectural decision records documented in `DECISIONS.md`
- Critical invariants documented in `AI_CONTEXT.md`
- Phase 0 milestone: documentation-first, no application code

### Current State

- **Phase**: 0 — Reset, Baseline & Master Contract ✅
- **Next phase**: Phase 1 — Application Foundation & UI System
- **Application code**: None (by design)
- **Database**: None (by design)
- **External integrations**: None (by design)
