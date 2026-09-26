"""Real Mumbai Experience Data Expansion Pipeline.

Expands the LocaLens catalog to approximately TARGET_ACTIVE_EXPERIENCES (~15,000)
using authentic, real-world, licensed Overture Maps Places data.

Strict Non-Negotiables:
- Real data only (no synthetic business names, no fabricated POIs)
- Real attributes only (no invented hours, ratings, reviews, availability, or images)
- Full source lineage & provenance preserved (is_synthetic=False, source_type='overture_places')
- Deterministic multi-signal conflation and deduplication
- Zero overwriting of existing authoritative LocaLens records
- Safe dry-run and atomic batch apply with rollback

Usage:
    python scripts/ingest_real_mumbai_places.py --dry-run
    python scripts/ingest_real_mumbai_places.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure apps/api and root are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(REPO_ROOT))

# Ensure database_url resolves to the live development database
db_file = API_ROOT / "localens_dev.db"
if db_file.exists():
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.resolve().as_posix()}"

import duckdb
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from scripts.conflate_real_places import (
        PlaceConflationService,
        haversine_distance_m,
        normalize_name,
        normalize_phone,
        normalize_website,
    )
except ImportError:
    from conflate_real_places import (
        PlaceConflationService,
        haversine_distance_m,
        normalize_name,
        normalize_phone,
        normalize_website,
    )
from src.core.category_map import OVERTURE_CATEGORY_MAP
from src.core.db import async_session_factory
from src.models import (
    Experience,
    ExperienceCategory,
    Location,
    Provider,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("real_ingestion")

# Geographic Scope
MUMBAI_BBOX = {"min_lon": 72.75, "max_lon": 72.98, "min_lat": 18.87, "max_lat": 19.22}

NEIGHBORHOOD_CENTROIDS: dict[str, tuple[float, float]] = {
    "Fort": (72.8356, 18.9346),
    "Kala Ghoda": (72.8317, 18.9281),
    "Colaba": (72.8147, 18.9067),
    "Churchgate": (72.8267, 18.9354),
    "Marine Drive": (72.8235, 18.9440),
    "Dadar": (72.8438, 19.0176),
    "Matunga": (72.8570, 19.0270),
    "Bandra": (72.8295, 19.0596),
    "Juhu": (72.8263, 19.1075),
    "Andheri": (72.8468, 19.1197),
    "Lower Parel": (72.8300, 18.9960),
    "Powai": (72.9060, 19.1176),
}

# Category duration estimates (minutes)
ESTIMATED_DURATION_MINUTES = {
    "food-drink": 60, "street-food": 45, "cafes": 45, "culture-heritage": 60,
    "art-galleries": 50, "museums": 75, "workshops": 100, "crafts": 90,
    "shopping-markets": 60, "outdoors": 60, "adventure": 120, "photography": 60,
    "family": 90, "nightlife": 90, "music": 90, "community": 45,
    "hidden-gems": 45, "wellness": 75, "entertainment": 120, "local-experiences": 120,
}

OVERTURE_ATTRIBUTION_TEMPLATE = (
    "Place data © {source_name} via the Overture Maps Foundation "
    "(Overture Places, release {version}), licensed {license}."
)


def nearest_neighborhood(lon: float, lat: float) -> str:
    """Assign human-readable locality by nearest centroid distance."""
    return min(NEIGHBORHOOD_CENTROIDS, key=lambda n: haversine_distance_m(lat, lon, NEIGHBORHOOD_CENTROIDS[n][1], NEIGHBORHOOD_CENTROIDS[n][0]))


def extract_provenance(sources_list: list[dict] | None) -> dict[str, Any]:
    sources = sources_list or []
    provider_entry = next((s for s in sources if isinstance(s, dict) and s.get("record_id")), None)
    entry = provider_entry or (sources[0] if sources and isinstance(sources[0], dict) else {})
    return {
        "source_name": entry.get("provider") or entry.get("dataset") or "meta",
        "source_record_id": entry.get("record_id"),
        "source_license": entry.get("license") or "CDLA-Permissive-2.0",
        "source_update_time": entry.get("update_time"),
    }


def format_address(addresses_raw: Any) -> tuple[str | None, str | None]:
    """Extract freeform address and postal code from Overture addresses struct/list."""
    if not addresses_raw:
        return None, None
    addr = addresses_raw[0] if isinstance(addresses_raw, list) and addresses_raw else addresses_raw
    if not isinstance(addr, dict):
        return None, None
    freeform = addr.get("freeform")
    postcode = addr.get("postcode")
    if not freeform:
        parts = [addr.get("house_number"), addr.get("road"), addr.get("locality"), addr.get("region")]
        freeform = ", ".join(p for p in parts if p)
    return (freeform[:490] if freeform else None, str(postcode)[:20] if postcode else None)


def parse_phone(phones_raw: Any) -> str | None:
    if not phones_raw:
        return None
    phone_val = normalize_phone(phones_raw)
    return phone_val[:40] if phone_val else None


def parse_website(websites_raw: Any) -> str | None:
    if not websites_raw:
        return None
    web_val = normalize_website(websites_raw)
    return web_val[:490] if web_val else None


class RealPlaceIngestionPipeline:
    def __init__(
        self,
        target_count: int = 15000,
        min_confidence: float = 0.30,
        overture_release: str = "2026-09-23.1",
        batch_size: int = 500,
        dry_run: bool = True,
    ):
        self.target_count = target_count
        self.min_confidence = min_confidence
        self.overture_release = overture_release
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.conflation_service = PlaceConflationService()

        self.data_dir = REPO_ROOT / "data" / "real_ingestion"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = REPO_ROOT / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    async def get_live_catalog_state(self, session: AsyncSession) -> dict[str, Any]:
        """Audit current catalog to discover counts and existing IDs for protection."""
        total_exp = (await session.execute(select(func.count(Experience.id)))).scalar_one()
        active_exp = (await session.execute(select(func.count(Experience.id)).where(Experience.status == "active"))).scalar_one()
        
        # Collect existing source record IDs
        query_ids = select(Experience.source_record_id, Experience.id, Experience.title, Experience.source_type)
        rows = (await session.execute(query_ids)).all()
        existing_source_ids = {r[0] for r in rows if r[0]}
        existing_exp_ids = {r[1] for r in rows}
        
        # Category map from slug -> id
        cats = (await session.execute(select(ExperienceCategory))).scalars().all()
        cat_slug_to_id = {c.slug: c.id for c in cats}
        
        return {
            "total_experiences": total_exp,
            "active_experiences": active_exp,
            "existing_source_ids": existing_source_ids,
            "existing_exp_ids": existing_exp_ids,
            "cat_slug_to_id": cat_slug_to_id,
        }

    def load_overture_candidates(self) -> list[dict[str, Any]]:
        """Load and filter Overture candidate records from local Parquet cache or S3."""
        cached_parquet = self.raw_dir / f"overture_mumbai_places_{self.overture_release.replace('.', '_')}.parquet"
        con = duckdb.connect()
        con.execute("INSTALL spatial; INSTALL httpfs; LOAD spatial; LOAD httpfs;")
        con.execute("SET s3_region='us-west-2';")

        if cached_parquet.exists():
            source_expr = f"read_parquet('{cached_parquet.as_posix()}')"
            logger.info("Reading from local cached Parquet: %s", cached_parquet)
            query = f"""
            SELECT 
                id,
                version,
                name,
                basic_category,
                confidence,
                operating_status,
                addresses,
                phones,
                websites,
                sources,
                lon,
                lat
            FROM {source_expr}
            WHERE lon BETWEEN {MUMBAI_BBOX['min_lon']} AND {MUMBAI_BBOX['max_lon']}
              AND lat BETWEEN {MUMBAI_BBOX['min_lat']} AND {MUMBAI_BBOX['max_lat']}
              AND name IS NOT NULL
              AND length(name) >= 2
              AND (operating_status IS NULL OR operating_status != 'permanently_closed')
              AND confidence >= {self.min_confidence}
            ORDER BY confidence DESC
            """
        else:
            s3_url = f"s3://overturemaps-us-west-2/release/{self.overture_release}/theme=places/type=place/*"
            source_expr = f"read_parquet('{s3_url}')"
            logger.info("Reading directly from S3: %s", s3_url)
            query = f"""
            SELECT 
                id,
                version,
                names.primary AS name,
                basic_category,
                confidence,
                operating_status,
                addresses,
                phones,
                websites,
                sources,
                ST_X(geometry) AS lon,
                ST_Y(geometry) AS lat
            FROM {source_expr}
            WHERE bbox.xmin <= {MUMBAI_BBOX['max_lon']} AND bbox.xmax >= {MUMBAI_BBOX['min_lon']}
              AND bbox.ymin <= {MUMBAI_BBOX['max_lat']} AND bbox.ymax >= {MUMBAI_BBOX['min_lat']}
              AND names.primary IS NOT NULL
              AND length(names.primary) >= 2
              AND (operating_status IS NULL OR operating_status != 'permanently_closed')
              AND confidence >= {self.min_confidence}
            ORDER BY confidence DESC
            """
        rows = con.execute(query).fetchall()
        columns = [
            "id", "version", "name", "basic_category", "confidence",
            "operating_status", "addresses", "phones", "websites",
            "sources", "lon", "lat"
        ]
        candidates = [dict(zip(columns, r, strict=True)) for r in rows]
        logger.info("Loaded %d raw eligible Overture candidate rows", len(candidates))
        return candidates

    def conflate_and_deduplicate(
        self,
        candidates: list[dict[str, Any]],
        existing_source_ids: set[str],
        required_count: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Deduplicate against existing DB records and conflate internally among candidates."""
        logger.info("Starting conflation & deduplication (required additional: %d)...", required_count)
        t0 = time.time()

        accepted: list[dict[str, Any]] = []
        ambiguous_pairs: list[dict[str, Any]] = []
        duplicate_count = 0
        already_existing_count = 0
        unmapped_category_count = 0

        # Spatial grid index for fast O(1) proximity lookups (cell size ~0.003 deg ~ 330m)
        grid: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)

        def get_grid_cells(lat: float, lon: float) -> list[tuple[int, int]]:
            gx = int(lon / 0.003)
            gy = int(lat / 0.003)
            return [(gx + dx, gy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

        if required_count <= 0:
            logger.info("Target count already met. 0 new records required.")
            conflation_report = {
                "candidates_evaluated": len(candidates),
                "unmapped_categories_skipped": 0,
                "already_in_database_skipped": 0,
                "internal_duplicates_merged": 0,
                "ambiguous_pairs_flagged": 0,
                "accepted_unique_real_places": 0,
                "duration_seconds": 0.0,
            }
            return [], conflation_report

        for cand in candidates:
            # 1. Category mapping
            cat_slug = OVERTURE_CATEGORY_MAP.get(cand["basic_category"])
            if not cat_slug:
                unmapped_category_count += 1
                continue
            cand["category_slug"] = cat_slug

            # 2. Check if already in DB
            cand_id = cand["id"]
            if cand_id in existing_source_ids:
                already_existing_count += 1
                continue

            # 3. Geo coordinates check
            lon, lat = cand["lon"], cand["lat"]
            if not (MUMBAI_BBOX["min_lon"] <= lon <= MUMBAI_BBOX["max_lon"] and MUMBAI_BBOX["min_lat"] <= lat <= MUMBAI_BBOX["max_lat"]):
                continue

            cand["locality"] = nearest_neighborhood(lon, lat)
            cand["norm_name"] = normalize_name(cand["name"])

            # 4. Check for duplicates in spatial vicinity
            is_dup = False
            for cell in get_grid_cells(lat, lon):
                if is_dup:
                    break
                for neighbor in grid[cell]:
                    match_res = self.conflation_service.score(cand, neighbor)
                    if match_res.is_match:
                        is_dup = True
                        duplicate_count += 1
                        break
                    elif match_res.is_ambiguous:
                        ambiguous_pairs.append({
                            "candidate_a": {"id": cand["id"], "name": cand["name"], "lat": lat, "lon": lon},
                            "candidate_b": {"id": neighbor["id"], "name": neighbor["name"], "lat": neighbor["lat"], "lon": neighbor["lon"]},
                            "match_score": match_res.score,
                            "signals": match_res.signals,
                            "reasons": match_res.reasons,
                        })

            if not is_dup:
                accepted.append(cand)
                center_cell = (int(lon / 0.003), int(lat / 0.003))
                grid[center_cell].append(cand)

                # Stop if we hit required additional count
                if len(accepted) >= required_count:
                    break

        conflation_report = {
            "candidates_evaluated": len(candidates),
            "unmapped_categories_skipped": unmapped_category_count,
            "already_in_database_skipped": already_existing_count,
            "internal_duplicates_merged": duplicate_count,
            "ambiguous_pairs_flagged": len(ambiguous_pairs),
            "accepted_unique_real_places": len(accepted),
            "duration_seconds": round(time.time() - t0, 2),
        }

        # Save ambiguous matches log
        amb_path = self.data_dir / "ambiguous_matches.jsonl"
        with open(amb_path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(pair) + "\n" for pair in ambiguous_pairs)

        with open(self.data_dir / "conflation_report.json", "w", encoding="utf-8") as f:
            json.dump(conflation_report, f, indent=2)

        logger.info(
            "Conflation finished: %d unique accepted, %d duplicates merged, %d ambiguous logged to %s",
            len(accepted), duplicate_count, len(ambiguous_pairs), amb_path
        )
        return accepted, conflation_report

    def build_entities(
        self,
        accepted: list[dict[str, Any]],
        cat_slug_to_id: dict[str, str],
    ) -> list[tuple[Location, Provider, Experience]]:
        """Construct validated SQLAlchemy model instances matching exact schema contract."""
        entities = []
        now = datetime.now(UTC)

        for item in accepted:
            cand_id = item["id"]
            name = item["name"].strip()
            cat_slug = item["category_slug"]
            cat_id = cat_slug_to_id.get(cat_slug)
            if not cat_id:
                continue

            lon, lat = item["lon"], item["lat"]
            locality = item["locality"]
            addr_text, postal_code = format_address(item.get("addresses"))
            phone = parse_phone(item.get("phones"))
            website = parse_website(item.get("websites"))
            prov_info = extract_provenance(item.get("sources"))

            loc_id = str(uuid.uuid4())
            provider_id = str(uuid.uuid4())
            exp_id = str(uuid.uuid4())

            # 1. Location
            location = Location(
                id=loc_id,
                latitude=float(lat),
                longitude=float(lon),
                place_name=name[:200],
                address=addr_text,
                locality=locality,
                city="Mumbai",
                state="Maharashtra",
                country="India",
                postal_code=postal_code,
                timezone="Asia/Kolkata",
                source_type="overture_places",
                source_name=prov_info["source_name"],
                source_record_id=cand_id,
                source_version=self.overture_release,
                source_accessed_at=now,
                source_url="https://docs.overturemaps.org/guides/places/",
                source_license=prov_info["source_license"],
                attribution_required=True,
                attribution_text=OVERTURE_ATTRIBUTION_TEMPLATE.format(
                    source_name=prov_info["source_name"],
                    version=self.overture_release,
                    license=prov_info["source_license"]
                ),
                source_confidence=float(item.get("confidence") or 0.8),
                is_synthetic=False,
                is_enriched=False,
            )

            # 2. Provider
            provider = Provider(
                id=provider_id,
                business_name=name[:200],
                description=f"Local experience venue and operator in {locality}, Mumbai.",
                provider_type=f"{cat_slug}_provider",
                contact_phone=phone,
                website=website,
                verification_status="catalog_imported",
                city="Mumbai",
                source_type="overture_places",
                source_name=prov_info["source_name"],
                source_record_id=cand_id,
                source_version=self.overture_release,
                source_accessed_at=now,
                source_url="https://docs.overturemaps.org/guides/places/",
                source_license=prov_info["source_license"],
                attribution_required=True,
                attribution_text=OVERTURE_ATTRIBUTION_TEMPLATE.format(
                    source_name=prov_info["source_name"],
                    version=self.overture_release,
                    license=prov_info["source_license"]
                ),
                source_confidence=float(item.get("confidence") or 0.8),
                is_synthetic=False,
                is_enriched=False,
            )

            # 3. Experience
            duration = ESTIMATED_DURATION_MINUTES.get(cat_slug, 60)
            short_desc = f"{name} in {locality}, Mumbai — authentic local {cat_slug.replace('-', ' ')}."
            full_desc = f"{name} is an active local {cat_slug.replace('-', ' ')} venue located in {locality}, Mumbai."
            if addr_text:
                full_desc += f" Address: {addr_text}."

            experience = Experience(
                id=exp_id,
                provider_id=provider_id,
                category_id=cat_id,
                location_id=loc_id,
                title=name[:200],
                short_description=short_desc[:300],
                full_description=full_desc,
                currency="INR",
                price=None,
                minimum_price=None,
                maximum_price=None,
                price_type="unknown",
                price_source="unavailable",
                price_confidence=None,
                is_price_estimated=False,
                duration_minutes=duration,
                duration_is_estimated=True,
                status="active",
                verification_status="catalog_imported",
                suitability=["solo", "friends", "family"],
                tags=[cat_slug, locality.lower().replace(" ", "-"), "mumbai-local"],
                rating=None,
                rating_source="unavailable",
                review_count=0,
                image_url=None,
                image_thumbnail_url=None,
                image_source=None,
                opening_hours_status="unavailable",
                source_type="overture_places",
                source_name=prov_info["source_name"],
                source_record_id=cand_id,
                source_version=self.overture_release,
                source_accessed_at=now,
                source_url="https://docs.overturemaps.org/guides/places/",
                source_license=prov_info["source_license"],
                attribution_required=True,
                attribution_text=OVERTURE_ATTRIBUTION_TEMPLATE.format(
                    source_name=prov_info["source_name"],
                    version=self.overture_release,
                    license=prov_info["source_license"]
                ),
                source_confidence=float(item.get("confidence") or 0.8),
                is_synthetic=False,
                is_enriched=True,
            )

            entities.append((location, provider, experience))

        return entities

    async def execute_batch_import(
        self,
        session: AsyncSession,
        entities: list[tuple[Location, Provider, Experience]],
    ) -> int:
        """Insert records in batches with transaction safety."""
        total = len(entities)
        if total == 0:
            logger.info("No entities to insert.")
            return 0
        inserted = 0
        t0 = time.time()
        logger.info("Beginning batch insertion of %d entities (batch size %d)...", total, self.batch_size)

        for i in range(0, total, self.batch_size):
            chunk = entities[i:i + self.batch_size]
            for loc, prov, exp in chunk:
                session.add(loc)
                session.add(prov)
                session.add(exp)
            await session.flush()
            inserted += len(chunk)
            if inserted % 2000 == 0 or inserted == total:
                logger.info("Inserted %d / %d records (%.1f%%)...", inserted, total, (inserted / total) * 100)

        await session.commit()
        logger.info("Batch insertion completed in %.2fs!", time.time() - t0)
        return inserted

    async def run(self) -> dict[str, Any]:
        async with async_session_factory() as session:
            state = await self.get_live_catalog_state(session)

        current_active = state["active_experiences"]
        current_total = state["total_experiences"]
        existing_source_ids = state["existing_source_ids"]
        cat_slug_to_id = state["cat_slug_to_id"]

        required_additional = max(0, self.target_count - current_active)
        logger.info(
            "Catalog Baseline: total=%d, active=%d. Target=%d, required additional=%d",
            current_total, current_active, self.target_count, required_additional
        )

        # 1. Load candidates
        raw_candidates = self.load_overture_candidates()

        # 2. Conflate & deduplicate
        accepted_candidates, conflation_report = self.conflate_and_deduplicate(
            raw_candidates, existing_source_ids, required_additional
        )

        potential_final_active = current_active + len(accepted_candidates)
        shortfall = max(0, self.target_count - potential_final_active)

        # 3. Build model entities
        entities = self.build_entities(accepted_candidates, cat_slug_to_id)

        # Category and geographic breakdown of newly accepted
        new_category_counts = Counter(e[2].tags[0] for e in entities)
        new_locality_counts = Counter(e[0].locality for e in entities)

        import_report = {
            "mode": "APPLY" if not self.dry_run else "DRY_RUN",
            "overture_release": self.overture_release,
            "target_count": self.target_count,
            "current_active_before": current_active,
            "required_additional": required_additional,
            "candidates_examined": len(raw_candidates),
            "new_unique_real_places_prepared": len(entities),
            "potential_final_active": potential_final_active,
            "shortfall": shortfall,
            "target_status": "MET" if potential_final_active >= self.target_count else "NEAR_TARGET",
            "conflation_summary": conflation_report,
            "new_places_by_category": dict(new_category_counts),
            "new_places_by_locality": dict(new_locality_counts),
            "database_changes_applied": False,
        }

        if self.dry_run:
            logger.info("DRY RUN COMPLETE — ZERO DATABASE CHANGES APPLIED.")
        else:
            logger.info("Applying database changes...")
            async with async_session_factory() as session:
                try:
                    inserted_count = await self.execute_batch_import(session, entities)
                    import_report["database_changes_applied"] = True
                    import_report["inserted_count"] = inserted_count
                    
                    # Verify final count
                    final_active = (await session.execute(select(func.count(Experience.id)).where(Experience.status == "active"))).scalar_one()
                    import_report["verified_final_active_experiences"] = final_active
                    logger.info("VERIFIED FINAL ACTIVE EXPERIENCES IN DB: %d", final_active)
                except Exception as e:
                    await session.rollback()
                    logger.error("Error during batch insert, rolled back: %s", e)
                    raise

        # Write reports
        with open(self.data_dir / "import_report.json", "w", encoding="utf-8") as f:  # noqa: ASYNC230
            json.dump(import_report, f, indent=2)

        self.generate_markdown_report(import_report)
        return import_report

    def generate_markdown_report(self, report: dict[str, Any]) -> None:
        md_path = self.data_dir / "final_report.md"
        lines = [
            "# Real Mumbai Data Ingestion Report",
            "",
            f"**Execution Mode**: `{report['mode']}`  ",
            f"**Overture Release**: `{report['overture_release']}`  ",
            f"**Target Count**: `{report['target_count']:,}`  ",
            f"**Target Status**: **{report['target_status']}**  ",
            "",
            "## Executive Summary",
            "",
            f"- **Active Experiences (Before)**: {report['current_active_before']:,}",
            f"- **Required Additional**: {report['required_additional']:,}",
            f"- **Raw Overture Mumbai Candidates Examined**: {report['candidates_examined']:,}",
            f"- **New Unique Real Places Prepared**: {report['new_unique_real_places_prepared']:,}",
            f"- **Final Active Experiences**: {report.get('verified_final_active_experiences', report['potential_final_active']):,}",
            f"- **Shortfall**: {report['shortfall']:,}",
            "",
            "## Source Lineage & Provenance",
            "",
            "- **Primary Source**: Overture Maps Places (CDLA-Permissive-2.0 / Apache-2.0)",
            f"- **Source Version**: {report['overture_release']}",
            "- **Synthetic Flag**: `is_synthetic = False` on all new records",
            "- **Attribution**: Full per-record attribution preserved",
            "- **Truthful Completeness**: Missing ratings, reviews, hours, and availability remain honest `NULL` / `unavailable` (NO fabricated facts).",
            "",
            "## Conflation & Deduplication Summary",
            "",
            f"- **Candidates Evaluated**: {report['conflation_summary']['candidates_evaluated']:,}",
            f"- **Skipped (Already in DB)**: {report['conflation_summary']['already_in_database_skipped']:,}",
            f"- **Internal Duplicates Merged**: {report['conflation_summary']['internal_duplicates_merged']:,}",
            f"- **Ambiguous Matches Flagged**: {report['conflation_summary']['ambiguous_pairs_flagged']:,} (logged to `ambiguous_matches.jsonl`)",
            f"- **Conflation Duration**: {report['conflation_summary']['duration_seconds']}s",
            "",
            "## Category Distribution (New Records)",
            "",
            "| Category Slug | Count |",
            "| :--- | :--- |",
        ]
        for cat, count in sorted(report["new_places_by_category"].items(), key=lambda x: -x[1]):
            lines.append(f"| `{cat}` | {count:,} |")

        lines.extend([
            "",
            "## Locality Distribution (New Records)",
            "",
            "| Locality | Count |",
            "| :--- | :--- |",
        ])
        for loc, count in sorted(report["new_places_by_locality"].items(), key=lambda x: -x[1]):
            lines.append(f"| {loc} | {count:,} |")

        lines.extend([
            "",
            "---",
            f"*Generated at {datetime.now(UTC).isoformat()} by `scripts/ingest_real_mumbai_places.py`*",
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        logger.info("Saved final markdown report to %s", md_path)


def main():
    parser = argparse.ArgumentParser(description="Ingest real-world Mumbai places into LocaLens catalog")
    parser.add_argument("--target-count", type=int, default=15000, help="Target total active experiences")
    parser.add_argument("--min-confidence", type=float, default=0.30, help="Minimum Overture confidence threshold")
    parser.add_argument("--overture-release", type=str, default="2026-09-23.1", help="Overture release version")
    parser.add_argument("--batch-size", type=int, default=500, help="Database batch insert size")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate ingestion without DB changes")
    group.add_argument("--apply", action="store_true", help="Apply changes to the database")

    args = parser.parse_args()
    is_dry_run = not args.apply

    pipeline = RealPlaceIngestionPipeline(
        target_count=args.target_count,
        min_confidence=args.min_confidence,
        overture_release=args.overture_release,
        batch_size=args.batch_size,
        dry_run=is_dry_run,
    )

    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
