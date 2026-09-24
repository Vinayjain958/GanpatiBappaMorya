"""WeatherAdapter interface — OpenWeather. Implemented in Phase 9."""

from __future__ import annotations

from typing import Any, Protocol


class WeatherAdapter(Protocol):
    async def get_current(self, lat: float, lng: float) -> dict[str, Any]: ...

    async def get_forecast(self, lat: float, lng: float) -> list[dict[str, Any]]: ...


class MockWeatherAdapter:
    async def get_current(self, lat: float, lng: float) -> dict[str, Any]:
        raise NotImplementedError("Weather is not implemented until Phase 9.")

    async def get_forecast(self, lat: float, lng: float) -> list[dict[str, Any]]:
        raise NotImplementedError("Weather is not implemented until Phase 9.")
