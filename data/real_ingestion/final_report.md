# Real Mumbai Data Ingestion Report

**Execution Mode**: `APPLY`  
**Overture Release**: `2026-09-23.1`  
**Target Count**: `15,000`  
**Target Status**: **MET**  

## Executive Summary

- **Active Experiences (Before)**: 15,000
- **Required Additional**: 0
- **Raw Overture Mumbai Candidates Examined**: 138,601
- **New Unique Real Places Prepared**: 0
- **Final Active Experiences**: 15,000
- **Shortfall**: 0

## Source Lineage & Provenance

- **Primary Source**: Overture Maps Places (CDLA-Permissive-2.0 / Apache-2.0)
- **Source Version**: 2026-09-23.1
- **Synthetic Flag**: `is_synthetic = False` on all new records
- **Attribution**: Full per-record attribution preserved
- **Truthful Completeness**: Missing ratings, reviews, hours, and availability remain honest `NULL` / `unavailable` (NO fabricated facts).

## Conflation & Deduplication Summary

- **Candidates Evaluated**: 138,601
- **Skipped (Already in DB)**: 0
- **Internal Duplicates Merged**: 0
- **Ambiguous Matches Flagged**: 0 (logged to `ambiguous_matches.jsonl`)
- **Conflation Duration**: 0.0s

## Category Distribution (New Records)

| Category Slug | Count |
| :--- | :--- |

## Locality Distribution (New Records)

| Locality | Count |
| :--- | :--- |

---
*Generated at 2026-09-26T16:34:49.596089+00:00 by `scripts/ingest_real_mumbai_places.py`*
