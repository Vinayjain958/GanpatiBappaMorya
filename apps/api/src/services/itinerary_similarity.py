"""ItinerarySimilarityService — deterministic similar-plan lookup (ADR-056).

Answers "how many previously generated, eligible itineraries resemble
this planning context?" and returns anonymized examples — WITHOUT
creating, saving, composing, routing, or calling Gemini. Pure database
read + arithmetic; no ML model, no embeddings, no pgvector (portable
across SQLite and PostgreSQL).

Eligibility (what counts toward similar_count):
  - an Itinerary with a persisted ItineraryPlanningProfile (i.e. produced
    by the compose pipeline after this feature shipped),
  - source == COMPOSER and status != CANCELLED,
  - owned by ANOTHER traveler (your own plans are already on /trip),
  - same destination city when the request names one (hard prefilter —
    a "similar plan" in another city is not useful),
  - weighted score >= SIMILARITY_THRESHOLD.
Examples (what is actually shown) are the subset whose owner opted in
via Itinerary.is_discoverable. Private itineraries contribute to the
count only; none of their fields, ids, or scores ever leave this module.

Scoring uses only NormalizedTripProfile, which has NO gender field — so
gender cannot become a generic preference signal, even by accident
(regression-tested in tests/test_itinerary_similarity.py).

Determinism: same normalized input + same DB snapshot => same count,
same scores (rounded to 4 dp), same order (score desc, created_at desc,
itinerary id asc).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.itinerary_planning import (
    PACE_ORDER,
    SIMILARITY_MATCHED_DIMENSION_MIN,
    SIMILARITY_MAX_SCAN,
    SIMILARITY_THRESHOLD,
    SIMILARITY_WEIGHTS,
    GroupSignals,
    group_signals_from_ages,
    interest_terms,
    normalize_destination,
    normalize_interests,
)
from src.models.category import ExperienceCategory
from src.models.experience import Experience
from src.models.itinerary import Itinerary
from src.models.itinerary_item import ItineraryItem
from src.models.itinerary_planning_profile import ItineraryPlanningProfile
from src.schemas.itinerary import (
    ItineraryPlanningContext,
    SimilarItinerariesRequest,
    SimilarItinerariesResponse,
    SimilarItinerarySummary,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NormalizedTripProfile:
    """The ONLY input the scorer sees. Intentionally no gender, no exact
    ages, no owner, no location coordinates."""

    destination_key: str | None
    group: GroupSignals
    interests: tuple[str, ...]
    budget_max: float | None
    pace: str
    accessibility: tuple[str, ...]
    trip_month: int
    duration_days: int = 1


@dataclass(frozen=True)
class SimilarityScore:
    score: float
    components: dict[str, float] = field(default_factory=dict)

    @property
    def matched_dimensions(self) -> list[str]:
        return [
            name for name in SIMILARITY_WEIGHTS
            if self.components.get(name, 0.0) >= SIMILARITY_MATCHED_DIMENSION_MIN
        ]


def build_normalized_profile(
    *,
    city: str | None,
    locality: str | None,
    itinerary_date: date,
    interests: list[str],
    category_slugs: list[str],
    max_budget: float | None,
    pace: str,
    accessibility_requirements: list[str],
    planning: ItineraryPlanningContext | None,
    party_size: int | None = None,
) -> NormalizedTripProfile:
    if planning is not None:
        group = group_signals_from_ages([p.age_years for p in planning.participants], planning.group_size)
    else:
        group = GroupSignals(group_size=party_size or 1)
    return NormalizedTripProfile(
        destination_key=normalize_destination(city, locality),
        group=group,
        interests=tuple(normalize_interests(interests, category_slugs)),
        budget_max=max_budget,
        pace=pace,
        accessibility=tuple(sorted(set(accessibility_requirements))),
        trip_month=itinerary_date.month,
    )


def profile_from_row(row: ItineraryPlanningProfile) -> NormalizedTripProfile:
    return NormalizedTripProfile(
        destination_key=row.destination_key,
        group=GroupSignals(
            group_size=row.group_size,
            children_count=row.children_count,
            teens_count=row.teens_count,
            adults_count=row.adults_count,
            seniors_count=row.seniors_count,
            age_band_distribution=dict(row.age_band_distribution or {}),
        ),
        interests=tuple(row.interests or ()),
        budget_max=row.budget_max,
        pace=row.pace,
        accessibility=tuple(row.accessibility_requirements or ()),
        trip_month=row.trip_month,
    )


# ─── Component scorers (each returns 0.0..1.0) ───────────────────────────


def _split_destination(key: str | None) -> tuple[str | None, str | None]:
    if not key:
        return None, None
    city, _, locality = key.partition("|")
    return (city or None), (locality or None)


def _destination_score(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.5  # unknown on one side — neutral, never a fabricated match
    if a == b:
        return 1.0
    a_city, a_loc = _split_destination(a)
    b_city, b_loc = _split_destination(b)
    if a_city and b_city and a_city == b_city:
        if a_loc and b_loc:
            return 0.7  # same city, different neighbourhood
        return 0.85  # same city, one side city-wide
    if a_loc and b_loc and a_loc == b_loc and not (a_city and b_city):
        return 0.85
    return 0.0


def _duration_score(a: int, b: int) -> float:
    return 1.0 - abs(a - b) / max(a, b, 1)


def _age_proportions(group: GroupSignals) -> tuple[float, float, float, float] | None:
    total = group.children_count + group.teens_count + group.adults_count + group.seniors_count
    if total == 0:
        return None
    return (
        group.children_count / total,
        group.teens_count / total,
        group.adults_count / total,
        group.seniors_count / total,
    )


def _group_score(a: GroupSignals, b: GroupSignals) -> float:
    size = 1.0 - abs(a.group_size - b.group_size) / max(a.group_size, b.group_size, 1)
    pa, pb = _age_proportions(a), _age_proportions(b)
    if pa is None or pb is None:
        distribution = 0.5  # no age profile on one side — neutral
    else:
        distribution = 1.0 - 0.5 * sum(abs(x - y) for x, y in zip(pa, pb, strict=True))
    return 0.5 * size + 0.5 * distribution


def _interest_score(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.5
    return len(sa & sb) / len(sa | sb)


def _budget_score(a: float | None, b: float | None) -> float:
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.5
    if a == b:
        return 1.0
    return max(0.0, 1.0 - abs(a - b) / max(a, b))


def _pace_score(a: str, b: str) -> float:
    ia, ib = PACE_ORDER.get(a), PACE_ORDER.get(b)
    if ia is None or ib is None:
        return 0.5
    return {0: 1.0, 1: 0.5}.get(abs(ia - ib), 0.0)


def _accessibility_score(requested: tuple[str, ...], candidate: tuple[str, ...]) -> float:
    # Strong only when the requester explicitly asked for something: a
    # historical plan built without that requirement is a poor example.
    if not requested:
        return 1.0
    return len(set(requested) & set(candidate)) / len(set(requested))


def _period_score(a: int, b: int) -> float:
    diff = abs(a - b) % 12
    diff = min(diff, 12 - diff)
    return 1.0 - diff / 6.0


def score_profiles(query: NormalizedTripProfile, candidate: NormalizedTripProfile) -> SimilarityScore:
    components = {
        "destination": _destination_score(query.destination_key, candidate.destination_key),
        "duration": _duration_score(query.duration_days, candidate.duration_days),
        "group_profile": _group_score(query.group, candidate.group),
        "interests": _interest_score(query.interests, candidate.interests),
        "budget": _budget_score(query.budget_max, candidate.budget_max),
        "pace": _pace_score(query.pace, candidate.pace),
        "accessibility": _accessibility_score(query.accessibility, candidate.accessibility),
        "trip_period": _period_score(query.trip_month, candidate.trip_month),
    }
    total = sum(SIMILARITY_WEIGHTS[name] * value for name, value in components.items())
    return SimilarityScore(
        score=round(total, 4),
        components={k: round(v, 4) for k, v in components.items()},
    )


# ─── Service ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Match:
    itinerary_id: str
    created_at_key: str
    is_discoverable: bool
    profile: ItineraryPlanningProfile
    score: SimilarityScore


class ItinerarySimilarityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _candidate_query(
        self, *, requester_traveler_id: str, destination_key: str | None
    ) -> Select[tuple[ItineraryPlanningProfile, str, datetime, bool]]:
        query = (
            select(
                ItineraryPlanningProfile,
                Itinerary.id,
                Itinerary.created_at,
                Itinerary.is_discoverable,
            )
            .join(Itinerary, Itinerary.id == ItineraryPlanningProfile.itinerary_id)
            .where(
                Itinerary.traveler_id != requester_traveler_id,
                Itinerary.source == "COMPOSER",
                Itinerary.status != "CANCELLED",
            )
        )
        city, _ = _split_destination(destination_key)
        if city:
            query = query.where(
                (ItineraryPlanningProfile.destination_key == city)
                | ItineraryPlanningProfile.destination_key.startswith(f"{city}|", autoescape=True)
            )
        return query.order_by(Itinerary.created_at.desc(), Itinerary.id.asc()).limit(SIMILARITY_MAX_SCAN)

    async def find_similar(
        self,
        *,
        requester_traveler_id: str,
        request: SimilarItinerariesRequest,
    ) -> SimilarItinerariesResponse:
        started = time.monotonic()
        logger.info(
            "event=similarity_search_started group_size=%d has_destination=%s",
            request.planning.group_size, bool(request.city or request.locality),
        )
        query_profile = build_normalized_profile(
            city=request.city,
            locality=request.locality,
            itinerary_date=request.itinerary_date,
            interests=interest_terms(request.interests, request.query),
            category_slugs=request.category_slugs,
            max_budget=request.max_budget,
            pace=request.pace,
            accessibility_requirements=list(request.accessibility_requirements),
            planning=request.planning,
        )

        rows = (
            await self._session.execute(
                self._candidate_query(
                    requester_traveler_id=requester_traveler_id,
                    destination_key=query_profile.destination_key,
                )
            )
        ).all()

        matches: list[_Match] = []
        for profile_row, itinerary_id, created_at, is_discoverable in rows:
            scored = score_profiles(query_profile, profile_from_row(profile_row))
            if scored.score >= SIMILARITY_THRESHOLD:
                matches.append(
                    _Match(
                        itinerary_id=itinerary_id,
                        created_at_key=created_at.isoformat() if created_at is not None else "",
                        is_discoverable=bool(is_discoverable),
                        profile=profile_row,
                        score=scored,
                    )
                )

        # Stable multi-key sort: score desc, then created_at desc, then id asc.
        matches.sort(key=lambda m: m.itinerary_id)
        matches.sort(key=lambda m: m.created_at_key, reverse=True)
        matches.sort(key=lambda m: m.score.score, reverse=True)

        discoverable = [m for m in matches if m.is_discoverable]
        page = discoverable[request.offset : request.offset + request.limit]
        examples = await self._build_examples(page)

        logger.info(
            "event=similarity_search_completed scanned=%d similar_count=%d examples_total=%d duration_ms=%d",
            len(rows), len(matches), len(discoverable), int((time.monotonic() - started) * 1000),
        )
        return SimilarItinerariesResponse(
            similar_count=len(matches),
            examples=examples,
            examples_total=len(discoverable),
            limit=request.limit,
            offset=request.offset,
            has_more=request.offset + len(page) < len(discoverable),
        )

    async def _build_examples(self, page: list[_Match]) -> list[SimilarItinerarySummary]:
        if not page:
            return []
        ids = [m.itinerary_id for m in page]
        usable = ItineraryItem.route_status.in_(("ROUTED", "ESTIMATED"))

        stats_rows = (
            await self._session.execute(
                select(
                    ItineraryItem.itinerary_id,
                    func.count(ItineraryItem.id),
                    func.sum(case((usable, ItineraryItem.travel_from_previous_distance_km), else_=None)),
                    func.sum(case((usable, ItineraryItem.travel_from_previous_minutes), else_=None)),
                )
                .where(ItineraryItem.itinerary_id.in_(ids))
                .group_by(ItineraryItem.itinerary_id)
            )
        ).all()
        stats = {row[0]: (int(row[1]), row[2], row[3]) for row in stats_rows}

        category_rows = (
            await self._session.execute(
                select(ItineraryItem.itinerary_id, ExperienceCategory.name)
                .join(Experience, Experience.id == ItineraryItem.experience_id)
                .join(ExperienceCategory, ExperienceCategory.id == Experience.category_id)
                .where(ItineraryItem.itinerary_id.in_(ids))
                .distinct()
            )
        ).all()
        categories: dict[str, set[str]] = {}
        for itinerary_id, name in category_rows:
            categories.setdefault(itinerary_id, set()).add(name)

        examples: list[SimilarItinerarySummary] = []
        for match in page:
            stop_count, distance_km, travel_minutes = stats.get(match.itinerary_id, (0, None, None))
            examples.append(
                SimilarItinerarySummary(
                    example_id=match.itinerary_id,
                    destination_label=match.profile.destination_label,
                    duration_days=1,
                    group_size=match.profile.group_size,
                    pace=match.profile.pace,
                    interests=list(match.profile.interests or []),
                    category_names=sorted(categories.get(match.itinerary_id, set())),
                    stop_count=stop_count,
                    total_distance_km=round(distance_km, 1) if distance_km is not None else None,
                    total_travel_minutes=round(travel_minutes) if travel_minutes is not None else None,
                    similarity_score=match.score.score,
                    matched_dimensions=match.score.matched_dimensions,
                )
            )
        return examples


__all__ = [
    "ItinerarySimilarityService",
    "NormalizedTripProfile",
    "SimilarityScore",
    "build_normalized_profile",
    "profile_from_row",
    "score_profiles",
]
