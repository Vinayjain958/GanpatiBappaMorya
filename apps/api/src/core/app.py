"""Application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.v1.router import api_v1_router
from src.core.config import get_settings
from src.core.errors import register_error_handlers
from src.core.logging import configure_logging
from src.core.startup import validate_startup


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging()
    validate_startup(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="LocaLens API",
        version="0.3.0",
        description=(
            "LocaLens backend. Authenticated endpoints use a short-lived "
            "Bearer access token (Authorization: Bearer <token>); the "
            "refresh token travels only as an HttpOnly cookie and is "
            "never part of the JSON API surface."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_v1_router)

    # Dev-grade local media store for traveler-uploaded experience photos
    # (src/adapters/media_storage.py::LocalFilesystemMediaStorage). A
    # production deployment would front this with real object storage and
    # drop this mount — see docs/DECISIONS.md ADR-058.
    media_dir = Path(settings.media_upload_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.media_public_base_url,
        StaticFiles(directory=str(media_dir)),
        name="experience-media",
    )

    return app
