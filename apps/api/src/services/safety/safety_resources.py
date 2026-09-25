from typing import List
import os
import logging

from src.schemas.safety import SafetyResource
from src.services.safety.resource_adapters import OSMSafetyResourceAdapter, SeedSafetyResourceAdapter

logger = logging.getLogger(__name__)

async def get_nearby_safety_resources(lat: float, lng: float, radius_km: float, category: str) -> List[SafetyResource]:
    mode = os.environ.get("SAFETY_RESOURCES_MODE", "auto").lower()

    if mode == "live":
        adapter = OSMSafetyResourceAdapter()
        return await adapter.get_nearby_resources(lat, lng, radius_km, category)
    elif mode == "fallback":
        adapter = SeedSafetyResourceAdapter()
        return await adapter.get_nearby_resources(lat, lng, radius_km, category)
    else:
        # Auto mode
        try:
            adapter = OSMSafetyResourceAdapter()
            return await adapter.get_nearby_resources(lat, lng, radius_km, category)
        except Exception as e:
            logger.warning(f"Live safety resource adapter failed, falling back to seed adapter: {e}")
            fallback = SeedSafetyResourceAdapter()
            return await fallback.get_nearby_resources(lat, lng, radius_km, category)
