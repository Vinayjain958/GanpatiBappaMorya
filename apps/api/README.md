# apps/api/

This directory will contain the **FastAPI** backend application.

**Phase**: 1 (not yet created)

**Planned stack**:
- Python 3.12+
- FastAPI 0.141+, Pydantic v2
- SQLAlchemy 2.0 (async), Alembic
- aiosqlite (dev) / asyncpg (production)

**Planned module structure** (Phase 1):
```
apps/api/
├── src/
│   ├── adapters/      ← External service adapter interfaces + implementations
│   ├── core/          ← Configuration, database engine, base classes
│   ├── modules/       ← Feature modules (discovery, feasibility, ranking, etc.)
│   │   ├── auth/
│   │   ├── traveler/
│   │   ├── provider/
│   │   ├── experiences/
│   │   ├── conversation/
│   │   ├── feasibility/
│   │   ├── ranking/
│   │   ├── composer/
│   │   ├── replanning/
│   │   ├── intelligence/
│   │   └── safety/       ← Isolated; no imports from other modules
│   └── main.py
├── alembic/
├── tests/
├── pyproject.toml
└── README.md
```

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` for details.
