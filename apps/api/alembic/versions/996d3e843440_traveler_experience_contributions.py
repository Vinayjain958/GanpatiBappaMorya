"""traveler_experience_contributions

Adds (ADR-058):
  - traveler_experience_contributions: audit/provenance record for the
    traveler direct-publish "Add a Local Experience" flow. NOT a second
    catalog — the published Experience row remains the canonical,
    searchable entity; this table exists so a submission is traceable
    back to its contributor and its as-submitted values.
  - a singleton "LocaLens Community" Provider row (fixed id
    00000000-0000-0000-0000-000000000001) that every traveler-submitted
    Experience is attached to, since Experience.provider_id is NOT NULL
    and travelers are never auto-converted into Provider accounts
    (spec §7/§62). source_type="system" is used only for this one row.

Existing rows are untouched — this migration only adds a new table and
inserts one new provider row.

Revision ID: 996d3e843440
Revises: d7e2f4a9b301
Create Date: 2026-09-26 23:15:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '996d3e843440'
down_revision: Union[str, Sequence[str], None] = 'd7e2f4a9b301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COMMUNITY_PROVIDER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'traveler_experience_contributions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('traveler_id', sa.String(length=36), nullable=False),
        sa.Column('published_experience_id', sa.String(length=36), nullable=True),
        sa.Column('submitted_name', sa.String(length=200), nullable=False),
        sa.Column('submitted_description', sa.Text(), nullable=True),
        sa.Column('submitted_contact_phone', sa.String(length=32), nullable=False),
        sa.Column('submitted_contact_phone_raw', sa.String(length=40), nullable=False),
        sa.Column('submitted_website', sa.String(length=500), nullable=True),
        sa.Column('submitted_category_id', sa.String(length=36), nullable=False),
        sa.Column('submitted_location_id', sa.String(length=36), nullable=True),
        sa.Column('submitted_image_object_key', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='published'),
        sa.Column('validation_status', sa.String(length=20), nullable=False),
        sa.Column('duplicate_check_status', sa.String(length=20), nullable=False, server_default='none'),
        sa.Column('duplicate_of_experience_id', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=80), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['traveler_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['published_experience_id'], ['experiences.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submitted_category_id'], ['experience_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['submitted_location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['duplicate_of_experience_id'], ['experiences.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('traveler_id', 'idempotency_key', name='uq_contribution_traveler_idempotency'),
    )
    op.create_index(
        'ix_traveler_experience_contributions_traveler_id',
        'traveler_experience_contributions', ['traveler_id'], unique=False,
    )
    op.create_index(
        'ix_traveler_experience_contributions_published_experience_id',
        'traveler_experience_contributions', ['published_experience_id'], unique=False,
    )

    providers = sa.table(
        'providers',
        sa.column('id', sa.String),
        sa.column('business_name', sa.String),
        sa.column('description', sa.Text),
        sa.column('provider_type', sa.String),
        sa.column('verification_status', sa.String),
        sa.column('source_type', sa.String),
        sa.column('is_synthetic', sa.Boolean),
        sa.column('is_enriched', sa.Boolean),
        sa.column('attribution_required', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    op.execute(
        providers.insert().values(
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
            attribution_required=False,
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
    )


def downgrade() -> None:
    """Downgrade schema.

    Destructive if any real contributions exist: deletes the singleton
    community provider row unconditionally, which will fail the FK
    constraint if any Experience still references it (traveler-submitted
    experiences would need to be reassigned or removed first). This
    mirrors how other seeded-data migrations in this project treat
    downgrade as a dev-time operation, not a safe production rollback.
    """
    op.execute(
        sa.text("DELETE FROM providers WHERE id = :id").bindparams(id=COMMUNITY_PROVIDER_ID)
    )
    op.drop_index(
        'ix_traveler_experience_contributions_published_experience_id',
        table_name='traveler_experience_contributions',
    )
    op.drop_index(
        'ix_traveler_experience_contributions_traveler_id',
        table_name='traveler_experience_contributions',
    )
    op.drop_table('traveler_experience_contributions')
