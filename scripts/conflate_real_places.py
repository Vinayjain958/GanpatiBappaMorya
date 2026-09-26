"""Place Conflation and Normalization Service for LocaLens.

Implements deterministic normalization and multi-signal conflation for
real-world POI datasets (Overture, OSM, existing LocaLens catalog).

Adheres strictly to the project non-negotiables:
- Deterministic scoring (no LLM in the conflation loop)
- Multi-signal matching (identity, distance, name, phone, website, taxonomy)
- Explicit ambiguous match logging (data/real_ingestion/ambiguous_matches.jsonl)
- Preserves primary source provenance and licensing
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_name(name: str | None) -> str:
    """Normalize a place or business name deterministically.
    
    Unicode NFKC normalization, lowercase, punctuation removal,
    whitespace collapse.
    """
    if not name:
        return ""
    # Normalize unicode
    normalized = unicodedata.normalize("NFKC", name)
    # Lowercase
    lowered = normalized.lower()
    # Strip common punctuation, replace with space
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    # Collapse multiple whitespaces
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_phone(phone_input: Any) -> str | None:
    """Normalize Indian phone numbers to E.164 format where confidently possible.
    
    Accepts string, list of strings/dicts, or None. Never guesses missing digits.
    """
    if not phone_input:
        return None
    raw = ""
    if isinstance(phone_input, list):
        if not phone_input:
            return None
        first = phone_input[0]
        raw = first.get("value", "") if isinstance(first, dict) else str(first)
    elif isinstance(phone_input, dict):
        raw = phone_input.get("value", "")
    else:
        raw = str(phone_input)

    # Remove formatting characters except +
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    if not cleaned:
        return None

    # Handle Indian numbers (+91)
    if cleaned.startswith("+91") and len(cleaned) == 13:
        return cleaned
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"+91{cleaned[1:]}"
    if len(cleaned) == 10 and cleaned[0] in "6789":
        return f"+91{cleaned}"
    
    return cleaned if len(cleaned) >= 8 else None


def normalize_website(website_input: Any) -> str | None:
    """Canonicalize a website URL by stripping tracking params and standardizing scheme/host."""
    if not website_input:
        return None
    raw = ""
    if isinstance(website_input, list):
        if not website_input:
            return None
        first = website_input[0]
        raw = first.get("value", "") if isinstance(first, dict) else str(first)
    else:
        raw = str(website_input)

    raw = raw.strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"

    try:
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        host = host.removeprefix("www.")
        
        # Strip tracking query parameters
        qs = parse_qs(parsed.query)
        tracking_prefixes = ("utm_", "fbclid", "gclid", "ref", "source")
        filtered_qs = {k: v for k, v in qs.items() if not any(k.lower().startswith(p) for p in tracking_prefixes)}
        new_query = urlencode(filtered_qs, doseq=True)
        
        path = parsed.path.rstrip("/")
        canonical = urlunparse((parsed.scheme.lower(), host, path, "", new_query, ""))
        return canonical
    except (ValueError, AttributeError):
        return raw


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in meters."""
    r = 6_371_000.0  # Earth's radius in meters
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def name_token_similarity(name1: str, name2: str) -> float:
    """Jaccard similarity on normalized token sets."""
    norm1, norm2 = normalize_name(name1), normalize_name(name2)
    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0
    tokens1, tokens2 = set(norm1.split()), set(norm2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


@dataclass
class MatchResult:
    score: float
    is_match: bool
    is_ambiguous: bool
    signals: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class PlaceConflationService:
    """Multi-signal deterministic place conflation service."""

    def __init__(
        self,
        match_threshold: float = 0.75,
        ambiguous_threshold: float = 0.45,
        max_proximity_meters: float = 120.0,
    ):
        self.match_threshold = match_threshold
        self.ambiguous_threshold = ambiguous_threshold
        self.max_proximity_meters = max_proximity_meters

    def score(self, record_a: dict, record_b: dict) -> MatchResult:
        signals: list[str] = []
        reasons: list[str] = []
        score = 0.0

        # 1. Exact Source ID (Primary Identity)
        id_a = record_a.get("source_record_id") or record_a.get("id")
        id_b = record_b.get("source_record_id") or record_b.get("id")
        if id_a and id_b and id_a == id_b:
            return MatchResult(
                score=1.0,
                is_match=True,
                is_ambiguous=False,
                signals=["exact_source_id"],
                reasons=[f"Identical source record ID {id_a}"]
            )

        # 2. Geographic Proximity
        lat_a, lon_a = record_a.get("lat"), record_a.get("lon")
        lat_b, lon_b = record_b.get("lat"), record_b.get("lon")
        
        if lat_a is None or lon_a is None or lat_b is None or lon_b is None:
            return MatchResult(score=0.0, is_match=False, is_ambiguous=False, reasons=["Missing coordinates"])

        dist_m = haversine_distance_m(lat_a, lon_a, lat_b, lon_b)
        
        # If farther than max proximity, highly unlikely to be the same physical venue
        if dist_m > 500.0:
            return MatchResult(score=0.0, is_match=False, is_ambiguous=False, reasons=[f"Distance {dist_m:.1f}m > 500m"])

        # Proximity signals
        if dist_m <= 15.0:
            score += 0.35
            signals.append("coincident_location_le_15m")
        elif dist_m <= 50.0:
            score += 0.25
            signals.append("near_location_le_50m")
        elif dist_m <= self.max_proximity_meters:
            score += 0.15
            signals.append(f"proximity_le_{int(self.max_proximity_meters)}m")

        # 3. Name Similarity
        name_a = record_a.get("name") or record_a.get("title", "")
        name_b = record_b.get("name") or record_b.get("title", "")
        norm_a = normalize_name(name_a)
        norm_b = normalize_name(name_b)

        sim = name_token_similarity(name_a, name_b)
        if norm_a and norm_b and norm_a == norm_b:
            score += 0.45
            signals.append("exact_normalized_name")
        elif sim >= 0.80:
            score += 0.35
            signals.append(f"high_name_token_similarity_{sim:.2f}")
        elif sim >= 0.50:
            score += 0.20
            signals.append(f"moderate_name_token_similarity_{sim:.2f}")

        # 4. Phone Match
        phone_a = normalize_phone(record_a.get("phones") or record_a.get("contact_phone"))
        phone_b = normalize_phone(record_b.get("phones") or record_b.get("contact_phone"))
        if phone_a and phone_b:
            if phone_a == phone_b:
                score += 0.40
                signals.append("same_phone_number")
            else:
                score -= 0.15
                reasons.append("conflicting_phone_numbers")

        # 5. Website Match
        web_a = normalize_website(record_a.get("websites") or record_a.get("website"))
        web_b = normalize_website(record_b.get("websites") or record_b.get("website"))
        if web_a and web_b:
            if web_a == web_b:
                score += 0.35
                signals.append("same_website")
            else:
                score -= 0.10
                reasons.append("conflicting_websites")

        # 6. Taxonomy/Category Compatibility
        cat_a = record_a.get("category_slug") or record_a.get("category")
        cat_b = record_b.get("category_slug") or record_b.get("category")
        if cat_a and cat_b:
            if cat_a == cat_b:
                score += 0.10
                signals.append("same_category")
            else:
                score -= 0.05

        final_score = min(1.0, max(0.0, score))
        is_match = final_score >= self.match_threshold
        is_ambiguous = (final_score >= self.ambiguous_threshold) and not is_match

        return MatchResult(
            score=round(final_score, 4),
            is_match=is_match,
            is_ambiguous=is_ambiguous,
            signals=signals,
            reasons=reasons or ([f"Distance {dist_m:.1f}m", f"Name sim {sim:.2f}"])
        )
