"""Personalized itinerary planning — shared domain constants and pure,
deterministic normalization helpers.

Single home for:
  - the controlled participant gender vocabulary,
  - age-band derivation (age_band is ALWAYS derived from age_years here,
    never accepted from a client, so a stored row can never hold a
    contradictory age/age_band pair),
  - normalized group signals (children/teens/adults/seniors counts +
    age-band distribution) used by the planning profile and by
    ItinerarySimilarityService,
  - destination/interest normalization,
  - the similarity scoring weights/threshold (kept here, not in any
    route/controller, so they can be tuned in one place).

Hard fairness rules (docs/DECISIONS.md ADR-056):
  - Gender is stored as self-described context only. Nothing in this
    module (or the similarity/ranking/feasibility code) reads it to
    prefer or penalize anything. `GroupSignals` deliberately has no
    gender field, so it structurally cannot feed a score.
  - Age bands are descriptive only. Nothing infers ability, health,
    fitness, or interests from age. Age never affects feasibility in
    this phase because the catalog has no authoritative age-restriction
    fields (Experience has no minimum_age/maximum_age) — see ADR-056.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal, get_args

# ─── Participants ────────────────────────────────────────────────────────

ParticipantGender = Literal["female", "male", "non_binary", "self_described", "prefer_not_to_say"]
PARTICIPANT_GENDERS: tuple[str, ...] = get_args(ParticipantGender)

MIN_PARTICIPANT_AGE = 0
MAX_PARTICIPANT_AGE = 120

AgeBand = Literal["0_5", "6_12", "13_17", "18_24", "25_34", "35_49", "50_64", "65_PLUS"]
AGE_BANDS: tuple[str, ...] = get_args(AgeBand)

# (inclusive lower bound, band) — walked from highest to lowest.
_AGE_BAND_LOWER_BOUNDS: tuple[tuple[int, str], ...] = (
    (65, "65_PLUS"),
    (50, "50_64"),
    (35, "35_49"),
    (25, "25_34"),
    (18, "18_24"),
    (13, "13_17"),
    (6, "6_12"),
    (0, "0_5"),
)

CHILD_BANDS = frozenset({"0_5", "6_12"})
TEEN_BANDS = frozenset({"13_17"})
ADULT_BANDS = frozenset({"18_24", "25_34", "35_49", "50_64"})
SENIOR_BANDS = frozenset({"65_PLUS"})


def derive_age_band(age_years: int) -> str:
    """Deterministic age -> band mapping. Raises on an out-of-range age
    rather than silently clamping (never mutate invalid user data)."""
    if not MIN_PARTICIPANT_AGE <= age_years <= MAX_PARTICIPANT_AGE:
        raise ValueError(f"age_years must be between {MIN_PARTICIPANT_AGE} and {MAX_PARTICIPANT_AGE}")
    for lower, band in _AGE_BAND_LOWER_BOUNDS:
        if age_years >= lower:
            return band
    raise ValueError("unreachable")  # pragma: no cover


@dataclass(frozen=True)
class GroupSignals:
    """Normalized, aggregate group profile. No gender field — by design."""

    group_size: int
    children_count: int = 0
    teens_count: int = 0
    adults_count: int = 0
    seniors_count: int = 0
    # band -> count, only bands that are present; keys sorted for stable JSON.
    age_band_distribution: dict[str, int] = field(default_factory=dict)

    @property
    def has_age_profile(self) -> bool:
        return sum(self.age_band_distribution.values()) > 0


def group_signals_from_ages(ages: list[int], group_size: int | None = None) -> GroupSignals:
    """Builds aggregate signals from participant ages. `group_size` defaults
    to len(ages); callers validate equality separately (schema layer)."""
    distribution: dict[str, int] = {}
    children = teens = adults = seniors = 0
    for age in ages:
        band = derive_age_band(age)
        distribution[band] = distribution.get(band, 0) + 1
        if band in CHILD_BANDS:
            children += 1
        elif band in TEEN_BANDS:
            teens += 1
        elif band in ADULT_BANDS:
            adults += 1
        else:
            seniors += 1
    return GroupSignals(
        group_size=group_size if group_size is not None else len(ages),
        children_count=children,
        teens_count=teens,
        adults_count=adults,
        seniors_count=seniors,
        age_band_distribution={k: distribution[k] for k in sorted(distribution)},
    )


# ─── Destination / interests normalization ───────────────────────────────


def normalize_token(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().lower().split())
    return cleaned or None


def normalize_destination(city: str | None, locality: str | None) -> str | None:
    """Canonical destination key: "city" or "city|locality" (lowercase,
    whitespace-collapsed). None when neither is given."""
    c = normalize_token(city)
    loc = normalize_token(locality)
    if c and loc:
        return f"{c}|{loc}"
    return c or (f"|{loc}" if loc else None)


def destination_label(city: str | None, locality: str | None) -> str | None:
    parts = [p.strip() for p in (locality, city) if p and p.strip()]
    return ", ".join(parts) if parts else None


def normalize_interests(interests: list[str], category_slugs: list[str]) -> list[str]:
    tokens = {t for t in (normalize_token(v) for v in [*interests, *category_slugs]) if t}
    return sorted(tokens)


def interest_terms(interests: list[str], query: str | None) -> list[str]:
    """Explicit interests plus the free-text query split on commas
    ("food, heritage walks" -> ["food", "heritage walks"]). Used
    identically when persisting a planning profile and when searching,
    so both sides tokenize the same way."""
    terms = list(interests)
    if query:
        terms.extend(part for part in query.split(",") if part.strip())
    return terms


# ─── Similarity scoring configuration ────────────────────────────────────
#
# Weights sum to 1.0. Gender intentionally has NO weight (and no field on
# the scoring input at all). Tune here only — never in route code.

SIMILARITY_WEIGHTS: dict[str, float] = {
    "destination": 0.25,  # strong
    "duration": 0.10,  # strong (always 1 day in the single-day phase)
    "group_profile": 0.20,  # strong
    "interests": 0.20,  # strong
    "budget": 0.08,  # medium
    "pace": 0.08,  # medium
    "accessibility": 0.06,  # strong *when explicitly requested* (see scorer)
    "trip_period": 0.03,  # weak
}
# Minimum weighted score for a historical itinerary to count as "similar".
SIMILARITY_THRESHOLD = 0.60
# A dimension whose component score reaches this is reported as "matched".
SIMILARITY_MATCHED_DIMENSION_MIN = 0.80
# Upper bound on how many historical planning profiles one similarity
# request will score (most recent first) — protects the endpoint from
# scanning an unbounded table. Portable SQLite/PostgreSQL; no pgvector.
SIMILARITY_MAX_SCAN = 2000
SIMILARITY_DEFAULT_LIMIT = 5
SIMILARITY_MAX_LIMIT = 20
SIMILARITY_MAX_OFFSET = 200

PACE_ORDER: dict[str, int] = {"relaxed": 0, "balanced": 1, "packed": 2}

# Bumped whenever the normalized-profile shape or signature inputs change.
PLANNING_PROFILE_VERSION = "planning-profile-v1"


def similarity_signature(payload: dict[str, object]) -> str:
    """Stable hash of a normalized planning profile (sorted-key JSON).
    Used only as an exact-duplicate fingerprint, never as a score."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:40]


__all__ = [
    "AGE_BANDS",
    "AgeBand",
    "GroupSignals",
    "MAX_PARTICIPANT_AGE",
    "MIN_PARTICIPANT_AGE",
    "PACE_ORDER",
    "PARTICIPANT_GENDERS",
    "PLANNING_PROFILE_VERSION",
    "ParticipantGender",
    "SIMILARITY_DEFAULT_LIMIT",
    "SIMILARITY_MATCHED_DIMENSION_MIN",
    "SIMILARITY_MAX_LIMIT",
    "SIMILARITY_MAX_OFFSET",
    "SIMILARITY_MAX_SCAN",
    "SIMILARITY_THRESHOLD",
    "SIMILARITY_WEIGHTS",
    "derive_age_band",
    "destination_label",
    "group_signals_from_ages",
    "interest_terms",
    "normalize_destination",
    "normalize_interests",
    "normalize_token",
    "similarity_signature",
]
