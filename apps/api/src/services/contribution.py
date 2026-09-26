"""Traveler direct-publish contribution orchestration.

Mirrors `services/experience.py:create_experience`'s Location-then-
Experience creation pattern, extended with the steps direct-publish needs
that a provider's own self-serve creation doesn't: idempotency check,
image validation, deterministic duplicate detection, and writing an audit
row (`TravelerExperienceContribution`) alongside the Experience it
publishes (spec §5/§27/§59).

`traveler_id`/`provider_id` are never accepted from the client — the
route only ever passes in the authenticated `User` (spec §7/§46).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.media_storage import MediaStorageAdapter
from src.core.errors import ApiError
from src.models.contribution import TravelerExperienceContribution
from src.models.experience import Experience
from src.models.location import Location
from src.models.provider import Provider
from src.models.user import User
from src.repositories.category_repository import CategoryRepository
from src.repositories.experience_repository import ExperienceRepository
from src.repositories.provider_repository import ProviderRepository
from src.schemas.contribution import ContributionCreateForm
from src.services.contribution_duplicate import find_duplicate_match
from src.services.media_validation import ImageValidationError, validate_and_process_image

# Fixed id also inserted (in real deployments) by
# alembic/versions/996d3e843440_traveler_experience_contributions.py —
# every traveler-submitted Experience is attached to this single
# placeholder Provider row so it satisfies Experience.provider_id's
# NOT NULL FK without auto-converting the contributing traveler into a
# real Provider account (spec §7/§62). `_get_or_create_community_provider`
# below makes this self-healing for test databases created via
# Base.metadata.create_all (tests/conftest.py), which never run Alembic
# migrations or their data-seeding steps.
COMMUNITY_PROVIDER_ID = "00000000-0000-0000-0000-000000000001"


async def _get_or_create_community_provider(session: AsyncSession) -> Provider:
    repo = ProviderRepository(session)
    provider = await repo.get_by_id(COMMUNITY_PROVIDER_ID)
    if provider is not None:
        return provider

    provider = Provider(
        id=COMMUNITY_PROVIDER_ID,
        business_name="LocaLens Community",
        description=(
            "Placeholder catalog owner for experiences published directly "
            "by travelers via the Add a Local Experience contribution flow. "
            "Not a real business — see docs/DECISIONS.md ADR-058."
        ),
        provider_type="community",
        verification_status="unverified",
        source_type="system",
        is_synthetic=False,
        is_enriched=False,
    )
    session.add(provider)
    await session.flush()
    return provider


_DIGITS_RE = re.compile(r"\D+")


class DuplicateExperienceError(Exception):
    """Strong duplicate match — publication must not proceed."""

    def __init__(self, existing_experience_id: str, reason: str) -> None:
        self.existing_experience_id = existing_experience_id
        self.reason = reason


class PossibleDuplicateError(Exception):
    """Uncertain match — client must confirm via override_duplicate_check."""

    def __init__(self, existing_experience_id: str, reason: str) -> None:
        self.existing_experience_id = existing_experience_id
        self.reason = reason


@dataclass(frozen=True)
class ContributionResult:
    experience: Experience
    contribution: TravelerExperienceContribution


def _normalize_phone_for_storage(raw: str) -> str:
    """Digits-only normalization with a leading '+' preserved if present.
    Never assumes a country code that wasn't given (spec §19) — this is
    intentionally not full E.164 validation, just enough to compare two
    numbers for duplicate detection and store a consistent form."""
    trimmed = raw.strip()
    digits = _DIGITS_RE.sub("", trimmed)
    if not digits:
        raise ApiError("Please enter a valid contact number.", status_code=422)
    if len(digits) < 6 or len(digits) > 15:
        raise ApiError("Please enter a valid contact number.", status_code=422)
    return f"+{digits}" if trimmed.startswith("+") else digits


async def submit_experience_contribution(
    session: AsyncSession,
    user: User,
    form: ContributionCreateForm,
    image_bytes: bytes,
    *,
    media_storage: MediaStorageAdapter,
    max_upload_bytes: int,
    max_image_dimension_px: int,
    duplicate_radius_m: float,
    idempotency_key: str | None,
) -> ContributionResult:
    # ── Idempotency: a repeated request (network retry, double-click)
    # with the same key must not publish twice (spec §88).
    if idempotency_key:
        existing = (
            await session.execute(
                select(TravelerExperienceContribution).where(
                    TravelerExperienceContribution.traveler_id == user.id,
                    TravelerExperienceContribution.idempotency_key == idempotency_key,
                )
            )
        ).scalars().one_or_none()
        if existing is not None and existing.published_experience_id:
            repo = ExperienceRepository(session)
            experience = await repo.get_by_id(existing.published_experience_id)
            if experience is not None:
                return ContributionResult(experience=experience, contribution=existing)

    category = await CategoryRepository(session).get_by_id(form.category_id)
    if category is None:
        raise ApiError("Please select a valid category.", status_code=422)

    normalized_phone = _normalize_phone_for_storage(form.contact_phone)

    try:
        processed = validate_and_process_image(
            image_bytes,
            max_bytes=max_upload_bytes,
            max_dimension_px=max_image_dimension_px,
        )
    except ImageValidationError as exc:
        raise ApiError(str(exc), status_code=422) from exc

    # ── Duplicate detection (deterministic only — spec §24/§26) ─────────
    experience_repo = ExperienceRepository(session)
    candidates = await experience_repo.find_nearby_active(
        latitude=form.latitude, longitude=form.longitude, radius_km=(duplicate_radius_m * 2) / 1000.0
    )
    match = find_duplicate_match(
        candidates,
        name=form.name,
        latitude=form.latitude,
        longitude=form.longitude,
        phone=normalized_phone,
        website=form.website,
        radius_m=duplicate_radius_m,
    )
    duplicate_check_status = "none"
    duplicate_of_experience_id: str | None = None
    if match is not None:
        if match.tier == "strong":
            raise DuplicateExperienceError(match.experience.id, match.reason)
        if match.tier == "uncertain" and not form.override_duplicate_check:
            raise PossibleDuplicateError(match.experience.id, match.reason)
        # Uncertain + explicitly overridden: proceed, but record it.
        duplicate_check_status = "uncertain_overridden"
        duplicate_of_experience_id = match.experience.id

    community_provider = await _get_or_create_community_provider(session)

    # ── Media is written only after every validation has passed, right
    # before commit, so a validation failure never leaves an orphaned
    # upload on disk (spec §27).
    image_url = media_storage.save(processed.data, processed.object_key, processed.content_type)

    location = Location(
        latitude=form.latitude,
        longitude=form.longitude,
        place_name=form.place_name or form.name,
        address=form.address,
        source_type="traveler_submission",
        is_synthetic=False,
        is_enriched=False,
    )
    session.add(location)
    await session.flush()

    now = datetime.now(UTC)
    experience = Experience(
        provider_id=community_provider.id,
        category_id=category.id,
        location_id=location.id,
        title=form.name,
        short_description=(form.description or form.name)[:300],
        full_description=form.description or form.name,
        status="active",
        verification_status="unverified",
        rating=None,
        rating_source=None,
        review_count=None,
        opening_hours_status="unavailable",
        price_source="unavailable",
        image_url=image_url,
        image_source="traveler_upload",
        image_is_place_specific=True,
        image_is_synthetic=False,
        image_retrieved_at=now,
        source_type="traveler_submission",
        source_name="LocaLens community contribution",
        is_synthetic=False,
        is_enriched=False,
    )
    session.add(experience)
    await session.flush()

    experience.source_record_id = experience.id

    contribution = TravelerExperienceContribution(
        traveler_id=user.id,
        published_experience_id=experience.id,
        submitted_name=form.name,
        submitted_description=form.description,
        submitted_contact_phone=normalized_phone,
        submitted_contact_phone_raw=form.contact_phone,
        submitted_website=form.website,
        submitted_category_id=category.id,
        submitted_location_id=location.id,
        submitted_image_object_key=processed.object_key,
        status="published",
        validation_status="passed",
        duplicate_check_status=duplicate_check_status,
        duplicate_of_experience_id=duplicate_of_experience_id,
        idempotency_key=idempotency_key,
        published_at=now,
    )
    session.add(contribution)

    await session.commit()

    reloaded = await experience_repo.get_by_id(experience.id)
    assert reloaded is not None
    return ContributionResult(experience=reloaded, contribution=contribution)
