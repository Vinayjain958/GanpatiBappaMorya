"""EventAdapter interface — Ticketmaster / seed events. Implemented in Phase 9."""

from __future__ import annotations

from typing import Any, Protocol


class EventAdapter(Protocol):
    async def search_events(
        self, lat: float, lng: float, radius_m: int
    ) -> list[dict[str, Any]]: ...


class SeedEventAdapter:
    async def search_events(self, lat: float, lng: float, radius_m: int) -> list[dict[str, Any]]:
        raise NotImplementedError("Event discovery is not implemented until Phase 9.")
