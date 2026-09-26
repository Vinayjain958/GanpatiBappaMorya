# LocaLens — Real Mumbai Experience Data Expansion

This directory documents the ingestion, normalization, conflation, and quality audit for expanding the LocaLens experience catalog to **15,000 active, unique, real-world experiences** within Mumbai.

---

## 1. Non-Negotiable Engineering Principles

- **Real Data Only**: No synthetic business names, fabricated venues, or simulated POIs were generated. Every single imported record originates from a real, verifiable open geographic record (Overture Maps Places, release `2026-09-23.1`).
- **Truthful Completeness**: Missing real-world attributes (hours, ratings, reviews, capacity, bookable availability) are left strictly as `NULL` or `"unavailable"`. No fake reviews or synthetic ratings are attached to real venues.
- **Source Lineage**: Every experience and location record preserves full provenance (`source_type="overture_places"`, `source_name`, `source_record_id` / GERS ID, `source_version="2026-09-23.1"`, `source_license="CDLA-Permissive-2.0"`, `attribution_required=True`).
- **Existing Data Protection**: All 413 pre-existing records (including 65 synthetic demo records and 60 manual catalog entries) were preserved completely without modification or deletion.
- **Deterministic Conflation**: Multi-signal conflation and deduplication evaluates exact source identity, coordinate distance (Haversine), normalized name token similarity, phone match, and website match. Ambiguous pairs are preserved in `ambiguous_matches.jsonl` rather than blindly merged.

---

## 2. Source & Scope Specifications

- **Source**: Overture Maps Foundation — Places Theme (Release `2026-09-23.1`, Schema v2.x).
- **Access Method**: DuckDB `httpfs` / `spatial` querying GeoParquet directly from public AWS S3 (`s3://overturemaps-us-west-2/release/2026-09-23.1/theme=places/type=place/*`).
- **Geographic Bounding Box**: `min_lon=72.75, max_lon=72.98, min_lat=18.87, max_lat=19.22` (South Mumbai through Colaba, Fort, Marine Drive, Dadar, Bandra, Juhu, Andheri, Lower Parel, and Powai).
- **Attribution**: "Place data © Overture Maps Foundation contributors via the Overture Maps Foundation (Overture Places, release 2026-09-23.1), licensed CDLA-Permissive-2.0."

---

## 3. Directory Artifacts

| File | Purpose |
| :--- | :--- |
| [`source_manifest.json`](./source_manifest.json) | Declares upstream data sources, release versions, schemas, and licensing. |
| [`mumbai_scope.json`](./mumbai_scope.json) | Geographic definition, bounding box coordinates, and neighborhood centroid mapping. |
| [`schema_audit.json`](./schema_audit.json) | Complete schema inspection of tables, columns, foreign keys, and indexes. |
| [`current_catalog_audit.json`](./current_catalog_audit.json) | Baseline audit before expansion (413 experiences: 288 Overture, 65 synthetic, 60 manual). |
| [`conflation_report.json`](./conflation_report.json) | Conflation and duplicate matching metrics and timing. |
| [`ambiguous_matches.jsonl`](./ambiguous_matches.jsonl) | Log of candidate pairs with match score 0.45–0.74, preserved for inspection. |
| [`import_report.json`](./import_report.json) | Complete machine-readable summary of the ingestion execution. |
| [`final_report.md`](./final_report.md) | Human-readable ingestion report detailing numbers, categories, and localities. |
| [`post_import_catalog_audit.json`](./post_import_catalog_audit.json) | Post-import validation metrics, foreign key integrity checks, and 50 sampled records. |

---

## 4. Execution Tools

- `scripts/ingest_real_mumbai_places.py`: Reusable, idempotent CLI for dry-run and atomic batch insertion.
- `scripts/conflate_real_places.py`: Deterministic normalizer and multi-signal `PlaceConflationService`.
- `scripts/audit_real_mumbai_catalog.py`: Post-import catalog quality auditor.
