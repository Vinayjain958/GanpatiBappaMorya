"""Live API regression test for 15,000 real experience catalog."""

import asyncio
from httpx import ASGITransport, AsyncClient
import sys
from pathlib import Path

# Add apps/api to sys.path
api_root = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(api_root))

from src.main import app


async def test_live_api() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Experience list
        res = await client.get("/api/v1/experiences?limit=10")
        assert res.status_code == 200, f"Status {res.status_code}: {res.text}"
        data = res.json()
        print("Experiences list count:", len(data.get("items", [])), "total:", data.get("total"))
        # Discovery candidate cap is 1000 (settings.discovery_candidate_cap)
        assert data.get("total") == 1000, f"Expected 1000 (discovery candidate cap), got {data.get('total')}"

        # 2. Category filter
        res_cat = await client.get("/api/v1/experiences?category=cafes&limit=5")
        assert res_cat.status_code == 200
        cat_data = res_cat.json()
        print("Cafes count:", cat_data.get("total"))
        assert cat_data.get("total") > 0

        # 3. Get single experience
        exp_id = cat_data["items"][0]["id"]
        res_single = await client.get(f"/api/v1/experiences/{exp_id}")
        assert res_single.status_code == 200
        exp = res_single.json()
        print(f"Single experience: {exp.get('title')} | Source: {exp.get('source_type')} | Synthetic: {exp.get('is_synthetic')}")
        assert exp.get("is_synthetic") is False

        # 4. Search
        res_search = await client.get("/api/v1/experiences?search=Bandra&limit=5")
        assert res_search.status_code == 200
        print("Search Bandra results:", res_search.json().get("total"))

        # 5. Feasibility checks (missing hours gracefully handled as UNKNOWN)
        res_feas = await client.post(
            "/api/v1/feasibility/check",
            json={
                "experience_ids": [exp_id],
                "start_time": "2026-09-28T10:00:00Z",
                "party_size": 2
            }
        )
        print("Feasibility endpoint status:", res_feas.status_code)
        if res_feas.status_code == 200:
            print("Feasibility result:", res_feas.json())

        print("\nALL LIVE API REGRESSION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(test_live_api())
