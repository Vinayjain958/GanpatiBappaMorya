"""Catalog Quality and Schema Audit Script for LocaLens.

Performs exhaustive verification of the active database:
- Counts and active status verification
- Provenance breakdown (overture_places, synthetic, manual)
- Category and locality distributions
- Quality checks: missing/invalid coordinates, duplicate source IDs, foreign key integrity
- Random sample inspection (50+ records)
"""

from __future__ import annotations

import json
import random
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"
DB_PATH = API_ROOT / "localens_dev.db"


def run_audit(sample_size: int = 50) -> dict:
    if not DB_PATH.exists():
        print(f"Error: Database file {DB_PATH} not found.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Experiences
    cur.execute("SELECT * FROM experiences")
    experiences = [dict(r) for r in cur.fetchall()]
    total_exp = len(experiences)
    active_exp = sum(1 for e in experiences if e.get("status") == "active")
    inactive_exp = sum(1 for e in experiences if e.get("status") == "inactive")

    prov_dist = Counter(e.get("source_type") for e in experiences)
    synth_dist = Counter(bool(e.get("is_synthetic")) for e in experiences)

    # 2. Categories
    cur.execute("SELECT id, slug, name FROM experience_categories")
    categories = [dict(r) for r in cur.fetchall()]
    cat_id_to_slug = {c["id"]: c["slug"] for c in categories}
    cat_dist = Counter(cat_id_to_slug.get(e.get("category_id"), "unknown") for e in experiences)

    # 3. Locations
    cur.execute("SELECT * FROM locations")
    locations = [dict(r) for r in cur.fetchall()]
    loc_id_to_loc = {l["id"]: l for l in locations}
    locality_dist = Counter(loc_id_to_loc.get(e.get("location_id"), {}).get("locality", "unknown") for e in experiences)

    # 4. Providers
    cur.execute("SELECT * FROM providers")
    providers = [dict(r) for r in cur.fetchall()]

    # Quality Checks
    missing_coords = 0
    invalid_coords = 0
    mumbai_bbox = {"min_lon": 72.75, "max_lon": 72.98, "min_lat": 18.87, "max_lat": 19.22}
    out_of_scope_coords = 0

    for l in locations:
        lat, lon = l.get("latitude"), l.get("longitude")
        if lat is None or lon is None:
            missing_coords += 1
        elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
            invalid_coords += 1
        elif not (mumbai_bbox["min_lon"] - 0.05 <= lon <= mumbai_bbox["max_lon"] + 0.05 and mumbai_bbox["min_lat"] - 0.05 <= lat <= mumbai_bbox["max_lat"] + 0.05):
            out_of_scope_coords += 1

    # Check for foreign key integrity
    loc_ids = {l["id"] for l in locations}
    prov_ids = {p["id"] for p in providers}
    cat_ids = set(cat_id_to_slug.keys())

    orphan_location = sum(1 for e in experiences if e.get("location_id") not in loc_ids)
    orphan_provider = sum(1 for e in experiences if e.get("provider_id") not in prov_ids)
    orphan_category = sum(1 for e in experiences if e.get("category_id") not in cat_ids)

    # Duplicate source IDs
    source_ids = [e.get("source_record_id") for e in experiences if e.get("source_record_id")]
    id_counts = Counter(source_ids)
    duplicate_source_ids = sum(1 for k, v in id_counts.items() if v > 1)

    # Attributes truthfulness check
    real_exps = [e for e in experiences if not e.get("is_synthetic")]
    real_with_fake_rating = sum(1 for e in real_exps if e.get("rating") is not None and e.get("rating_source") == "unavailable")

    audit_report = {
        "database_path": str(DB_PATH),
        "experiences": {
            "total": total_exp,
            "active": active_exp,
            "inactive": inactive_exp,
            "provenance_distribution": dict(prov_dist),
            "synthetic_distribution": {"synthetic": synth_dist.get(True, 0), "real": synth_dist.get(False, 0)},
            "category_distribution": dict(cat_dist),
            "locality_distribution": dict(locality_dist),
        },
        "quality_metrics": {
            "missing_coordinates": missing_coords,
            "invalid_coordinates": invalid_coords,
            "out_of_scope_coordinates": out_of_scope_coords,
            "orphan_locations": orphan_location,
            "orphan_providers": orphan_provider,
            "orphan_categories": orphan_category,
            "duplicate_source_ids": duplicate_source_ids,
            "real_with_fake_rating": real_with_fake_rating,
        },
    }

    # Sample verification
    random.seed(42)
    sample_records = random.sample(experiences, min(sample_size, len(experiences)))
    samples = []
    for s in sample_records:
        loc = loc_id_to_loc.get(s.get("location_id"), {})
        samples.append({
            "id": s.get("id"),
            "title": s.get("title"),
            "category": cat_id_to_slug.get(s.get("category_id")),
            "locality": loc.get("locality"),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "source_type": s.get("source_type"),
            "source_record_id": s.get("source_record_id"),
            "source_confidence": s.get("source_confidence"),
            "is_synthetic": bool(s.get("is_synthetic")),
            "status": s.get("status"),
        })

    audit_report["samples"] = samples

    out_file = REPO_ROOT / "data" / "real_ingestion" / "post_import_catalog_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    print("=" * 60)
    print("CATALOG AUDIT REPORT")
    print("=" * 60)
    print(f"Total Experiences: {total_exp}")
    print(f"Active Experiences: {active_exp}")
    print(f"Real vs Synthetic: Real={synth_dist.get(False, 0)}, Synthetic={synth_dist.get(True, 0)}")
    print(f"Provenance Distribution: {dict(prov_dist)}")
    print(f"Quality Metrics: {audit_report['quality_metrics']}")
    print(f"Audit report saved to: {out_file}")
    return audit_report


if __name__ == "__main__":
    run_audit()
